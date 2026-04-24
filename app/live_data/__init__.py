"""
即時資料自動更新模組

提供全域單例工廠函數，串接所有元件：
Registry → Normalizer → CacheManager → FallbackProvider → Fetcher → Scheduler
"""

import logging

from app.live_data.models import (  # noqa: F401
    AnnualStat,
    CachedData,
    DataSourceConfig,
    FetchResult,
    FreshnessInfo,
    MonthlyTrendEntry,
    NormalizedData,
    ScamTypeStat,
)

logger = logging.getLogger(__name__)

__all__ = [
    # Data models
    "ScamTypeStat",
    "MonthlyTrendEntry",
    "AnnualStat",
    "NormalizedData",
    "FetchResult",
    "DataSourceConfig",
    "CachedData",
    "FreshnessInfo",
    # Factory functions
    "get_cache_manager",
    "get_fallback_provider",
    "get_fetch_scheduler",
]

_cache_manager = None
_fallback_provider = None
_fetch_scheduler = None


def get_cache_manager():
    """取得 CacheManager 單例"""
    global _cache_manager
    if _cache_manager is None:
        from app.live_data.cache_manager import CacheManager
        _cache_manager = CacheManager()
    return _cache_manager


def get_fallback_provider():
    """取得 FallbackProvider 單例"""
    global _fallback_provider
    if _fallback_provider is None:
        from app.live_data.fallback import FallbackProvider
        _fallback_provider = FallbackProvider(get_cache_manager())
    return _fallback_provider


def get_fetch_scheduler():
    """取得 FetchScheduler 單例（串接所有元件）"""
    global _fetch_scheduler
    if _fetch_scheduler is None:
        from app.live_data.registry import DataSourceRegistry
        from app.live_data.normalizer import DataNormalizer
        from app.live_data.fetcher import DataFetcher
        from app.live_data.scheduler import FetchScheduler

        registry = DataSourceRegistry()
        normalizer = DataNormalizer()
        cache_mgr = get_cache_manager()
        fallback = get_fallback_provider()
        fetcher = DataFetcher(
            registry=registry,
            normalizer=normalizer,
            cache_manager=cache_mgr,
            fallback_provider=fallback,
        )
        _fetch_scheduler = FetchScheduler(fetcher=fetcher)
    return _fetch_scheduler
