"""
ScamOracle 全域 CSS — 專業商務風
參考：ceogo.com.tw 風格
- 深綠頂部導覽列（logo 左、選單中、狀態右）
- 米白/白色主體，無多餘空白
- 卡片白底、細邊框、輕陰影
- 所有文字清晰可讀
"""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── 基礎重置 ─────────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Microsoft JhengHei', 'Noto Sans TC', sans-serif !important;
}

/* ── 主背景 ──────────────────────────────────────────────────────────────── */
.stApp {
    background-color: #F5F4F0 !important;
    color: #1a2332 !important;
}

/* ── 隱藏 Streamlit 預設元素 ─────────────────────────────────────────────── */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
header { visibility: hidden !important; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* ── 壓縮所有多餘空白 ────────────────────────────────────────────────────── */
.main .block-container {
    padding-top: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-bottom: 2rem !important;
    max-width: 100% !important;
}
section[data-testid="stMain"] > div:first-child {
    padding-top: 0 !important;
}
.stMarkdown { margin-bottom: 0 !important; }
div[data-testid="stVerticalBlock"] > div { gap: 0 !important; }

/* ── 頁面內容區域 ────────────────────────────────────────────────────────── */
.page-body {
    padding: 24px 32px;
    max-width: 1400px;
    margin: 0 auto;
}

/* ── Metric 卡片 ─────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    padding: 16px 20px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    transition: box-shadow 0.2s !important;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}
[data-testid="stMetricLabel"] {
    color: #6B7280 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    color: #14532d !important;
    font-weight: 700 !important;
    font-size: 1.7rem !important;
}
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

/* ── 按鈕 ────────────────────────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: #166534 !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    box-shadow: 0 1px 4px rgba(22,101,52,0.2) !important;
    transition: background 0.15s !important;
}
.stButton > button[kind="primary"]:hover {
    background: #14532d !important;
}
.stButton > button:not([kind="primary"]) {
    background: white !important;
    color: #374151 !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 6px !important;
    font-size: 0.875rem !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: #166534 !important;
    color: #166534 !important;
}

/* ── 輸入框 ──────────────────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: white !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 6px !important;
    color: #1a2332 !important;
    font-size: 0.875rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #166534 !important;
    box-shadow: 0 0 0 2px rgba(22,101,52,0.12) !important;
}

/* ── 進度條 ──────────────────────────────────────────────────────────────── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #166534, #22c55e) !important;
}
.stProgress > div > div > div { background: #E5E7EB !important; }

/* ── Alert ───────────────────────────────────────────────────────────────── */
div[data-testid="stNotification"][kind="success"] {
    background: #F0FDF4 !important; border: 1px solid #BBF7D0 !important;
    color: #166534 !important; border-radius: 8px !important;
}
div[data-testid="stNotification"][kind="error"] {
    background: #FEF2F2 !important; border: 1px solid #FECACA !important;
    color: #991B1B !important; border-radius: 8px !important;
}
div[data-testid="stNotification"][kind="warning"] {
    background: #FFFBEB !important; border: 1px solid #FDE68A !important;
    color: #92400E !important; border-radius: 8px !important;
}
div[data-testid="stNotification"][kind="info"] {
    background: #EFF6FF !important; border: 1px solid #BFDBFE !important;
    color: #1E40AF !important; border-radius: 8px !important;
}

/* ── Expander ────────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: white !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    color: #374151 !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
}
.streamlit-expanderContent {
    background: #FAFAFA !important;
    border: 1px solid #E5E7EB !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* ── DataFrame ───────────────────────────────────────────────────────────── */
.stDataFrame {
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    background: white !important;
}

/* ── 標題 ────────────────────────────────────────────────────────────────── */
h1 {
    color: #14532d !important;
    font-weight: 700 !important;
    -webkit-text-fill-color: #14532d !important;
    background: none !important;
    font-size: 1.6rem !important;
    margin-bottom: 4px !important;
}
h2 {
    color: #1a2332 !important;
    font-weight: 600 !important;
    font-size: 1.2rem !important;
    margin-bottom: 4px !important;
}
h3 {
    color: #374151 !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
}
hr { border-color: #E5E7EB !important; margin: 1rem 0 !important; }
.stCaption, small { color: #9CA3AF !important; font-size: 0.78rem !important; }
.stCheckbox label { color: #374151 !important; font-size: 0.875rem !important; }

/* ── Column 等高對齊 ─────────────────────────────────────────────────────── */
div[data-testid="stHorizontalBlock"] {
    align-items: stretch !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
    display: flex !important;
    flex-direction: column !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div > div {
    flex: 1 !important;
}
.stSlider > div > div > div > div { background: #166534 !important; }
.stSpinner > div { border-top-color: #166534 !important; }

/* ── 功能卡片 ────────────────────────────────────────────────────────────── */
.feature-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 24px 20px;
    height: 100%;
    min-height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    transition: box-shadow 0.2s, transform 0.15s;
}
.feature-card:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}
.feature-card-icon { display: none; }
.feature-card-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #166534;
    margin-bottom: 8px;
}
.feature-card-desc { font-size: 0.85rem; color: #6B7280; line-height: 1.6; }

/* ── cyber-card 相容 ─────────────────────────────────────────────────────── */
.cyber-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 18px;
    margin: 6px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s, transform 0.15s;
}
.cyber-card:hover {
    box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    transform: translateY(-1px);
}

/* ── 動畫 ────────────────────────────────────────────────────────────────── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.fade-in { animation: fadeInUp 0.35s ease-out; }

@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 4px rgba(239,68,68,0.3); }
    50% { box-shadow: 0 0 14px rgba(239,68,68,0.5); }
}
.alert-pulse { animation: pulse-glow 2s infinite; }

/* ── 徽章 ────────────────────────────────────────────────────────────────── */
.badge-high {
    background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA;
    padding: 2px 9px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;
}
.badge-medium {
    background: #FFFBEB; color: #92400E; border: 1px solid #FDE68A;
    padding: 2px 9px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;
}
.badge-low {
    background: #F0FDF4; color: #166534; border: 1px solid #BBF7D0;
    padding: 2px 9px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;
}
.neon-text { color: #166534; font-weight: 600; }
.neon-red { color: #DC2626; font-weight: 600; }
</style>
"""


def inject_css() -> None:
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def card(content: str, glow: bool = False) -> str:
    extra = ' alert-pulse' if glow else ''
    return f'<div class="cyber-card{extra} fade-in">{content}</div>'


def badge(text: str, level: str = "medium") -> str:
    cls = {"高": "badge-high", "中": "badge-medium", "低": "badge-low"}.get(level, "badge-medium")
    return f'<span class="{cls}">{text}</span>'


def neon(text: str, color: str = "blue") -> str:
    cls = "neon-red" if color == "red" else "neon-text"
    return f'<span class="{cls}">{text}</span>'
