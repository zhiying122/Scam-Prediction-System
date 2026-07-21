"""沙盤推演頁面"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from app.dashboard.page_views.sandbox import (
    SandboxParams, run_sandbox_simulation,
    VALID_SCENARIO_TYPES, VALID_TARGET_AUDIENCES,
)
from streamlit_app.utils.mock_data import RISK_VECTORS

st.set_page_config(page_title="沙盤推演", page_icon="🧪", layout="wide")
st.title("🧪 沙盤推演")
st.caption("模擬新興詐騙情境，預測可能出現的變種手法與風險等級")

RISK_COLORS = {"高": "🔴", "中": "🟡", "低": "🟢"}

# ── 參數設定 ──────────────────────────────────────────────────────────────────
with st.form("sandbox_form"):
    st.subheader("情境參數設定")
    col1, col2, col3 = st.columns(3)

    with col1:
        scenario = st.selectbox(
            "詐騙情境類型",
            sorted(VALID_SCENARIO_TYPES),
            index=0,
        )
    with col2:
        audience = st.selectbox(
            "目標受眾",
            sorted(VALID_TARGET_AUDIENCES),
            index=0,
        )
    with col3:
        time_window = st.slider("分析時間視窗（天）", 1, 30, 7)

    risk_filter = st.radio(
        "風險等級篩選",
        ["不篩選", "高", "中", "低"],
        horizontal=True,
    )

    submitted = st.form_submit_button("🚀 開始推演", type="primary", use_container_width=True)

# ── 推演結果 ──────────────────────────────────────────────────────────────────
if submitted:
    params = SandboxParams(
        scenario_type=scenario,
        target_audience=audience,
        risk_level_filter=None if risk_filter == "不篩選" else risk_filter,
        time_window_days=time_window,
    )

    with st.spinner("推演中..."):
        result = run_sandbox_simulation(params, risk_vectors=RISK_VECTORS)

    st.divider()
    st.subheader("推演結果")

    # 摘要
    risk_icon = RISK_COLORS.get(result.predicted_risk_level, "⚪")
    st.info(result.summary)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("預測風險等級", f"{risk_icon} {result.predicted_risk_level}")
    col_b.metric("信心分數", f"{result.confidence_score:.0%}")
    col_c.metric("識別特徵數", len(result.predicted_features))

    st.divider()
    col_feat, col_cluster = st.columns(2)

    with col_feat:
        st.markdown("**預測高風險特徵**")
        for feat in result.predicted_features:
            st.markdown(f"- {feat}")

    with col_cluster:
        st.markdown("**相關詐騙類群**")
        if result.related_cluster_labels:
            for label in result.related_cluster_labels:
                st.markdown(f"- `{label}`")
        else:
            st.caption("無相關類群資料")
