"""
受害風險地圖頁面邏輯 — page_views 層

Re-export 自 page_modules.risk_map，統一 import 路徑。
streamlit_app/pages/4_風險地圖.py 從 app.dashboard.page_views.risk_map 引入。

需求：4.3
"""

from app.dashboard.page_modules.risk_map import (  # noqa: F401
    AGE_GROUP_MAPPING,
    VALID_AGE_GROUPS,
    VALID_REGIONS,
    RiskMapData,
    RiskMapEntry,
    build_risk_map,
    compute_risk_index,
    get_risk_map_summary,
)

__all__ = [
    "AGE_GROUP_MAPPING",
    "VALID_AGE_GROUPS",
    "VALID_REGIONS",
    "RiskMapData",
    "RiskMapEntry",
    "build_risk_map",
    "compute_risk_index",
    "get_risk_map_summary",
]
