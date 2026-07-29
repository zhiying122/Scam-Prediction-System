"""
ScamDNA 全域 CSS — 專業商務風
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

/* ── 隱藏 Streamlit 預設元素（須 display:none，visibility:hidden 仍佔位）─── */
#MainMenu { display: none !important; }
footer { display: none !important; }
header,
header[data-testid="stHeader"],
[data-testid="stHeader"],
.stAppHeader,
[data-testid="stToolbar"],
.stAppToolbar,
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stDeployButton,
[data-testid="stAppDeployButton"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* ── 壓縮所有多餘空白（頂部貼齊自訂 header）─────────────────────────────── */
html, body {
    margin: 0 !important;
    padding: 0 !important;
}
.stApp {
    margin-top: 0 !important;
    padding-top: 0 !important;
    --header-height: 0px !important;
}
[data-testid="stAppViewContainer"],
.stAppViewContainer {
    padding-top: 0 !important;
    margin-top: 0 !important;
}
.main .block-container,
div[data-testid="stMainBlockContainer"],
.stMainBlockContainer {
    padding-top: calc(var(--scamdna-header-h, 106px) + 12px) !important;
    padding-left: 32px !important;
    padding-right: 32px !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
    width: 100% !important;
    margin-left: auto !important;
    margin-right: auto !important;
    margin-top: 0 !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
    overflow-y: visible !important;
    height: auto !important;
    max-height: none !important;
}
section[data-testid="stMain"],
section[data-testid="stMain"] > div,
section[data-testid="stMain"] > div:first-child {
    padding-top: 0 !important;
    margin-top: 0 !important;
}
.stMarkdown { margin-bottom: 0.25rem !important; }
div[data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
div[data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
/* 自訂 site-header 貼頂（完整規則另由父頁 _TOP_FLUSH_CSS 注入） */
.site-header {
    margin: 0 !important;
    padding: 0 !important;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
    z-index: 999999 !important;
}
[data-testid="stMarkdownContainer"]:has(.site-header),
div:has(> .site-header) {
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
}
/* 壓扁 height=0 的 components iframe／純 style 的 st.html，避免頂部米色空條 */
iframe[height="0"],
iframe[height="0px"] {
    display: block !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    width: 0 !important;
    border: none !important;
    margin: 0 !important;
    padding: 0 !important;
    position: absolute !important;
    overflow: hidden !important;
    visibility: hidden !important;
}
div:has(> iframe[height="0"]),
div:has(> iframe[height="0px"]),
[data-testid="stElementContainer"]:has(iframe[height="0"]),
[data-testid="element-container"]:has(iframe[height="0"]),
[data-testid="stVerticalBlockBorderWrapper"]:has(iframe[height="0"]) {
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    overflow: hidden !important;
}

/* 內容留白改由 block-container padding 統一處理，避免雙倍 margin 造成錯位 */

/* ── 頁面內容區域 ────────────────────────────────────────────────────────── */
.page-body {
    padding: 0;
    max-width: 100%;
    margin: 0;
    box-sizing: border-box;
}
.hero-section {
    margin: 0 0 8px !important;
    padding: 6px 0 2px !important;
    box-sizing: border-box !important;
    width: 100% !important;
    max-width: 100% !important;
}

/* ── Metric 卡片 ─────────────────────────────────────────────────────────── */
div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 12px !important;
    margin: 0 0 12px !important;
    padding: 0 !important;
    align-items: stretch !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}
div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div[data-testid="stColumn"] {
    flex: 1 1 0 !important;
    min-width: 0 !important;
    max-width: none !important;
    position: relative !important;
    top: auto !important;
    left: auto !important;
    transform: none !important;
    margin: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    box-sizing: border-box !important;
}
div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) [data-testid="stElementContainer"],
div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) [data-testid="element-container"] {
    position: relative !important;
    top: auto !important;
    left: auto !important;
    margin: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    height: auto !important;
    transform: none !important;
}
[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 10px !important;
    padding: 16px 18px !important;
    margin: 0 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    transition: box-shadow 0.2s !important;
    height: 100% !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    position: relative !important;
    overflow: hidden !important;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}
[data-testid="stMetricLabel"] {
    color: #4B5563 !important;
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
.stButton > button[kind="primary"],
.stForm button[kind="primary"],
.stForm button[data-testid="stBaseButton-primary"],
.stForm [data-testid="stFormSubmitButton"] button,
div[data-testid="stForm"] [data-testid="stFormSubmitButton"] > button {
    background: #166534 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
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
.stButton > button[kind="primary"] div,
.stForm button[kind="primary"] p,
.stForm button[kind="primary"] span,
.stForm button[kind="primary"] div,
.stForm button[data-testid="stBaseButton-primary"] p,
.stForm button[data-testid="stBaseButton-primary"] span,
.stForm button[data-testid="stBaseButton-primary"] div,
.stForm [data-testid="stFormSubmitButton"] button p,
.stForm [data-testid="stFormSubmitButton"] button span,
.stForm [data-testid="stFormSubmitButton"] button div,
.stForm [data-testid="stFormSubmitButton"] [data-testid="stMarkdownContainer"] p,
div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button p,
div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button span,
div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button div,
div[data-testid="stForm"] [data-testid="stFormSubmitButton"] [data-testid="stMarkdownContainer"] p {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
.stButton > button[data-testid="stBaseButton-primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover,
.stForm button[kind="primary"]:hover,
.stForm button[data-testid="stBaseButton-primary"]:hover,
.stForm [data-testid="stFormSubmitButton"] button:hover,
div[data-testid="stForm"] [data-testid="stFormSubmitButton"] > button:hover {
    background: #14532d !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
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
.stTextArea > div > div > textarea {
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
    border: 1px solid #D1D5DB !important;
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
/* placeholder 確保可讀（避免與輸入文字重疊或過淡） */
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #6B7280 !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #6B7280 !important;
}
.stTextInput input::-webkit-input-placeholder,
.stTextArea textarea::-webkit-input-placeholder {
    color: #6B7280 !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #6B7280 !important;
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
.stDataFrame,
[data-testid="stDataFrame"],
[data-testid="stDataFrameResizable"] {
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    overflow: auto !important;
    background: white !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}
div[data-testid="stElementContainer"]:has([data-testid="stDataFrame"]),
div[data-testid="element-container"]:has([data-testid="stDataFrame"]) {
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: auto !important;
    box-sizing: border-box !important;
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
.stCaption, small { color: #6B7280 !important; font-size: 0.78rem !important; }
.stCheckbox label { color: #374151 !important; font-size: 0.875rem !important; }

/* ── Form / Label 文字確保可見 ───────────────────────────────────────────── */
.stForm {
    background: white !important;
    border: 1px solid #9CA3AF !important;
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
/* Selectbox 選項文字（勿對所有 div 設樣式，以免蓋掉外框） */
.stSelectbox [data-baseweb="select"] span,
.stMultiSelect [data-baseweb="select"] span {
    color: #1a2332 !important;
}
/* Radio button label */
.stRadio [data-testid="stMarkdownContainer"] p {
    color: #1a2332 !important;
}
/* 一般段落文字 */
[data-testid="stMarkdownContainer"] p {
    color: #374151 !important;
}

/* ── Column 等高對齊（勿對深層強制 flex:1，避免 metric／表格被撐破）──────── */
div[data-testid="stHorizontalBlock"] {
    align-items: stretch !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
    min-width: 0 !important;
    box-sizing: border-box !important;
}
/* Vega / Altair 圖表不溢出 */
[data-testid="stVegaLiteChart"],
.stVegaLiteChart,
.stAltairChart {
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: auto !important;
    box-sizing: border-box !important;
}

/* ── Slider（Streamlit 1.58+ 使用 stSliderThumbValue / stSliderTickBar）──── */
[data-testid="stSlider"] {
    padding-top: 0.25rem !important;
    padding-bottom: 0.35rem !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] {
    margin-top: 1.6rem !important;
    margin-bottom: 1.35rem !important;
}
/* 目前數值、最小值、最大值：深色粗體 + 足夠字級 */
[data-testid="stSlider"] [data-testid="stSliderThumbValue"],
[data-testid="stSlider"] [data-testid="stSliderTickBar"],
[data-testid="stSlider"] [data-testid="stThumbValue"],
[data-testid="stSlider"] [data-testid="stTickBarMin"],
[data-testid="stSlider"] [data-testid="stTickBarMax"] {
    background: transparent !important;
    background-color: transparent !important;
    color: #1a2332 !important;
    -webkit-text-fill-color: #1a2332 !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    line-height: 1.2 !important;
    box-shadow: none !important;
    border: none !important;
    opacity: 1 !important;
    z-index: 2 !important;
}
[data-testid="stSlider"] [data-testid="stSliderThumbValue"] *,
[data-testid="stSlider"] [data-testid="stSliderTickBar"] *,
[data-testid="stSlider"] [data-testid="stThumbValue"] *,
[data-testid="stSlider"] [data-testid="stTickBarMin"] *,
[data-testid="stSlider"] [data-testid="stTickBarMax"] * {
    color: #1a2332 !important;
    -webkit-text-fill-color: #1a2332 !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    opacity: 1 !important;
}
/* 拖曳點上方數值：白底綠框，避免與軌道重疊 */
[data-testid="stSlider"] [data-testid="stSliderThumbValue"],
[data-testid="stSlider"] [data-testid="stThumbValue"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1.5px solid #166534 !important;
    border-radius: 6px !important;
    padding: 2px 10px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.12) !important;
    color: #14532d !important;
    -webkit-text-fill-color: #14532d !important;
    min-width: 1.5rem !important;
    text-align: center !important;
}
/* 軌道兩端最小／最大值 */
[data-testid="stSlider"] [data-testid="stSliderTickBar"] {
    color: #374151 !important;
    -webkit-text-fill-color: #374151 !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}
[data-testid="stSlider"] [data-testid="stSliderTickBar"] * {
    color: #374151 !important;
    -webkit-text-fill-color: #374151 !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}
/* track 未填充 */
[data-testid="stSlider"] [data-baseweb="slider"] > div:first-child {
    background: #D1D5DB !important;
}
/* track 已填充 */
[data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stTickBar"] {
    background: transparent !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] > div:first-child > div {
    background: #166534 !important;
}
/* thumb 圓點 */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background-color: #166534 !important;
    background: #166534 !important;
    border: 2px solid #ffffff !important;
    box-shadow: 0 0 0 2px rgba(22,101,52,0.35) !important;
}
[data-testid="stSlider"] input[type="range"]::-webkit-slider-thumb {
    background: #166534 !important;
    border: 2px solid #ffffff !important;
}
[data-testid="stSlider"] input[type="range"]::-moz-range-thumb {
    background: #166534 !important;
    border: 2px solid #ffffff !important;
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
.feature-card-desc { font-size: 0.85rem; color: #4B5563; line-height: 1.6; }

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
    grid-template-columns: repeat(3, minmax(0, 1fr));
    grid-auto-rows: 1fr;
    gap: 16px;
    margin: 0 0 12px !important;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
}
.feature-grid .feature-card {
    margin: 0;
    height: auto;
    min-height: unset;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
}
@media (max-width: 900px) {
    .feature-grid {
        grid-template-columns: 1fr;
    }
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

/* ── Selectbox / Multiselect 外框（置於最後以提高優先級）──────────────────── */
/* Streamlit 1.58：Baseweb 常用 inset box-shadow 當邊框；不可設 box-shadow:none */
.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"],
div[data-baseweb="select"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1.5px solid #6B7280 !important;
    border-radius: 6px !important;
    box-shadow: inset 0 0 0 1px #6B7280 !important;
    min-height: 40px !important;
}
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div,
div[data-baseweb="select"] > div {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1.5px solid #6B7280 !important;
    border-radius: 6px !important;
    box-shadow: inset 0 0 0 1px #6B7280 !important;
    min-height: 38px !important;
}
/* 控制列（label 下方的實際選單列） */
.stSelectbox > div:not(:first-child),
.stMultiSelect > div:not(:first-child) {
    border: 1.5px solid #6B7280 !important;
    border-radius: 6px !important;
    background: #ffffff !important;
    box-shadow: inset 0 0 0 1px #6B7280 !important;
}
.stForm .stSelectbox > div:not(:first-child),
.stForm .stMultiSelect > div:not(:first-child),
.stForm div[data-baseweb="select"],
.stForm div[data-baseweb="select"] > div {
    border: 1.5px solid #6B7280 !important;
    border-radius: 6px !important;
    background: #ffffff !important;
    box-shadow: inset 0 0 0 1px #6B7280 !important;
}
.stSelectbox [data-baseweb="select"]:hover,
.stSelectbox [data-baseweb="select"]:hover > div,
.stSelectbox > div:not(:first-child):hover,
.stForm .stSelectbox > div:not(:first-child):hover {
    border-color: #374151 !important;
    box-shadow: inset 0 0 0 1px #374151 !important;
}
.stSelectbox [data-baseweb="select"]:focus-within,
.stSelectbox [data-baseweb="select"]:focus-within > div,
.stSelectbox > div:not(:first-child):focus-within {
    border-color: #166534 !important;
    box-shadow: inset 0 0 0 1px #166534, 0 0 0 2px rgba(22,101,52,0.15) !important;
}
</style>
"""

