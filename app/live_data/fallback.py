"""
降級提供者

當所有外部來源不可用時提供降級資料。
降級順序：磁碟快取 → 靜態預設資料（data/taiwan_scam_data.py）。
永遠不會回傳 None。
"""

import logging
from datetime import datetime, timezone

from app.live_data.cache_manager import CacheManager
from app.live_data.models import (
    AnnualStat,
    CachedData,
    MonthlyTrendEntry,
    NormalizedData,
    ScamTypeStat,
)

logger = logging.getLogger(__name__)


class FallbackProvider:
    """
    當所有外部來源不可用時提供降級資料

    降級順序：
    1. 磁碟快取（透過 CacheManager）
    2. 靜態預設資料（data/taiwan_scam_data.py）

    永遠不會回傳 None，確保 Dashboard 始終有資料可顯示。
    """

    def __init__(self, cache_manager: CacheManager) -> None:
        self._cache_manager = cache_manager

    def get_data(self) -> CachedData:
        """
        取得降級資料

        Returns:
            CachedData，來自磁碟快取或靜態預設資料
        """
        # 嘗試磁碟快取
        cached = self._cache_manager._load_from_disk()
        if cached is not None:
            logger.info("降級使用磁碟快取：來源='%s'", cached.source_name)
            cached.is_fallback = True
            return cached

        # 最終降級：靜態預設資料
        logger.info("降級使用靜態預設資料")
        static_data = self._load_static_defaults()
        now = datetime.now(timezone.utc)
        return CachedData(
            data=static_data,
            cached_at=now,
            source_name="靜態預設資料",
            is_fallback=True,
        )

    @staticmethod
    def _load_static_defaults() -> NormalizedData:
        """
        將 data/taiwan_scam_data.py 的靜態資料轉換為 NormalizedData 格式

        映射所有欄位：
        - TAIWAN_SCAM_CASES_BY_REGION → scam_cases_by_region
        - SCAM_TYPE_STATS → scam_type_stats
        - MONTHLY_TREND → monthly_trend
        - VICTIM_AGE_DISTRIBUTION → victim_age_distribution
        - ANNUAL_STATS → annual_stats
        - REAL_HOTWORDS → hotwords
        - REAL_SCAM_SCRIPTS → real_scam_scripts
        - MODEL_PERFORMANCE → (stored in real_scam_scripts metadata)
        """
        from data.taiwan_scam_data import (
            ANNUAL_STATS,
            MONTHLY_TREND,
            MODEL_PERFORMANCE,
            REAL_HOTWORDS,
            REAL_SCAM_SCRIPTS,
            SCAM_TYPE_STATS,
            TAIWAN_SCAM_CASES_BY_REGION,
            VICTIM_AGE_DISTRIBUTION,
        )

        # 轉換詐騙類型統計
        scam_type_stats: dict[str, ScamTypeStat] = {}
        for name, stats in SCAM_TYPE_STATS.items():
            scam_type_stats[name] = ScamTypeStat(
                cases=stats["cases"],
                avg_loss_ntd=stats["avg_loss_ntd"],
                trend=stats["trend"],
            )

        # 轉換月度趨勢
        monthly_trend: list[MonthlyTrendEntry] = []
        for entry in MONTHLY_TREND:
            monthly_trend.append(
                MonthlyTrendEntry(
                    month=entry["month"],
                    cases=entry["cases"],
                    amount_billion=entry["amount_billion"],
                )
            )

        # 轉換年度統計
        annual_stats: dict[str, AnnualStat] = {}
        for year_key, stats in ANNUAL_STATS.items():
            annual_stats[str(year_key)] = AnnualStat(
                total_cases=stats["total_cases"],
                total_loss_billion=stats["total_loss_billion"],
            )

        # 將 MODEL_PERFORMANCE 附加到 real_scam_scripts 的 metadata
        scam_scripts = list(REAL_SCAM_SCRIPTS)
        scam_scripts.append({"_model_performance": MODEL_PERFORMANCE})

        return NormalizedData(
            scam_cases_by_region=dict(TAIWAN_SCAM_CASES_BY_REGION),
            scam_type_stats=scam_type_stats,
            monthly_trend=monthly_trend,
            victim_age_distribution=dict(VICTIM_AGE_DISTRIBUTION),
            annual_stats=annual_stats,
            source_name="靜態預設資料",
            fetched_at=datetime.now(timezone.utc),
            hotwords=dict(REAL_HOTWORDS),
            real_scam_scripts=scam_scripts,
        )
