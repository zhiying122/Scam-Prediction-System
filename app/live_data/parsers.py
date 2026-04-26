"""
內建資料解析器

提供政府開放資料 JSON 與 CSV 統計報表的解析器。
每個解析器接受原始資料並回傳 NormalizedData。
"""

import csv
import io
import logging
from datetime import datetime, timezone

from app.live_data.models import (
    AnnualStat,
    MonthlyTrendEntry,
    NormalizedData,
    ScamTypeStat,
)

logger = logging.getLogger(__name__)


def json_gov_parser(raw_data: dict) -> NormalizedData:
    """
    解析政府開放資料 JSON 格式

    預期格式（data.gov.tw CKAN API 回應）：
    {
        "success": true,
        "result": {
            "records": [...],
            "scam_cases_by_region": {...},
            "scam_type_stats": {...},
            "monthly_trend": [...],
            "victim_age_distribution": {...},
            "annual_stats": {...},
            "hotwords": {...},
            "real_scam_scripts": [...]
        }
    }

    也支援直接傳入 result 層級的字典。
    """
    # 支援 CKAN 包裝格式或直接資料
    if "result" in raw_data:
        data = raw_data["result"]
    else:
        data = raw_data

    scam_cases_by_region = data.get("scam_cases_by_region", {})

    # 解析詐騙類型統計
    raw_type_stats = data.get("scam_type_stats", {})
    scam_type_stats = {}
    for name, stats in raw_type_stats.items():
        if isinstance(stats, dict):
            scam_type_stats[name] = ScamTypeStat(**stats)
        elif isinstance(stats, ScamTypeStat):
            scam_type_stats[name] = stats

    # 解析月度趨勢
    raw_trend = data.get("monthly_trend", [])
    monthly_trend = []
    for entry in raw_trend:
        if isinstance(entry, dict):
            monthly_trend.append(MonthlyTrendEntry(**entry))
        elif isinstance(entry, MonthlyTrendEntry):
            monthly_trend.append(entry)

    victim_age_distribution = data.get("victim_age_distribution", {})

    # 解析年度統計
    raw_annual = data.get("annual_stats", {})
    annual_stats = {}
    for year_key, stats in raw_annual.items():
        if isinstance(stats, dict):
            annual_stats[str(year_key)] = AnnualStat(**stats)
        elif isinstance(stats, AnnualStat):
            annual_stats[str(year_key)] = stats

    hotwords = data.get("hotwords", {})
    real_scam_scripts = data.get("real_scam_scripts", [])

    return NormalizedData(
        scam_cases_by_region=scam_cases_by_region,
        scam_type_stats=scam_type_stats,
        monthly_trend=monthly_trend,
        victim_age_distribution=victim_age_distribution,
        annual_stats=annual_stats,
        source_name="json_gov",
        fetched_at=datetime.now(timezone.utc),
        hotwords=hotwords,
        real_scam_scripts=real_scam_scripts,
    )


def csv_stats_parser(raw_data: str) -> NormalizedData:
    """
    解析 CSV 統計報表格式

    預期 CSV 格式（每行一筆縣市統計）：
    region,cases,investment_fraud,phone_fraud,online_fraud
    台北市,8432,2100,3200,3132
    新北市,11205,2800,4100,4305
    ...

    此解析器從 CSV 提取各縣市案件數，其他欄位留空
    由 normalizer 的 _fill_missing_from_cache 填補。
    """
    reader = csv.DictReader(io.StringIO(raw_data))

    scam_cases_by_region: dict[str, int] = {}
    for row in reader:
        region = row.get("region", "").strip()
        cases_str = row.get("cases", "0").strip()
        if region:
            try:
                scam_cases_by_region[region] = int(cases_str)
            except ValueError:
                logger.warning("CSV 案件數解析失敗：region='%s', cases='%s'", region, cases_str)

    return NormalizedData(
        scam_cases_by_region=scam_cases_by_region,
        scam_type_stats={},
        monthly_trend=[],
        victim_age_distribution={},
        annual_stats={},
        source_name="csv_stats",
        fetched_at=datetime.now(timezone.utc),
        hotwords={},
        real_scam_scripts=[],
    )


def scraper_result_parser(raw_data: NormalizedData) -> NormalizedData:
    """
    爬蟲結果解析器（pass-through）

    爬蟲模組（scraper.py）已直接回傳 NormalizedData，
    此解析器僅做 pass-through 並更新 fetched_at 時間戳。
    """
    return raw_data.model_copy(
        update={
            "fetched_at": datetime.now(timezone.utc),
        }
    )