# 下拉選單外框：經由父頁 head 注入，避免 st.html DOMPurify 剝除屬性選擇器
_SELECTBOX_BORDER_CSS = """
.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"],
div[data-baseweb="select"] {
  background: #ffffff !important;
  border: 1.5px solid #6B7280 !important;
  border-radius: 6px !important;
  box-shadow: inset 0 0 0 1px #6B7280 !important;
  min-height: 40px !important;
}
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div,
div[data-baseweb="select"] > div {
  background: #ffffff !important;
  border: 1.5px solid #6B7280 !important;
  border-radius: 6px !important;
  box-shadow: inset 0 0 0 1px #6B7280 !important;
  min-height: 38px !important;
}
.stSelectbox > div:not(:first-child),
.stMultiSelect > div:not(:first-child),
.stForm .stSelectbox > div:not(:first-child),
.stForm .stMultiSelect > div:not(:first-child) {
  border: 1.5px solid #6B7280 !important;
  border-radius: 6px !important;
  background: #ffffff !important;
  box-shadow: inset 0 0 0 1px #6B7280 !important;
}
.stSelectbox div[role="combobox"],
.stForm .stSelectbox div[role="combobox"],
.stSelectbox div[role="button"],
.stForm .stSelectbox div[role="button"] {
  border: 1.5px solid #6B7280 !important;
  border-radius: 6px !important;
  background: #ffffff !important;
  box-shadow: inset 0 0 0 1px #6B7280 !important;
  min-height: 38px !important;
}
"""


