"""
AI 詐騙進化預測系統 - Streamlit 儀表板主入口
"""
import streamlit as st

st.set_page_config(
    page_title="AI 詐騙進化預測系統",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🛡️ AI 詐騙進化預測系統")
st.markdown("從被動防禦到主動預測，運用生成式 AI 構築下一代防詐護城河。")

st.divider()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("本週新增話術樣本", "112", "+17 較上週")
with col2:
    st.metric("偵測異常事件", "8", "+3 較上週")
with col3:
    st.metric("高風險預警", "3", delta="需關注", delta_color="inverse")
with col4:
    st.metric("模型準確率", "82%", "+7% 微調後")

st.divider()
st.markdown("### 請從左側選單選擇功能頁面")

pages = {
    "🔥 熱詞排行榜": "掌握最新詐騙高頻關鍵詞趨勢",
    "🔍 XAI 可解釋性分析": "高亮顯示話術中的心理操控片段",
    "🧪 沙盤推演": "模擬新興詐騙情境，預測風險等級",
    "🗺️ 受害風險地圖": "依年齡層與地區呈現風險分布",
}
for name, desc in pages.items():
    st.markdown(f"- **{name}**：{desc}")
