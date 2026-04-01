"""熱詞排行榜頁面"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import streamlit as st

from app.dashboard.pages.hotwords import get_hotword_page_data
from streamlit_app.utils.mock_data import HOTWORD_FREQ, TREND_DATA

st.set_page_config(page_title="熱詞排行榜", page_icon="🔥", layout="wide")
st.title("🔥 詐騙熱詞排行榜")
st.caption("資料來源：Pattern Analyzer TF-IDF 關鍵詞提取，每 24 小時更新")

# ── 計算排行 ──────────────────────────────────────────────────────────────────
data = get_hotword_page_data(HOTWORD_FREQ)
ranking = data["ranking"]
freq_values = [HOTWORD_FREQ[w] for w in ranking]

col_chart, col_table = st.columns([3, 2])

with col_chart:
    st.subheader("頻率長條圖")
    df_bar = pd.DataFrame({"關鍵詞": ranking, "出現次數": freq_values})
    st.bar_chart(df_bar.set_index("關鍵詞"), height=420)

with col_table:
    st.subheader("排行榜 Top 20")
    df_table = pd.DataFrame({
        "排名": [f"#{i+1}" for i in range(len(ranking))],
        "關鍵詞": ranking,
        "出現次數": freq_values,
    })
    st.dataframe(df_table, use_container_width=True, hide_index=True, height=420)

st.divider()

# ── 趨勢折線圖 ────────────────────────────────────────────────────────────────
st.subheader("📈 近期詐騙話術數量趨勢")
df_trend = pd.DataFrame(TREND_DATA)
df_trend["date"] = pd.to_datetime(df_trend["date"])
df_trend = df_trend.set_index("date")
st.line_chart(df_trend["count"], height=250)

st.info(f"共追蹤 {data['total_keywords']} 個關鍵詞，顯示前 {data['displayed_count']} 名")