# 頂部貼齊：經父頁 head 注入（st.html DOMPurify 會剝除屬性選擇器）
# 策略：site-header 固定貼頂；主內容用 padding 避開；禁止負 margin / absolute 拉飛元件
_TOP_FLUSH_CSS = """
html, body, .stApp {
  margin: 0 !important;
  padding: 0 !important;
  --header-height: 0px !important;
  --scamdna-header-h: 106px;
  overflow-x: hidden !important;
  overflow-y: auto !important;
  height: auto !important;
  max-height: none !important;
}
[data-testid="stAppViewContainer"],
.stAppViewContainer,
section[data-testid="stMain"],
.main,
.main .block-container,
div[data-testid="stMainBlockContainer"],
.stMainBlockContainer {
  overflow-x: hidden !important;
  overflow-y: visible !important;
  height: auto !important;
  max-height: none !important;
}
.stApp, [data-testid="stAppViewContainer"] {
  min-height: 100vh !important;
}
header,
header[data-testid="stHeader"],
[data-testid="stHeader"],
.stAppHeader,
[data-testid="stToolbar"],
.stAppToolbar,
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stDeployButton,
[data-testid="stAppDeployButton"] {
  display: none !important;
  height: 0 !important;
  min-height: 0 !important;
  max-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  overflow: hidden !important;
  visibility: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
}
[data-testid="stAppViewContainer"],
.stAppViewContainer,
section[data-testid="stMain"],
section[data-testid="stMain"] > div {
  padding-top: 0 !important;
  margin-top: 0 !important;
}
.site-header {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  width: 100% !important;
  max-width: 100vw !important;
  margin: 0 !important;
  padding: 0 !important;
  z-index: 999999 !important;
  box-sizing: border-box !important;
}
[data-testid="stMarkdownContainer"]:has(.site-header),
div:has(> .site-header) {
  height: 0 !important;
  min-height: 0 !important;
  max-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  overflow: visible !important;
}
.main .block-container,
div[data-testid="stMainBlockContainer"],
.stMainBlockContainer {
  padding-top: calc(var(--scamdna-header-h) + 12px) !important;
  padding-left: 32px !important;
  padding-right: 32px !important;
  padding-bottom: 2rem !important;
  max-width: 1400px !important;
  width: 100% !important;
  margin-left: auto !important;
  margin-right: auto !important;
  margin-top: 0 !important;
  box-sizing: border-box !important;
  overflow-x: hidden !important;
  overflow-y: visible !important;
  height: auto !important;
  max-height: none !important;
}
iframe[height="0"],
iframe[height="0px"] {
  display: block !important;
  height: 0 !important;
  min-height: 0 !important;
  max-height: 0 !important;
  width: 0 !important;
  border: none !important;
  margin: 0 !important;
  padding: 0 !important;
  position: absolute !important;
  left: -9999px !important;
  top: 0 !important;
  overflow: hidden !important;
  visibility: hidden !important;
  pointer-events: none !important;
}
/* 僅壓扁「只有」零高 iframe 的空殼，勿用過寬 :has 誤傷內容 */
[data-testid="stElementContainer"]:has(> iframe[height="0"]):not(:has([data-testid="stMetric"])):not(:has(.site-header)):not(:has(table)):not(:has([data-testid="stDataFrame"])),
[data-testid="element-container"]:has(> iframe[height="0"]):not(:has([data-testid="stMetric"])):not(:has(.site-header)) {
  height: 0 !important;
  min-height: 0 !important;
  max-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  overflow: hidden !important;
}
.hero-section {
  margin: 0 0 8px !important;
  padding: 6px 0 2px !important;
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
}
div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  gap: 12px !important;
  margin: 0 0 12px !important;
  padding: 0 !important;
  align-items: stretch !important;
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
}
div[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > div[data-testid="stColumn"] {
  flex: 1 1 0 !important;
  min-width: 0 !important;
  position: relative !important;
  top: auto !important;
  left: auto !important;
  transform: none !important;
  margin: 0 !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
  box-sizing: border-box !important;
}
[data-testid="stMetric"] {
  margin: 0 !important;
  border: 1px solid #D1D5DB !important;
  height: 100% !important;
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
  position: relative !important;
  overflow: hidden !important;
}
.stDataFrame,
[data-testid="stDataFrame"],
[data-testid="stVegaLiteChart"],
.stAltairChart {
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
}
"""


