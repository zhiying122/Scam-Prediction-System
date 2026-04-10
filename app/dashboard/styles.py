"""
全域 CSS 樣式注入模組

提供暗色系科技感主題，包含：
- 深色背景 + 霓虹藍/紅漸層
- 卡片式 UI 元件
- 動畫效果（脈衝、漸入）
- 自訂 metric、button、sidebar 樣式
"""

GLOBAL_CSS = """
<style>
/* ── 全域字體與背景 ─────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', 'Microsoft JhengHei', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1b2a 50%, #0a0e1a 100%);
    color: #e2e8f0;
}

/* ── 側邊欄 ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1b2a 0%, #0a1628 100%);
    border-right: 1px solid rgba(0, 212, 255, 0.15);
}

[data-testid="stSidebar"] .stRadio label {
    color: #94a3b8 !important;
    transition: color 0.2s;
}

[data-testid="stSidebar"] .stRadio label:hover {
    color: #00d4ff !important;
}

/* ── 標題樣式 ────────────────────────────────────────────────────────────── */
h1 {
    background: linear-gradient(90deg, #00d4ff, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700 !important;
    letter-spacing: -0.5px;
}

h2, h3 {
    color: #e2e8f0 !important;
    font-weight: 600 !important;
}

/* ── Metric 卡片 ─────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.05), rgba(124, 58, 237, 0.05));
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 12px;
    padding: 16px !important;
    transition: border-color 0.3s, transform 0.2s;
}

[data-testid="stMetric"]:hover {
    border-color: rgba(0, 212, 255, 0.5);
    transform: translateY(-2px);
}

[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

[data-testid="stMetricValue"] {
    color: #00d4ff !important;
    font-weight: 700 !important;
    font-size: 1.8rem !important;
}

[data-testid="stMetricDelta"] {
    font-size: 0.85rem !important;
}

/* ── 按鈕 ────────────────────────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00d4ff, #7c3aed) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px;
    transition: opacity 0.2s, transform 0.2s !important;
    box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
}

.stButton > button[kind="primary"]:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4) !important;
}

.stButton > button:not([kind="primary"]) {
    background: rgba(255, 255, 255, 0.05) !important;
    color: #94a3b8 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}

.stButton > button:not([kind="primary"]):hover {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #e2e8f0 !important;
    border-color: rgba(0, 212, 255, 0.3) !important;
}

/* ── 輸入框 ──────────────────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(0, 212, 255, 0.2) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    transition: border-color 0.2s;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(0, 212, 255, 0.6) !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.1) !important;
}

/* ── 進度條 ──────────────────────────────────────────────────────────────── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #00d4ff, #7c3aed) !important;
    border-radius: 4px;
}

.stProgress > div > div > div {
    background: rgba(255, 255, 255, 0.08) !important;
    border-radius: 4px;
}

/* ── Alert / Info / Success / Warning / Error ────────────────────────────── */
.stAlert {
    border-radius: 10px !important;
    border: none !important;
}

[data-testid="stNotification"] {
    border-radius: 10px !important;
}

div[data-testid="stNotification"][kind="success"] {
    background: rgba(16, 185, 129, 0.1) !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
    color: #6ee7b7 !important;
}

div[data-testid="stNotification"][kind="error"] {
    background: rgba(239, 68, 68, 0.1) !important;
    border: 1px solid rgba(239, 68, 68, 0.3) !important;
    color: #fca5a5 !important;
}

div[data-testid="stNotification"][kind="warning"] {
    background: rgba(245, 158, 11, 0.1) !important;
    border: 1px solid rgba(245, 158, 11, 0.3) !important;
    color: #fcd34d !important;
}

div[data-testid="stNotification"][kind="info"] {
    background: rgba(59, 130, 246, 0.1) !important;
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    color: #93c5fd !important;
}

/* ── Expander ────────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(0, 212, 255, 0.15) !important;
    border-radius: 8px !important;
    color: #94a3b8 !important;
}

.streamlit-expanderContent {
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(0, 212, 255, 0.1) !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* ── DataFrame / Table ───────────────────────────────────────────────────── */
.stDataFrame {
    border: 1px solid rgba(0, 212, 255, 0.15) !important;
    border-radius: 10px !important;
    overflow: hidden;
}

/* ── Divider ─────────────────────────────────────────────────────────────── */
hr {
    border-color: rgba(0, 212, 255, 0.1) !important;
}

/* ── Caption / Small text ────────────────────────────────────────────────── */
.stCaption, small, .caption {
    color: #64748b !important;
}

/* ── Checkbox ────────────────────────────────────────────────────────────── */
.stCheckbox label {
    color: #94a3b8 !important;
}

/* ── Slider ──────────────────────────────────────────────────────────────── */
.stSlider > div > div > div > div {
    background: linear-gradient(90deg, #00d4ff, #7c3aed) !important;
}

/* ── Spinner ─────────────────────────────────────────────────────────────── */
.stSpinner > div {
    border-top-color: #00d4ff !important;
}

/* ── 自訂卡片元件 ────────────────────────────────────────────────────────── */
.cyber-card {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.05), rgba(124, 58, 237, 0.05));
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 12px;
    padding: 20px;
    margin: 8px 0;
    transition: border-color 0.3s, transform 0.2s;
}

.cyber-card:hover {
    border-color: rgba(0, 212, 255, 0.4);
    transform: translateY(-2px);
}

/* ── 脈衝動畫（用於警示） ────────────────────────────────────────────────── */
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 5px rgba(239, 68, 68, 0.3); }
    50% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.6); }
}

.alert-pulse {
    animation: pulse-glow 2s infinite;
}

/* ── 漸入動畫 ────────────────────────────────────────────────────────────── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.fade-in {
    animation: fadeInUp 0.5s ease-out;
}

/* ── 霓虹文字 ────────────────────────────────────────────────────────────── */
.neon-text {
    color: #00d4ff;
    text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.neon-red {
    color: #ff4757;
    text-shadow: 0 0 10px rgba(255, 71, 87, 0.5);
}

/* ── 風險等級徽章 ────────────────────────────────────────────────────────── */
.badge-high {
    background: rgba(239, 68, 68, 0.15);
    color: #fca5a5;
    border: 1px solid rgba(239, 68, 68, 0.3);
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

.badge-medium {
    background: rgba(245, 158, 11, 0.15);
    color: #fcd34d;
    border: 1px solid rgba(245, 158, 11, 0.3);
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

.badge-low {
    background: rgba(16, 185, 129, 0.15);
    color: #6ee7b7;
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

/* ── 隱藏 Streamlit 預設元素 ─────────────────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* ── 主內容區域 ──────────────────────────────────────────────────────────── */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}
</style>
"""


def inject_css() -> None:
    """注入全域 CSS 樣式到 Streamlit 頁面"""
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def card(content: str, glow: bool = False) -> str:
    """生成卡片 HTML"""
    extra = ' alert-pulse' if glow else ''
    return f'<div class="cyber-card{extra} fade-in">{content}</div>'


def badge(text: str, level: str = "medium") -> str:
    """生成風險等級徽章 HTML"""
    cls = {"高": "badge-high", "中": "badge-medium", "低": "badge-low"}.get(level, "badge-medium")
    return f'<span class="{cls}">{text}</span>'


def neon(text: str, color: str = "blue") -> str:
    """生成霓虹文字 HTML"""
    cls = "neon-red" if color == "red" else "neon-text"
    return f'<span class="{cls}">{text}</span>'
