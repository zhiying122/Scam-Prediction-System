"""
熱詞排行榜頁面邏輯 — page_views 層

Re-export 自 page_modules.hotwords，統一 import 路徑。
streamlit_app/pages/1_熱詞排行榜.py 從 app.dashboard.page_views.hotwords 引入。

需求：4.1
"""

from app.dashboard.page_modules.hotwords import (  # noqa: F401
    compute_hotword_ranking,
    get_hotword_page_data,
)

__all__ = ["compute_hotword_ranking", "get_hotword_page_data"]