def inject_html(html: str) -> None:
    """注入 HTML/CSS（Streamlit 1.58+ 需用 st.html，勿用 st.markdown 包 <style>）。"""
    import streamlit as st
    st.html(html)


def _inject_parent_css(style_id: str, css: str) -> None:
    """把 CSS 寫進父頁 head（繞過 st.html DOMPurify）。"""
    import streamlit.components.v1 as components

    css_escaped = css.replace("\\", "\\\\").replace("`", "\\`")
    components.html(
        f"""
        <script>
        (function () {{
          const id = "{style_id}";
          let doc;
          try {{ doc = window.top.document; }} catch (e) {{
            try {{ doc = window.parent.document; }} catch (e2) {{ return; }}
          }}
          if (!doc || !doc.head) return;
          let el = doc.getElementById(id);
          if (!el) {{
            el = doc.createElement("style");
            el.id = id;
            doc.head.appendChild(el);
          }}
          el.textContent = `{css_escaped}`;
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def _inject_selectbox_border_into_parent() -> None:
    """把下拉選單邊框 CSS 寫進父頁 head（繞過 st.html 過濾）。"""
    _inject_parent_css("scamdna-selectbox-border-css", _SELECTBOX_BORDER_CSS)


def _inject_top_flush_into_parent() -> None:
    """綠列固定貼頂：只調 header 與主容器 padding，不拉飛任何內容框。"""
    import streamlit.components.v1 as components

    css = _TOP_FLUSH_CSS.replace("\\", "\\\\").replace("`", "\\`")
    components.html(
        f"""
        <script>
        (function () {{
          let doc;
          try {{ doc = window.top.document; }} catch (e) {{
            try {{ doc = window.parent.document; }} catch (e2) {{ return; }}
          }}
          if (!doc || !doc.head) return;

          const id = "scamdna-top-flush-css";
          let el = doc.getElementById(id);
          if (!el) {{
            el = doc.createElement("style");
            el.id = id;
            doc.head.appendChild(el);
          }}
          el.textContent = `{css}`;

          function repairBrokenInline() {{
            // 清掉先前負 margin / absolute 造成的跨框、突出
            const broken = doc.querySelectorAll(
              '[data-testid="stMetric"], [data-testid="stColumn"], ' +
              '[data-testid="stHorizontalBlock"], [data-testid="stElementContainer"], ' +
              '[data-testid="element-container"], [data-testid="stDataFrame"]'
            );
            broken.forEach(function (node) {{
              if (!node || !node.style) return;
              const mt = node.style.marginTop || "";
              if (mt && (mt.startsWith("-") || parseFloat(mt) < 0)) {{
                node.style.removeProperty("margin-top");
              }}
              const pos = (node.style.position || "").toLowerCase();
              if (pos === "absolute" || pos === "fixed") {{
                // 勿動真正的 site-header；其餘內容框拉回文件流
                if (node.classList && node.classList.contains("site-header")) return;
                if (node.querySelector && node.querySelector(".site-header")) return;
                node.style.removeProperty("position");
                node.style.removeProperty("top");
                node.style.removeProperty("left");
                node.style.removeProperty("right");
                node.style.removeProperty("width");
                node.style.removeProperty("height");
                node.style.removeProperty("max-height");
                node.style.removeProperty("opacity");
                node.style.removeProperty("pointer-events");
                node.style.removeProperty("transform");
              }}
            }});
          }}

          function flushTop() {{
            const header = doc.querySelector(".site-header");
            if (!header) return;

            header.style.setProperty("position", "fixed", "important");
            header.style.setProperty("top", "0px", "important");
            header.style.setProperty("left", "0", "important");
            header.style.setProperty("right", "0", "important");
            header.style.setProperty("width", "100%", "important");
            header.style.setProperty("z-index", "999999", "important");
            header.style.setProperty("margin", "0", "important");
            header.style.setProperty("transform", "none", "important");

            repairBrokenInline();

            const h = Math.max(96, Math.ceil(header.getBoundingClientRect().height || 106));
            doc.documentElement.style.setProperty("--scamdna-header-h", h + "px");
            const padTop = h + 12;
            const mains = doc.querySelectorAll(
              '.main .block-container, div[data-testid="stMainBlockContainer"], .stMainBlockContainer'
            );
            mains.forEach(function (m) {{
              [
                "height", "max-height", "min-height", "overflow", "margin-left",
                "margin-right", "width", "max-width", "display", "justify-content",
                "align-items", "position", "top", "left"
              ].forEach(function (p) {{ m.style.removeProperty(p); }});
              m.style.setProperty("height", "auto", "important");
              m.style.setProperty("max-height", "none", "important");
              m.style.setProperty("overflow-x", "hidden", "important");
              m.style.setProperty("overflow-y", "visible", "important");
              m.style.setProperty("padding-top", padTop + "px", "important");
              m.style.setProperty("padding-left", "32px", "important");
              m.style.setProperty("padding-right", "32px", "important");
              m.style.setProperty("margin-top", "0", "important");
              m.style.setProperty("margin-left", "auto", "important");
              m.style.setProperty("margin-right", "auto", "important");
              m.style.setProperty("max-width", "1400px", "important");
              m.style.setProperty("width", "100%", "important");
              m.style.setProperty("box-sizing", "border-box", "important");
            }});
            [doc.documentElement, doc.body].forEach(function (n) {{
              if (!n || !n.style) return;
              n.style.setProperty("overflow-x", "hidden", "important");
              n.style.setProperty("overflow-y", "auto", "important");
              n.style.setProperty("height", "auto", "important");
              n.style.setProperty("max-height", "none", "important");
            }});
          }}

          let timer = null;
          let runs = 0;
          function scheduleFlush() {{
            if (timer) return;
            timer = setTimeout(function () {{
              timer = null;
              flushTop();
              runs += 1;
              // 幾次穩定後停止 observer，避免持續改 DOM 造成版面抖動
              if (runs >= 8 && window.__scamdnaTopFlushObs) {{
                try {{ window.__scamdnaTopFlushObs.disconnect(); }} catch (e) {{}}
                window.__scamdnaTopFlushObs = null;
              }}
            }}, 120);
          }}

          flushTop();
          setTimeout(flushTop, 80);
          setTimeout(flushTop, 400);
          try {{
            // 先斷開舊 observer（避免熱重載後仍跑舊版負 margin 邏輯）
            if (window.__scamdnaTopFlushObs) {{
              try {{ window.__scamdnaTopFlushObs.disconnect(); }} catch (e) {{}}
              window.__scamdnaTopFlushObs = null;
            }}
            window.__scamdnaTopFlushObs = new MutationObserver(scheduleFlush);
            window.__scamdnaTopFlushObs.observe(doc.body, {{ childList: true, subtree: true }});
            window.__scamdnaLayoutVersion = 3;
          }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def inject_css() -> None:
    inject_html(GLOBAL_CSS)
    _inject_top_flush_into_parent()
    _inject_selectbox_border_into_parent()


def card(content: str, glow: bool = False) -> str:
    extra = ' alert-pulse' if glow else ''
    return f'<div class="cyber-card{extra} fade-in">{content}</div>'


def badge(text: str, level: str = "medium") -> str:
    cls = {"高": "badge-high", "中": "badge-medium", "低": "badge-low"}.get(level, "badge-medium")
    return f'<span class="{cls}">{text}</span>'


def neon(text: str, color: str = "blue") -> str:
    cls = "neon-red" if color == "red" else "neon-text"
    return f'<span class="{cls}">{text}</span>'
