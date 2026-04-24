"""
資料正規化器

將不同來源的原始資料轉換為統一的 NormalizedData 格式。
支援解析器註冊機制，允許新增來源格式而不修改核心邏輯。
"""

import logging
from datetime import datetime, timezone
from typing import Any, Callable

from app.live_data.models import NormalizedData

logger = logging.getLogger(__name__)

# 解析器型別
ParserFunc = Callable[[Any], NormalizedData]


class DataNormalizer:
    """
    將不同來源的原始資料轉換為統一格式

    支援：
    - 解析器註冊機制（register_parser）
    - 缺失欄位以快取值填補
    - 資料驗證
    """

    def __init__(self) -> None:
        self._parsers: dict[str, ParserFunc] = {}
        self._register_builtin_parsers()

    def _register_builtin_parsers(self) -> None:
        """註冊內建解析器"""
        from app.live_data.parsers import csv_stats_parser, json_gov_parser

        self._parsers["json"] = json_gov_parser
        self._parsers["csv"] = csv_stats_parser

    def register_parser(self, source_format: str, parser: ParserFunc) -> None:
        """
        註冊自訂解析器

        Args:
            source_format: 資料格式識別字串（如 "json", "csv", "xml"）
            parser: 接受原始資料並回傳 NormalizedData 的函數
        """
        self._parsers[source_format] = parser
        logger.info("已註冊解析器：格式='%s'", source_format)

    def normalize(
        self,
        raw_data: Any,
        source_format: str,
        source_name: str,
        cache: NormalizedData | None = None,
    ) -> NormalizedData:
        """
        將原始資料正規化為 NormalizedData

        Args:
            raw_data: 原始資料
            source_format: 資料格式（對應已註冊的解析器）
            source_name: 資料來源名稱
            cache: 最近一次成功快取（用於填補缺失欄位）

        Returns:
            正規化後的 NormalizedData

        Raises:
            ValueError: 無對應解析器或解析失敗
        """
        parser = self._parsers.get(source_format)
        if parser is None:
            raise ValueError(f"無對應解析器：格式='{source_format}'")

        try:
            data = parser(raw_data)
        except Exception as exc:
            logger.error(
                "解析失敗：來源='%s'，格式='%s'，錯誤：%s",
                source_name,
                source_format,
                exc,
            )
            raise

        # 覆寫來源名稱與擷取時間
        data = data.model_copy(
            update={
                "source_name": source_name,
                "fetched_at": datetime.now(timezone.utc),
            }
        )

        # 填補缺失欄位
        if cache is not None:
            data = self._fill_missing_from_cache(data, cache)

        return data

    def validate(self, data: NormalizedData) -> list[str]:
        """
        驗證 NormalizedData 的資料品質

        Returns:
            驗證錯誤訊息列表（空列表表示通過）
        """
        errors: list[str] = []

        # 檢查各縣市案件數非負
        for region, count in data.scam_cases_by_region.items():
            if count < 0:
                errors.append(f"縣市 '{region}' 案件數為負數: {count}")

        # 檢查年齡層比例總和
        if data.victim_age_distribution:
            total = sum(data.victim_age_distribution.values())
            if not (0.99 <= total <= 1.01):
                errors.append(
                    f"年齡層比例總和 {total:.4f} 不在 0.99~1.01 範圍內"
                )

        # 檢查月度趨勢月份格式
        for entry in data.monthly_trend:
            if len(entry.month) != 7 or entry.month[4] != "-":
                errors.append(f"月度趨勢月份格式錯誤: '{entry.month}'")

        return errors

    def _fill_missing_from_cache(
        self, partial_data: NormalizedData, cache: NormalizedData
    ) -> NormalizedData:
        """以快取資料填補缺失欄位"""
        updates: dict[str, Any] = {}

        if not partial_data.scam_cases_by_region:
            updates["scam_cases_by_region"] = cache.scam_cases_by_region
            logger.info("以快取填補欄位：scam_cases_by_region")

        if not partial_data.scam_type_stats:
            updates["scam_type_stats"] = cache.scam_type_stats
            logger.info("以快取填補欄位：scam_type_stats")

        if not partial_data.monthly_trend:
            updates["monthly_trend"] = cache.monthly_trend
            logger.info("以快取填補欄位：monthly_trend")

        if not partial_data.victim_age_distribution:
            updates["victim_age_distribution"] = cache.victim_age_distribution
            logger.info("以快取填補欄位：victim_age_distribution")

        if not partial_data.annual_stats:
            updates["annual_stats"] = cache.annual_stats
            logger.info("以快取填補欄位：annual_stats")

        if not partial_data.hotwords:
            updates["hotwords"] = cache.hotwords
            logger.info("以快取填補欄位：hotwords")

        if not partial_data.real_scam_scripts:
            updates["real_scam_scripts"] = cache.real_scam_scripts
            logger.info("以快取填補欄位：real_scam_scripts")

        if updates:
            return partial_data.model_copy(update=updates)
        return partial_data
