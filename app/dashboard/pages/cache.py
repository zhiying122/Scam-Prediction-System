"""
快取讀取與降級邏輯

實作 Dashboard 的快取讀取機制，當後端服務不可用時，
顯示最後一次成功載入的快取資料並標示資料更新時間。

需求：4.4、4.5
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# 快取預設 TTL（秒）
DEFAULT_CACHE_TTL_SECONDS = 86400  # 24 小時


@dataclass
class CacheEntry:
    """
    快取條目

    儲存快取資料與相關元資料（更新時間、TTL 等）。
    """

    key: str
    """快取鍵"""

    data: Any
    """快取資料"""

    cached_at: datetime
    """快取寫入時間"""

    ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS
    """快取存活時間（秒）"""

    is_stale: bool = False
    """是否為過期降級資料"""

    @property
    def is_expired(self) -> bool:
        """判斷快取是否已過期"""
        now = datetime.now(timezone.utc)
        cached = self.cached_at
        if cached.tzinfo is None:
            cached = cached.replace(tzinfo=timezone.utc)
        elapsed = (now - cached).total_seconds()
        return elapsed > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """快取資料的年齡（秒）"""
        now = datetime.now(timezone.utc)
        cached = self.cached_at
        if cached.tzinfo is None:
            cached = cached.replace(tzinfo=timezone.utc)
        return (now - cached).total_seconds()


class DashboardCache:
    """
    Dashboard 快取管理器

    提供快取讀取與降級邏輯：
    - 正常情況：從後端服務取得最新資料並更新快取
    - 後端不可用時：回傳快取資料並標示更新時間（降級模式）

    需求：4.4、4.5
    """

    def __init__(self) -> None:
        # in-memory 快取儲存
        self._store: dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[CacheEntry]:
        """
        讀取快取條目

        Args:
            key: 快取鍵

        Returns:
            快取條目，若不存在則回傳 None
        """
        return self._store.get(key)

    def set(
        self,
        key: str,
        data: Any,
        ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
        is_stale: bool = False,
    ) -> CacheEntry:
        """
        寫入快取條目

        Args:
            key: 快取鍵
            data: 要快取的資料
            ttl_seconds: 快取存活時間（秒）
            is_stale: 是否標記為過期降級資料

        Returns:
            已寫入的快取條目
        """
        entry = CacheEntry(
            key=key,
            data=data,
            cached_at=datetime.now(timezone.utc),
            ttl_seconds=ttl_seconds,
            is_stale=is_stale,
        )
        self._store[key] = entry
        return entry

    def invalidate(self, key: str) -> None:
        """
        使快取條目失效

        Args:
            key: 要失效的快取鍵
        """
        self._store.pop(key, None)

    def clear(self) -> None:
        """清除所有快取"""
        self._store.clear()

    def fetch_with_fallback(
        self,
        key: str,
        fetch_fn: Callable[[], Any],
        ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    ) -> tuple[Any, bool, Optional[datetime]]:
        """
        帶降級邏輯的快取讀取

        嘗試呼叫 fetch_fn 取得最新資料並更新快取；
        若 fetch_fn 拋出例外（後端不可用），則回傳快取資料（降級模式）。

        Args:
            key: 快取鍵
            fetch_fn: 取得最新資料的函數（可能拋出例外）
            ttl_seconds: 快取存活時間（秒）

        Returns:
            (data, is_from_cache, cached_at) 三元組：
            - data: 回傳的資料（最新或快取）
            - is_from_cache: 是否為快取資料（True 表示降級模式）
            - cached_at: 快取寫入時間（若為最新資料則為 None）

        Raises:
            RuntimeError: 若後端不可用且無快取資料可降級
        """
        try:
            # 嘗試從後端取得最新資料
            fresh_data = fetch_fn()
            entry = self.set(key, fresh_data, ttl_seconds=ttl_seconds)
            logger.debug("快取已更新：key=%s", key)
            return fresh_data, False, None

        except Exception as exc:
            logger.warning("後端服務不可用，嘗試使用快取降級：key=%s，錯誤：%s", key, exc)

            # 嘗試從快取讀取（即使已過期也使用）
            cached_entry = self.get(key)
            if cached_entry is not None:
                logger.info(
                    "使用快取降級資料：key=%s，快取時間=%s，年齡=%.1f 秒",
                    key,
                    cached_entry.cached_at.isoformat(),
                    cached_entry.age_seconds,
                )
                return cached_entry.data, True, cached_entry.cached_at

            # 無快取可用，拋出例外
            raise RuntimeError(
                f"後端服務不可用且無快取資料：key={key}，原始錯誤：{exc}"
            ) from exc


def format_cache_status(is_from_cache: bool, cached_at: Optional[datetime]) -> str:
    """
    格式化快取狀態說明文字

    供 Dashboard 頁面顯示資料來源與更新時間。

    Args:
        is_from_cache: 是否為快取資料
        cached_at: 快取寫入時間

    Returns:
        狀態說明文字
    """
    if not is_from_cache:
        return "資料已是最新"

    if cached_at is None:
        return "顯示快取資料（更新時間未知）"

    # 格式化快取時間
    if cached_at.tzinfo is None:
        cached_at = cached_at.replace(tzinfo=timezone.utc)

    formatted_time = cached_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"⚠️ 後端服務暫時不可用，顯示快取資料（最後更新：{formatted_time}）"
