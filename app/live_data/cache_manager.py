"""
快取管理器

管理 NormalizedData 的雙層快取（記憶體 + 磁碟 JSON）。
寫入時同時更新記憶體與磁碟，讀取時優先記憶體。
系統重啟後自動從磁碟恢復快取。
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from app.live_data.models import CachedData, FreshnessInfo, NormalizedData

logger = logging.getLogger(__name__)


class CacheManager:
    """
    管理 NormalizedData 的記憶體與磁碟快取

    雙層快取策略：
    - 記憶體層：快速存取，程序重啟後消失
    - 磁碟層：JSON 檔案持久化，程序重啟後自動恢復
    """

    def __init__(self, cache_file_path: str = "data/live_cache.json") -> None:
        self._cache_file_path = cache_file_path
        self._memory_cache: CachedData | None = None
        # 啟動時自動從磁碟載入
        self._auto_load_from_disk()

    def _auto_load_from_disk(self) -> None:
        """啟動時自動從磁碟載入快取至記憶體"""
        if self._memory_cache is None:
            disk_data = self._load_from_disk()
            if disk_data is not None:
                self._memory_cache = disk_data
                logger.info("已從磁碟恢復快取：來源='%s'", disk_data.source_name)

    def store(self, data: NormalizedData) -> None:
        """
        儲存資料至記憶體與磁碟快取

        Args:
            data: 正規化後的詐騙統計資料
        """
        now = datetime.now(timezone.utc)
        cached = CachedData(
            data=data,
            cached_at=now,
            source_name=data.source_name,
            is_fallback=False,
        )
        self._memory_cache = cached
        self._persist_to_disk(data)
        logger.info("快取已更新：來源='%s'", data.source_name)

    def load(self) -> CachedData | None:
        """
        載入快取資料

        優先從記憶體載入，記憶體為空時從磁碟載入。

        Returns:
            快取資料，若無快取則回傳 None
        """
        if self._memory_cache is not None:
            return self._memory_cache
        disk_data = self._load_from_disk()
        if disk_data is not None:
            self._memory_cache = disk_data
        return self._memory_cache

    def get_freshness_info(self) -> FreshnessInfo:
        """
        取得資料新鮮度資訊

        Returns:
            FreshnessInfo 包含來源、時間、新鮮度狀態
        """
        cached = self.load()
        if cached is None:
            return FreshnessInfo(
                source_name="無資料",
                is_static=True,
            )

        now = datetime.now(timezone.utc)
        age_hours = (now - cached.cached_at).total_seconds() / 3600

        return FreshnessInfo(
            source_name=cached.source_name,
            fetched_at=cached.cached_at,
            is_fresh=age_hours < 1.0 and not cached.is_fallback,
            is_cached=not cached.is_fallback and age_hours >= 1.0,
            is_static=cached.is_fallback,
            cache_age_hours=age_hours,
        )

    def _persist_to_disk(self, data: NormalizedData) -> None:
        """
        將資料持久化至磁碟 JSON 檔案

        Args:
            data: 正規化後的詐騙統計資料
        """
        try:
            cache_path = Path(self._cache_file_path)
            cache_path.parent.mkdir(parents=True, exist_ok=True)

            payload = {
                "data": json.loads(data.model_dump_json()),
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "source_name": data.source_name,
                "version": 1,
            }

            # 寫入暫存檔再重命名，避免寫入中斷導致損壞
            tmp_path = cache_path.with_suffix(".tmp")
            tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp_path.replace(cache_path)

            logger.info("快取已持久化至磁碟：%s", self._cache_file_path)
        except OSError as exc:
            logger.error("磁碟快取寫入失敗：%s", exc)

    def _load_from_disk(self) -> CachedData | None:
        """
        從磁碟 JSON 檔案載入快取

        Returns:
            快取資料，若無檔案或解析失敗則回傳 None
        """
        cache_path = Path(self._cache_file_path)
        if not cache_path.exists():
            return None

        try:
            raw = cache_path.read_text(encoding="utf-8")
            payload = json.loads(raw)

            data = NormalizedData.model_validate(payload["data"])
            cached_at = datetime.fromisoformat(payload["cached_at"])
            source_name = payload.get("source_name", data.source_name)

            return CachedData(
                data=data,
                cached_at=cached_at,
                source_name=source_name,
                is_fallback=False,
            )
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.error("磁碟快取反序列化失敗，刪除損壞檔案：%s", exc)
            try:
                cache_path.unlink()
            except OSError:
                pass
            return None
        except OSError as exc:
            logger.warning("磁碟快取讀取失敗：%s", exc)
            return None
