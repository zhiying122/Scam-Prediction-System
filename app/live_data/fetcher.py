"""
資料擷取器

從外部來源擷取詐騙統計資料，支援 HTTP API 與爬蟲型來源。
依優先順序逐一嘗試來源，第一個成功即停止。
所有來源失敗時觸發 FallbackProvider。
"""

import logging
from collections import deque
from datetime import datetime, timezone

import httpx

from app.live_data.cache_manager import CacheManager
from app.live_data.fallback import FallbackProvider
from app.live_data.models import FetchResult
from app.live_data.normalizer import DataNormalizer, is_data_complete
from app.live_data.registry import DataSourceRegistry

logger = logging.getLogger(__name__)

_CONSECUTIVE_FAILURE_LOG_THRESHOLD = 3


class DataFetcher:
    """
    從外部來源擷取詐騙統計資料

    功能：
    - 使用 httpx.AsyncClient 進行非同步 HTTP 請求
    - 依優先順序逐一嘗試來源，第一個成功即停止
    - 保留最近 100 筆 FetchResult 紀錄（環形緩衝區）
    - 所有來源失敗時觸發 FallbackProvider
    - 連續 3 次排程擷取失敗時記錄 ERROR 日誌
    """

    def __init__(
        self,
        registry: DataSourceRegistry,
        normalizer: DataNormalizer,
        cache_manager: CacheManager,
        fallback_provider: FallbackProvider,
        timeout_seconds: int = 30,
    ) -> None:
        self._registry = registry
        self._normalizer = normalizer
        self._cache_manager = cache_manager
        self._fallback_provider = fallback_provider
        self._timeout_seconds = timeout_seconds
        self._results: deque[FetchResult] = deque(maxlen=100)
        self._consecutive_failures = 0

    async def fetch(self) -> FetchResult:
        """
        嘗試從外部來源擷取資料

        依優先順序逐一嘗試來源，第一個成功即停止。
        支援 scraper 型來源（data_format="scraper"）與傳統 HTTP API 來源。
        所有來源失敗時觸發 FallbackProvider。

        Returns:
            FetchResult 包含擷取結果
        """
        sources = self._registry.get_active_sources()

        if not sources:
            logger.warning("無可用資料來源，啟動降級機制")
            return self._handle_all_failed("無可用資料來源")

        # 取得快取資料用於缺失欄位填補；不完整快取改以靜態基準資料合併
        cached = self._cache_manager.load()
        cache_data = cached.data if cached else None
        if cache_data is not None and not is_data_complete(cache_data):
            logger.warning("現有快取不完整，合併時改用靜態基準資料")
            cache_data = None
        merge_base = (
            cache_data
            if cache_data is not None
            else FallbackProvider._load_static_defaults()
        )

        for source in sources:
            # 爬蟲型來源：使用 scraper 模組
            if source.data_format == "scraper":
                try:
                    from app.live_data.scraper import (
                        scrape_all_sources,
                        _VALID_SCAM_TYPES,
                        _VALID_REGIONS,
                    )

                    scraped = scrape_all_sources()

                    if scraped is None:
                        # 爬蟲回傳 None
                        self._registry.record_failure(source.name)
                        result = FetchResult(
                            source_name=source.name,
                            fetched_at=datetime.now(timezone.utc),
                            success=False,
                            error_message="爬蟲未取得有效資料",
                        )
                        self._results.append(result)
                        logger.warning("爬蟲來源 '%s' 未取得有效資料", source.name)
                        continue

                    # 以完整基準資料填補缺失欄位（快取或靜態預設）
                    scraped = self._normalizer._fill_missing_from_cache(
                        scraped, merge_base
                    )

                    # 驗證：scam_type_stats 只保留白名單內的類型
                    if scraped.scam_type_stats:
                        valid_types = {
                            k: v for k, v in scraped.scam_type_stats.items()
                            if k in _VALID_SCAM_TYPES
                        }
                        if not valid_types and len(scraped.scam_type_stats) > 0:
                            logger.warning(
                                "爬蟲結果 scam_type_stats 全部不在白名單內，清除"
                            )
                            scraped = scraped.model_copy(update={"scam_type_stats": {}})
                        elif valid_types:
                            scraped = scraped.model_copy(update={"scam_type_stats": valid_types})

                    # 驗證：scam_cases_by_region 只保留白名單內的縣市
                    if scraped.scam_cases_by_region:
                        valid_regions = {
                            k: v for k, v in scraped.scam_cases_by_region.items()
                            if k in _VALID_REGIONS
                        }
                        scraped = scraped.model_copy(update={"scam_cases_by_region": valid_regions})

                    # 合併後須具備核心欄位才寫入快取
                    has_data = is_data_complete(scraped)

                    if has_data:
                        self._cache_manager.store(scraped)
                        self._registry.record_success(source.name)
                        self._consecutive_failures = 0

                        result = FetchResult(
                            source_name=scraped.source_name,
                            fetched_at=datetime.now(timezone.utc),
                            success=True,
                            record_count=len(scraped.scam_cases_by_region),
                        )
                        self._results.append(result)
                        logger.info(
                            "爬蟲資料擷取成功：來源='%s'，annual_stats=%s",
                            scraped.source_name,
                            list(scraped.annual_stats.keys()),
                        )
                        return result

                    # 爬蟲回傳但無實質資料
                    self._registry.record_failure(source.name)
                    result = FetchResult(
                        source_name=source.name,
                        fetched_at=datetime.now(timezone.utc),
                        success=False,
                        error_message="爬蟲結果無實質資料",
                    )
                    self._results.append(result)
                    logger.warning("爬蟲來源 '%s' 結果無實質資料", source.name)
                    continue

                except Exception as exc:
                    error_msg = f"{type(exc).__name__}: {exc}"
                    self._registry.record_failure(source.name)
                    result = FetchResult(
                        source_name=source.name,
                        fetched_at=datetime.now(timezone.utc),
                        success=False,
                        error_message=error_msg,
                    )
                    self._results.append(result)
                    logger.warning(
                        "爬蟲來源 '%s' 擷取失敗：%s", source.name, error_msg
                    )
                    continue

            # 傳統 HTTP API 來源
            try:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.get(source.url)

                    if response.status_code == 200:
                        # 根據格式解析原始資料
                        if source.data_format == "json":
                            raw_data = response.json()
                        else:
                            raw_data = response.text

                        # 正規化
                        normalized = self._normalizer.normalize(
                            raw_data=raw_data,
                            source_format=source.data_format,
                            source_name=source.name,
                            cache=merge_base,
                        )

                        # 驗證正規化後的資料是否有實質內容
                        if not normalized.scam_cases_by_region and not normalized.scam_type_stats:
                            error_msg = "解析後資料為空"
                            self._registry.record_failure(source.name)
                            result = FetchResult(
                                source_name=source.name,
                                fetched_at=datetime.now(timezone.utc),
                                success=False,
                                http_status=response.status_code,
                                error_message=error_msg,
                            )
                            self._results.append(result)
                            logger.warning(
                                "來源 '%s' 回傳 200 但解析後資料為空，跳過",
                                source.name,
                            )
                            continue

                        # 儲存快取
                        self._cache_manager.store(normalized)
                        self._registry.record_success(source.name)

                        # 重置連續失敗計數
                        self._consecutive_failures = 0

                        result = FetchResult(
                            source_name=source.name,
                            fetched_at=datetime.now(timezone.utc),
                            success=True,
                            http_status=response.status_code,
                            record_count=len(normalized.scam_cases_by_region),
                        )
                        self._results.append(result)
                        logger.info(
                            "資料擷取成功：來源='%s'，筆數=%d",
                            source.name,
                            result.record_count,
                        )
                        return result
                    else:
                        # 非 200 狀態碼
                        error_msg = f"HTTP {response.status_code}"
                        self._registry.record_failure(source.name)
                        result = FetchResult(
                            source_name=source.name,
                            fetched_at=datetime.now(timezone.utc),
                            success=False,
                            http_status=response.status_code,
                            error_message=error_msg,
                        )
                        self._results.append(result)
                        logger.warning(
                            "來源 '%s' 回傳非 200 狀態碼：%d",
                            source.name,
                            response.status_code,
                        )

            except (httpx.TimeoutException, httpx.RequestError, Exception) as exc:
                error_msg = f"{type(exc).__name__}: {exc}"
                self._registry.record_failure(source.name)
                result = FetchResult(
                    source_name=source.name,
                    fetched_at=datetime.now(timezone.utc),
                    success=False,
                    error_message=error_msg,
                )
                self._results.append(result)
                logger.warning(
                    "來源 '%s' 擷取失敗：%s", source.name, error_msg
                )

        # 所有來源失敗
        return self._handle_all_failed("所有來源擷取失敗")

    def _handle_all_failed(self, reason: str) -> FetchResult:
        """處理所有來源失敗的情況"""
        self._consecutive_failures += 1

        if self._consecutive_failures >= _CONSECUTIVE_FAILURE_LOG_THRESHOLD:
            logger.error(
                "連續擷取失敗 %d 次：%s",
                self._consecutive_failures,
                reason,
            )

        # 觸發降級
        logger.warning("所有來源失敗，觸發降級機制")
        fallback_data = self._fallback_provider.get_data()

        # 將降級資料存入記憶體快取（不覆蓋磁碟快取）
        self._cache_manager._memory_cache = fallback_data

        result = FetchResult(
            source_name=fallback_data.source_name,
            fetched_at=datetime.now(timezone.utc),
            success=False,
            error_message=reason,
        )
        self._results.append(result)
        return result

    def get_recent_results(self, limit: int = 100) -> list[FetchResult]:
        """
        取得最近的擷取結果

        Args:
            limit: 最大回傳筆數，預設 100

        Returns:
            最近的 FetchResult 列表
        """
        results = list(self._results)
        return results[-limit:] if len(results) > limit else results

    @property
    def consecutive_failure_count(self) -> int:
        """回傳連續失敗次數"""
        return self._consecutive_failures
