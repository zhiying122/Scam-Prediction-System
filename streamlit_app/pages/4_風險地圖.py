"""受害風險地圖頁面"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import streamlit as st

from app.dashboard.pages.risk_map import build_risk_map, get_risk_map_summary
from streamlit_app.utils.mock_data import RISK_VECTORS

st.set_page_config(page_title="風險地圖", page_icon="🗺️", layout="wide")
st.title("🗺️ 受害風險地圖")
st.caption("依年齡層與地區維度呈現詐騙受害風險分布")

RISK_COLORS = {"高": "#FF6B6B", "中": "#FFE66D", "低": "#A8E6CF"}

# ── 篩選器 ────────────────────────────────────────────────────────────────────
with st.expander("篩選設定", expanded=False):
    from app.dashboard.pages.risk_map import VALID_AGE_GROUPS, VALID_REGIONS
    selected_ages = st.multiselect(
        "年齡層",
        sorted(VALID_AGE_GROUPS),
        default=sorted(VALID_AGE_GROUPS),
    )
    selected_regions = st.multiselect(
        "地區",
        sorted(VALID_REGIONS),
        default=["台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市"],
    )

if not selected_ages or not selected_regions:
    st.warning("請至少選擇一個年齡層與一個地區")
    st.stop()

# ── 建立風險地圖 ──────────────────────────────────────────────────────────────
risk_map = build_risk_map(RISK_VECTORS, age_groups=selected_ages, regions=selected_regions)
summary = get_risk_map_summary(risk_map)

# ── 摘要指標 ──────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("整體風險等級", summary["overall_risk_level"])
col2.metric("🔴 高風險區域", summary["high_risk_count"])
col3.metric("🟡 中風險區域", summary["medium_risk_count"])
col4.metric("🟢 低風險區域", summary["low_risk_count"])

if summary.get("highest_risk"):
    hr = summary["highest_risk"]
    st.warning(
        f"⚠️ 最高風險：**{hr['age_group']}** × **{hr['region']}**"
        f"（風險指數 {hr['risk_index']:.2f}，主要類型：{hr['dominant_scam_type']}）"
    )

st.divider()

# ── 熱力矩陣 ──────────────────────────────────────────────────────────────────
st.subheader("風險熱力矩陣")

# 建立 pivot table
rows = [
    {"年齡層": e.age_group, "地區": e.region, "風險指數": e.risk_index}
    for e in risk_map.entries
]
df = pd.DataFrame(rows)
pivot = df.pivot(index="年齡層", columns="地區", values="風險指數").fillna(0)

# 用 dataframe 搭配 background_gradient 顯示
st.dataframe(
    pivot.style.background_gradient(cmap="RdYlGn_r", vmin=0, vmax=1).format("{:.2f}"),
    use_container_width=True,
)

st.divider()

# ── 明細表格 ──────────────────────────────────────────────────────────────────
st.subheader("風險明細")
df_detail = pd.DataFrame([
    {
        "年齡層": e.age_group,
        "地區": e.region,
        "風險指數": f"{e.risk_index:.2f}",
        "風險等級": e.risk_level,
        "主要詐騙類型": e.dominant_scam_type,
        "相關案件數": e.case_count,
    }
    for e in sorted(risk_map.entries, key=lambda x: -x.risk_index)
])

# 風險等級顏色標記
def highlight_risk(val):
    color = RISK_COLORS.get(val, "")
    return f"background-color: {color}; color: #333" if color else ""

st.dataframe(
    df_detail.style.applymap(highlight_risk, subset=["風險等級"]),
    use_container_width=True,
    hide_index=True,
    height=350,
)
