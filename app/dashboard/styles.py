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
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;600;700;800&display=swap');

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
.stMarkdown { margin-bottom: 0.25rem !important; }
div[data-testid="stVerticalBlock"] > div { gap: 0.75rem !important; }

/* 子頁面內容留白（header 維持全寬） */
section[data-testid="stMain"] h1,
section[data-testid="stMain"] h2,
section[data-testid="stMain"] h3,
section[data-testid="stMain"] .stTextArea,
section[data-testid="stMain"] .stTextInput,
section[data-testid="stMain"] [data-testid="stButton"],
section[data-testid="stMain"] [data-testid="stForm"],
section[data-testid="stMain"] [data-testid="stSelectbox"],
section[data-testid="stMain"] [data-testid="stSlider"],
section[data-testid="stMain"] [data-testid="stCheckbox"],
section[data-testid="stMain"] [data-testid="stMetric"],
section[data-testid="stMain"] [data-testid="stDataFrame"],
section[data-testid="stMain"] [data-testid="stNotification"],
section[data-testid="stMain"] [data-testid="stExpander"],
section[data-testid="stMain"] [data-testid="stProgress"],
section[data-testid="stMain"] > div > div[data-testid="stVerticalBlock"] > div > [data-testid="stMarkdownContainer"] {
    margin-left: 32px !important;
    margin-right: 32px !important;
}

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
/* Streamlit 1.58+ 使用 data-testid="stBaseButton-primary"，舊版使用 kind="primary" */
.stButton > button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primary"],
.stButton > button[kind="primary"] {
    background: #166534 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    box-shadow: 0 1px 4px rgba(22,101,52,0.2) !important;
    transition: background 0.15s !important;
}
.stButton > button[data-testid="stBaseButton-primary"] p,
.stButton > button[data-testid="stBaseButton-primary"] span,
.stButton > button[data-testid="stBaseButton-primary"] div,
button[data-testid="stBaseButton-primary"] p,
button[data-testid="stBaseButton-primary"] span,
button[data-testid="stBaseButton-primary"] div,
.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span,
.stButton > button[kind="primary"] div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
.stButton > button[data-testid="stBaseButton-primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover {
    background: #14532d !important;
    color: #ffffff !important;
}
.stButton > button[data-testid="stBaseButton-secondary"],
.stButton > button[data-testid="stBaseButton-tertiary"],
button[data-testid="stBaseButton-secondary"],
button[data-testid="stBaseButton-tertiary"],
.stButton > button:not([data-testid="stBaseButton-primary"]):not([kind="primary"]) {
    background: white !important;
    color: #374151 !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 6px !important;
    font-size: 0.875rem !important;
}
.stButton > button[data-testid="stBaseButton-secondary"] p,
.stButton > button[data-testid="stBaseButton-secondary"] span,
.stButton > button[data-testid="stBaseButton-secondary"] div,
.stButton > button[data-testid="stBaseButton-tertiary"] p,
.stButton > button[data-testid="stBaseButton-tertiary"] span,
.stButton > button[data-testid="stBaseButton-tertiary"] div,
button[data-testid="stBaseButton-secondary"] p,
button[data-testid="stBaseButton-secondary"] span,
button[data-testid="stBaseButton-secondary"] div,
button[data-testid="stBaseButton-tertiary"] p,
button[data-testid="stBaseButton-tertiary"] span,
button[data-testid="stBaseButton-tertiary"] div,
.stButton > button:not([data-testid="stBaseButton-primary"]):not([kind="primary"]) p,
.stButton > button:not([data-testid="stBaseButton-primary"]):not([kind="primary"]) span,
.stButton > button:not([data-testid="stBaseButton-primary"]):not([kind="primary"]) div {
    color: #374151 !important;
    -webkit-text-fill-color: #374151 !important;
}
.stButton > button[data-testid="stBaseButton-secondary"]:hover,
.stButton > button[data-testid="stBaseButton-tertiary"]:hover,
button[data-testid="stBaseButton-secondary"]:hover,
button[data-testid="stBaseButton-tertiary"]:hover,
.stButton > button:not([data-testid="stBaseButton-primary"]):not([kind="primary"]):hover {
    border-color: #166534 !important;
    color: #166534 !important;
}
.stButton > button[data-testid="stBaseButton-secondary"]:hover p,
.stButton > button[data-testid="stBaseButton-secondary"]:hover span,
.stButton > button[data-testid="stBaseButton-secondary"]:hover div,
.stButton > button[data-testid="stBaseButton-tertiary"]:hover p,
.stButton > button[data-testid="stBaseButton-tertiary"]:hover span,
.stButton > button[data-testid="stBaseButton-tertiary"]:hover div,
.stButton > button:not([data-testid="stBaseButton-primary"]):not([kind="primary"]):hover p,
.stButton > button:not([data-testid="stBaseButton-primary"]):not([kind="primary"]):hover span,
.stButton > button:not([data-testid="stBaseButton-primary"]):not([kind="primary"]):hover div {
    color: #166534 !important;
    -webkit-text-fill-color: #166534 !important;
}
/* 主按鈕 disabled 狀態仍保持可讀文字 */
.stButton > button[data-testid="stBaseButton-primary"]:disabled,
button[data-testid="stBaseButton-primary"]:disabled,
.stButton > button[kind="primary"]:disabled {
    background: #86efac !important;
    color: #14532d !important;
    opacity: 1 !important;
}
.stButton > button[data-testid="stBaseButton-primary"]:disabled p,
.stButton > button[data-testid="stBaseButton-primary"]:disabled span,
.stButton > button[data-testid="stBaseButton-primary"]:disabled div,
button[data-testid="stBaseButton-primary"]:disabled p,
button[data-testid="stBaseButton-primary"]:disabled span,
button[data-testid="stBaseButton-primary"]:disabled div,
.stButton > button[kind="primary"]:disabled p,
.stButton > button[kind="primary"]:disabled span,
.stButton > button[kind="primary"]:disabled div {
    color: #14532d !important;
    -webkit-text-fill-color: #14532d !important;
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
/* Streamlit 1.58+ baseweb 外層容器（避免灰底看起來像 disabled）
   注意：勿用 [data-testid="stTextArea"]，st.html 的 DOMPurify 會整段剝除 */
.stTextArea {
    pointer-events: auto !important;
}
.stTextArea [data-baseweb="textarea"],
.stTextArea [data-baseweb="base-input"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1px solid #D1D5DB !important;
    border-color: #D1D5DB !important;
    border-radius: 6px !important;
    opacity: 1 !important;
    cursor: text !important;
}
.stTextArea > div > div > textarea,
.stTextArea textarea {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #1a2332 !important;
    -webkit-text-fill-color: #1a2332 !important;
    font-size: 0.875rem !important;
    cursor: text !important;
    pointer-events: auto !important;
    opacity: 1 !important;
    caret-color: #1a2332 !important;
}
.stTextArea textarea:disabled,
.stTextArea textarea[readonly] {
    background: #ffffff !important;
    color: #1a2332 !important;
    -webkit-text-fill-color: #1a2332 !important;
    opacity: 1 !important;
    cursor: text !important;
}
.stTextInput [data-baseweb="input"] {
    background: #ffffff !important;
    border-color: #D1D5DB !important;
    border-radius: 6px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stTextArea textarea:focus,
.stTextArea [data-baseweb="textarea"]:focus-within,
.stTextInput [data-baseweb="input"]:focus-within {
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
/* 表格標題置中，數值靠右 */
.stDataFrame th {
    text-align: center !important;
    font-weight: 600 !important;
}
.stDataFrame td {
    text-align: right !important;
}
.stDataFrame td:first-child {
    text-align: left !important;
}
[data-testid="stDataFrame"] [role="columnheader"] {
    text-align: center !important;
    justify-content: center !important;
}
[data-testid="stDataFrame"] [role="gridcell"] {
    text-align: right !important;
    justify-content: flex-end !important;
}
/* glide-data-grid 內部 cell 對齊 */
[data-testid="stDataFrame"] canvas + div [role="columnheader"] span,
[data-testid="stDataFrame"] .dvn-scroller [role="columnheader"] {
    text-align: center !important;
    display: flex !important;
    justify-content: center !important;
}
[data-testid="stDataFrame"] .dvn-scroller [role="gridcell"] {
    text-align: right !important;
    display: flex !important;
    justify-content: flex-end !important;
}
/* st.table 對齊 */
.stTable thead th {
    text-align: center !important;
    font-weight: 600 !important;
    background: #F9FAFB !important;
}
.stTable tbody td {
    text-align: right !important;
}
.stTable tbody td:first-child {
    text-align: left !important;
}

/* ── Pandas Styler HTML 表格美化 ─────────────────────────────────────────── */
table.dataframe,
[data-testid="stMarkdownContainer"] table {
    width: 100% !important;
    border-collapse: collapse !important;
    background: white !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    font-size: 0.875rem !important;
    margin: 8px 0 !important;
}
table.dataframe th,
[data-testid="stMarkdownContainer"] table th {
    text-align: center !important;
    font-weight: 600 !important;
    background: #F9FAFB !important;
    color: #374151 !important;
    padding: 10px 14px !important;
    border-bottom: 2px solid #E5E7EB !important;
    font-size: 0.82rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.3px !important;
}
table.dataframe td,
[data-testid="stMarkdownContainer"] table td {
    text-align: right !important;
    padding: 8px 14px !important;
    border-bottom: 1px solid #F3F4F6 !important;
    color: #374151 !important;
}
table.dataframe td:first-child,
[data-testid="stMarkdownContainer"] table td:first-child {
    text-align: left !important;
    font-weight: 500 !important;
}
table.dataframe tbody tr:hover,
[data-testid="stMarkdownContainer"] table tbody tr:hover {
    background: #F9FAFB !important;
}
table.dataframe tbody tr:last-child td,
[data-testid="stMarkdownContainer"] table tbody tr:last-child td {
    border-bottom: none !important;
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

/* ── Form / Label 文字確保可見 ───────────────────────────────────────────── */
.stForm {
    background: white !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    padding: 16px !important;
}
/* 所有 label 文字 */
label, .stTextInput label, .stTextArea label,
.stSelectbox label, .stSlider label,
.stCheckbox label, .stRadio label,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span {
    color: #1a2332 !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
}
/* Selectbox 選項文字 */
.stSelectbox [data-baseweb="select"] span,
.stSelectbox [data-baseweb="select"] div {
    color: #1a2332 !important;
}
/* Slider 數值標籤 */
.stSlider [data-testid="stThumbValue"],
.stSlider [data-testid="stTickBarMin"],
.stSlider [data-testid="stTickBarMax"] {
    color: #374151 !important;
}
/* Radio button label */
.stRadio [data-testid="stMarkdownContainer"] p {
    color: #1a2332 !important;
}
/* 一般段落文字 */
[data-testid="stMarkdownContainer"] p {
    color: #374151 !important;
}

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
/* Slider thumb（拖曳圓點）與 track 確保在白色背景上可見 */
.stSlider [data-testid="stThumbValue"] { color: #166534 !important; }
.stSlider input[type="range"]::-webkit-slider-thumb {
    background: #166534 !important;
    border: 2px solid #166534 !important;
}
.stSlider input[type="range"]::-moz-range-thumb {
    background: #166534 !important;
    border: 2px solid #166534 !important;
}
/* Slider track 底色（未填充部分）確保可見 */
.stSlider [data-baseweb="slider"] > div:first-child {
    background: #D1D5DB !important;
}
/* Slider 已填充部分 */
.stSlider [data-baseweb="slider"] > div:first-child > div {
    background: #166534 !important;
}
/* Slider thumb 圓點 */
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: #166534 !important;
    border-color: #166534 !important;
    box-shadow: 0 0 0 2px rgba(22,101,52,0.3) !important;
}
.stSpinner > div { border-top-color: #166534 !important; }

/* ── Checkbox 確保勾選框在白色背景上可見 ─────────────────────────────────── */
.stCheckbox [data-testid="stCheckbox"] > label > div:first-child {
    border-color: #6B7280 !important;
}
.stCheckbox [data-testid="stCheckbox"] > label > div:first-child[aria-checked="true"] {
    background-color: #166534 !important;
    border-color: #166534 !important;
}
/* Streamlit checkbox 內部 SVG 勾勾顏色 */
.stCheckbox svg { fill: white !important; }
/* baseweb checkbox 樣式覆蓋 */
[data-baseweb="checkbox"] > div:first-child {
    border-color: #6B7280 !important;
    border-width: 2px !important;
}
[data-baseweb="checkbox"][aria-checked="true"] > div:first-child {
    background-color: #166534 !important;
    border-color: #166534 !important;
}
/* 確保 checkbox label 文字可見 */
[data-baseweb="checkbox"] label {
    color: #374151 !important;
}

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

@keyframes marquee {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-auto-rows: 1fr;
    gap: 16px;
    margin-bottom: 8px;
}
.feature-grid .feature-card {
    margin: 0;
    height: auto;
    min-height: unset;
}

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


def inject_html(html: str) -> None:
    """注入 HTML/CSS（Streamlit 1.58+ 需用 st.html，勿用 st.markdown 包 <style>）。"""
    import streamlit as st
    st.html(html)


def inject_css() -> None:
    inject_html(GLOBAL_CSS)


def card(content: str, glow: bool = False) -> str:
    extra = ' alert-pulse' if glow else ''
    return f'<div class="cyber-card{extra} fade-in">{content}</div>'


def badge(text: str, level: str = "medium") -> str:
    cls = {"高": "badge-high", "中": "badge-medium", "低": "badge-low"}.get(level, "badge-medium")
    return f'<span class="{cls}">{text}</span>'


def neon(text: str, color: str = "blue") -> str:
    cls = "neon-red" if color == "red" else "neon-text"
    return f'<span class="{cls}">{text}</span>'
