"""
AEGIS CORE — AI 詐騙進化預測系統
啟動指令：python -m streamlit run app/dashboard/streamlit_app.py
"""

import asyncio

import nest_asyncio
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
import os

nest_asyncio.apply()

load_dotenv()


def _safe_async_run(coro):
    """Safely run async coroutine in Streamlit environment.

    Streamlit maintains its own event loop, so ``asyncio.run()`` may raise
    ``RuntimeError: This event loop is already running``.  We use
    ``nest_asyncio`` (applied at module level) together with
    ``get_event_loop().run_until_complete()`` to avoid the conflict.
    Falls back to ``asyncio.run()`` when no running loop is available.
    """
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)

st.set_page_config(
    page_title="AEGIS CORE — 詐騙預測系統",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from app.dashboard.styles import inject_css
inject_css()

# ── API Gateway 呼叫輔助函數 ──────────────────────────────────────────────────
import requests as _requests

_API_GATEWAY_URL = os.environ.get("API_GATEWAY_URL", "http://localhost:8000")
_API_KEY = os.environ.get("API_KEY", "test-key-001")


def _call_api_gateway(endpoint: str, payload: dict) -> dict:
    """透過 API Gateway 呼叫後端服務（遵守架構分層原則）。"""
    url = f"{_API_GATEWAY_URL.rstrip('/')}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": _API_KEY,
    }
    try:
        resp = _requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except _requests.RequestException as exc:
        return {"error": str(exc)}


# ── LLM 設定（從環境變數讀取）────────────────────────────────────────────────
_provider = os.environ.get("LLM_PROVIDER", "openai").lower()
_fallback = os.environ.get("LLM_FALLBACK", "").lower()
_openai_key = os.environ.get("OPENAI_API_KEY", "")
_google_key = os.environ.get("GOOGLE_API_KEY", "")

_llm_ready = False

# 優先嘗試主要 provider
if _provider == "openai" and _openai_key and _openai_key != "sk-your-openai-api-key-here":
    st.session_state["openai_api_key"] = _openai_key
    st.session_state["llm_provider"] = "openai"
    _llm_ready = True
elif _provider == "google" and _google_key and _google_key != "your-google-api-key-here":
    st.session_state["openai_api_key"] = _google_key
    st.session_state["llm_provider"] = "google"
    _llm_ready = True
elif _provider == "ollama":
    st.session_state["openai_api_key"] = "ollama"
    st.session_state["llm_provider"] = "ollama"
    _llm_ready = True

# 主要 provider 不可用時，fallback 到備案
if not _llm_ready and _fallback == "ollama":
    st.session_state["openai_api_key"] = "ollama"
    st.session_state["llm_provider"] = "ollama"
    _llm_ready = True

# ── 快取管理器 ────────────────────────────────────────────────────────────────
from app.dashboard.page_modules.cache import DashboardCache, format_cache_status

@st.cache_resource
def get_cache() -> DashboardCache:
    return DashboardCache()

cache = get_cache()

# ── 真實資料 ──────────────────────────────────────────────────────────────────
import sys
import os as _os
sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', '..'))
from data.taiwan_scam_data import (
    REAL_HOTWORDS, REAL_SCAM_SCRIPTS, TAIWAN_SCAM_CASES_BY_REGION,
    VICTIM_AGE_DISTRIBUTION, SCAM_TYPE_STATS, MONTHLY_TREND,
    MODEL_PERFORMANCE, ANNUAL_STATS,
)

MOCK_KEYWORD_FREQ = REAL_HOTWORDS

# 風險向量資料（基於 taiwan_scam_data.py 真實案件統計計算）
# 資料來源：內政部警政署 165 反詐騙諮詢專線統計（2023-2024）、刑事警察局詐欺案件統計
# 計算邏輯：綜合案件數佔比（40%）、平均損失佔比（40%）、趨勢權重（±10%）與基礎分（10%）
total_cases = sum(TAIWAN_SCAM_CASES_BY_REGION.values())
max_cases = max(s["cases"] for s in SCAM_TYPE_STATS.values())
max_loss = max(s["avg_loss_ntd"] for s in SCAM_TYPE_STATS.values())
COMPUTED_RISK_VECTORS: list[dict] = []
for scam_type, stats in SCAM_TYPE_STATS.items():
    case_weight = stats["cases"] / max_cases  # 案件數佔比（正規化 0-1）
    loss_weight = stats["avg_loss_ntd"] / max_loss  # 平均損失佔比（正規化 0-1）
    trend_bonus = 0.1 if stats["trend"] == "上升" else -0.05 if stats["trend"] == "下降" else 0
    risk_score = min(0.95, case_weight * 0.4 + loss_weight * 0.4 + trend_bonus + 0.1)
    audience = "中老年族群" if scam_type in ["假冒銀行客服", "假冒政府機關"] else \
               "年輕族群" if scam_type in ["投資詐騙", "購物詐騙"] else "一般民眾"
    top_region = max(TAIWAN_SCAM_CASES_BY_REGION, key=lambda k: TAIWAN_SCAM_CASES_BY_REGION[k])
    COMPUTED_RISK_VECTORS.append({
        "scam_cluster_label": scam_type,
        "risk_score": round(risk_score, 2),
        "target_audience": audience,
        "region": top_region,
        "high_risk_features": [f"{scam_type}話術", f"平均損失 {stats['avg_loss_ntd']//10000} 萬元"],
        "cases_2023": stats["cases"],
        "trend": stats["trend"],
    })


def show_cache_warning(is_from_cache: bool, cached_at) -> None:
    status_msg = format_cache_status(is_from_cache, cached_at)
    if is_from_cache:
        st.warning(status_msg)
    else:
        st.success(status_msg)


# ── 導覽選單定義 ──────────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("", "首頁", "home"),
    ("", "威脅監控", "threat_monitor"),
    ("", "對話模擬器", "simulator"),
    ("", "DNA 圖譜", "dna_map"),
    ("", "進化時間軸", "evolution"),
    ("", "免疫訓練", "training"),
    ("", "LLM 生成", "llm_demo"),
    ("", "XAI 分析", "xai"),
    ("", "熱詞排行", "hotwords"),
    ("", "沙盤推演", "sandbox"),
    ("", "風險地圖", "risk_map"),
    ("", "模型評估", "evaluation"),
]

PAGE_TITLES = {
    "home": ("首頁", ""),
    "threat_monitor": ("即時威脅監控", "模擬 SOC 安全操作中心，即時監控台灣詐騙威脅態勢"),
    "simulator": ("詐騙對話模擬器", "與 AI 扮演的詐騙犯對話，練習識破詐騙手法"),
    "dna_map": ("話術 DNA 圖譜", "各詐騙類型的心理操控特徵分布與相互關聯"),
    "evolution": ("話術進化時間軸", "追蹤詐騙話術從 2021 到 2024 的演化歷程"),
    "training": ("詐騙免疫訓練", "互動式防詐訓練，通過測驗獲得防詐免疫證書"),
    "llm_demo": ("LLM 話術生成", "呼叫 GPT-4o 生成多種變形話術並進行 XAI 分析"),
    "xai": ("XAI 話術分析", "可解釋性 AI 高亮顯示詐騙話術的心理操控特徵"),
    "hotwords": ("熱詞排行榜", "詐騙話術中出現頻率最高的關鍵詞統計"),
    "sandbox": ("沙盤推演", "模擬不同詐騙情境的風險評估與預測"),
    "risk_map": ("受害風險地圖", "依年齡層與地區呈現詐騙受害風險指數"),
    "evaluation": ("模型準確率評估", "AI 模型在各詐騙類型上的分類準確率評估"),
}

# ── 讀取 query params 決定當前頁面 ───────────────────────────────────────────
params = st.query_params
page_key = params.get("page", "home")
valid_keys = {k for _, _, k in NAV_ITEMS}
if page_key not in valid_keys:
    page_key = "home"

# ── LLM 狀態文字 ─────────────────────────────────────────────────────────────
if _llm_ready:
    provider_label = {"ollama": "Ollama", "google": "Gemini", "openai": "OpenAI"}.get(
        st.session_state.get("llm_provider", "openai"), "OpenAI"
    )
    llm_status_html = f'<span style="color:#86efac;font-size:0.72rem;font-weight:600;">● LLM: {provider_label}</span>'
else:
    llm_status_html = '<span style="color:#92400E;font-size:0.72rem;font-weight:600;">未設定 LLM</span>'

# ── 建立導覽選單 HTML ─────────────────────────────────────────────────────────
nav_items_html = ""
for _icon, _label, _key in NAV_ITEMS:
    _is_active = (page_key == _key)
    _active_cls = "nav-active" if _is_active else ""
    nav_items_html += (
        f'<a href="?page={_key}" target="_top" '
        f'class="nav-item {_active_cls}">{_label}</a>'
    )

# ── 讀取 Logo 圖片（base64）──────────────────────────────────────────────────
import base64
import pathlib

_logo_path = pathlib.Path(__file__).parent / "static" / "logo.png"
if _logo_path.exists():
    logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode()
else:
    logo_b64 = ""

# ── 資料新鮮度（提前計算，嵌入 top-bar）──────────────────────────────────────
def get_live_data_manager():
    """取得 CacheManager 單例，供 Dashboard 使用"""
    try:
        from app.live_data import get_cache_manager
        return get_cache_manager()
    except Exception:
        return None

_freshness_text = ""
try:
    from app.dashboard.pages.freshness import render_freshness_indicator

    # 每次頁面載入自動觸發資料擷取
    try:
        from app.live_data import get_fetch_scheduler
        _sched = get_fetch_scheduler()
        _sched.trigger_now()
    except Exception:
        pass

    _live_mgr = get_live_data_manager()
    if _live_mgr is not None:
        _freshness_info = _live_mgr.get_freshness_info()
        _freshness_text = render_freshness_indicator(_freshness_info)
    else:
        _freshness_text = "顯示靜態預設資料（2023-2024）"
except Exception:
    _freshness_text = ""

_freshness_html = f'<div style="color:rgba(255,255,255,0.55);font-size:0.65rem;margin-top:2px;">{_freshness_text}</div>' if _freshness_text else ""

st.markdown(f"""
<style>
.top-bar {{
    background: linear-gradient(135deg, #14532d 0%, #166534 100%);
    padding: 0 32px 0 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 90px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.2);
}}
.top-bar-logo {{
    display: flex;
    align-items: center;
    gap: 0;
    text-decoration: none !important;
    margin-left: 0;
}}
.top-bar-logo img {{
    margin-right: -30px;
}}
.top-bar-logo-text {{
    color: white;
    font-family: 'Orbitron', 'Rajdhani', monospace;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 2.5px;
    line-height: 1.2;
    text-transform: uppercase;
    margin-left: -2px;
}}
.top-bar-logo-sub {{
    color: rgba(255,255,255,0.6);
    font-size: 0.7rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 2px;
}}
.top-bar-right {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.72rem;
    color: rgba(255,255,255,0.7);
}}
.status-dot {{
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #86efac;
    display: inline-block;
    margin-right: 4px;
}}
.nav-bar {{
    background: #166534;
    padding: 0 32px;
    display: flex;
    align-items: stretch;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    overflow-x: auto;
    margin-bottom: 0;
}}
.nav-item {{
    color: rgba(255,255,255,0.85) !important;
    font-size: 0.95rem;
    font-weight: 500;
    padding: 11px 16px;
    text-decoration: none !important;
    white-space: nowrap;
    border-bottom: 2px solid transparent;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
    display: flex;
    align-items: center;
    gap: 5px;
}}
.nav-item:hover {{
    background: rgba(255,255,255,0.1);
    color: white !important;
    text-decoration: none !important;
}}
.nav-active {{
    color: white !important;
    font-weight: 700;
    border-bottom: 2px solid white;
    background: rgba(255,255,255,0.12);
}}
@keyframes soft-glow {{
    0%, 100% {{ opacity: 0.3; transform: scale(0.9); }}
    50% {{ opacity: 0.7; transform: scale(1.1); }}
}}
.main .block-container {{
    padding-top: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-bottom: 1.5rem !important;
    max-width: 100% !important;
}}
section[data-testid="stMain"] > div {{
    padding-top: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}}
</style>
<div class="top-bar">
    <a href="?page=home" target="_top" class="top-bar-logo">
        <div style="position:relative;display:inline-flex;align-items:center;justify-content:center;">
            <div style="position:absolute;width:50px;height:50px;border-radius:50%;
            background:radial-gradient(circle,rgba(91,192,222,0.35) 0%,rgba(91,192,222,0.1) 40%,transparent 70%);
            filter:blur(6px);animation:soft-glow 3s ease-in-out infinite;"></div>
            <img src="data:image/png;base64,{logo_b64}" alt="AEGIS CORE" style="height:100px;width:auto;position:relative;z-index:1;">
        </div>
        <div>
            <div class="top-bar-logo-text">AEGIS CORE</div>
            <div class="top-bar-logo-sub">AI 詐騙進化預測系統</div>
        </div>
    </a>
    <div class="top-bar-right">
        <div style="text-align:right;">
            <div style="display:flex;align-items:center;gap:12px;">
                <span><span class="status-dot"></span>系統運行中</span>
                <span style="color:rgba(255,255,255,0.3);">|</span>
                {llm_status_html}
            </div>
            {_freshness_html}
        </div>
    </div>
</div>
<div class="nav-bar">
    {nav_items_html}
</div>
""", unsafe_allow_html=True)

# ── 麵包屑（非首頁才顯示）────────────────────────────────────────────────────
if page_key != "home":
    _title, _desc = PAGE_TITLES.get(page_key, (page_key, ""))
    st.markdown(f"""
    <div style="background:white;border-bottom:1px solid #E5E7EB;padding:8px 32px;
    font-size:0.8rem;color:#6B7280;display:flex;align-items:center;gap:6px;">
        <a href="?page=home" target="_top" style="color:#166534;text-decoration:none;">首頁</a>
        <span style="color:#D1D5DB;">›</span>
        <span style="color:#374151;font-weight:500;">{_title}</span>
    </div>
    """, unsafe_allow_html=True)

# ── 從 live_data 層取得最新資料（取代直接 import 靜態資料）─────────────────────
def _get_live_data():
    """從 CacheManager 取得最新資料，資料為空時回傳 None（降級至靜態資料）"""
    try:
        mgr = get_live_data_manager()
        if mgr is not None:
            cached = mgr.load()
            if cached is not None and cached.data.scam_type_stats:
                return cached.data
    except Exception:
        pass
    return None

_live = _get_live_data()
if _live is not None and _live.scam_cases_by_region and _live.scam_type_stats:
    # 用 live data 覆蓋靜態資料變數，讓下游頁面無感切換
    SCAM_TYPE_STATS = {k: {"cases": v.cases, "avg_loss_ntd": v.avg_loss_ntd, "trend": v.trend}
                       for k, v in _live.scam_type_stats.items()}
    TAIWAN_SCAM_CASES_BY_REGION = _live.scam_cases_by_region
    VICTIM_AGE_DISTRIBUTION = _live.victim_age_distribution
    MONTHLY_TREND = [{"month": e.month, "cases": e.cases, "amount_billion": e.amount_billion}
                     for e in _live.monthly_trend]
    ANNUAL_STATS = {k: {"total_cases": v.total_cases, "total_loss_billion": v.total_loss_billion}
                    for k, v in _live.annual_stats.items()}
    MOCK_KEYWORD_FREQ = _live.hotwords if _live.hotwords else REAL_HOTWORDS
    if _live.real_scam_scripts:
        REAL_SCAM_SCRIPTS = [s for s in _live.real_scam_scripts if "_model_performance" not in s]
    # 重新計算風險向量
    total_cases = sum(TAIWAN_SCAM_CASES_BY_REGION.values())
    max_cases = max(s["cases"] for s in SCAM_TYPE_STATS.values()) if SCAM_TYPE_STATS else 1
    max_loss = max(s["avg_loss_ntd"] for s in SCAM_TYPE_STATS.values()) if SCAM_TYPE_STATS else 1
    COMPUTED_RISK_VECTORS = []
    for scam_type, stats in SCAM_TYPE_STATS.items():
        case_weight = stats["cases"] / max_cases
        loss_weight = stats["avg_loss_ntd"] / max_loss
        trend_bonus = 0.1 if stats["trend"] == "上升" else -0.05 if stats["trend"] == "下降" else 0
        risk_score = min(0.95, case_weight * 0.4 + loss_weight * 0.4 + trend_bonus + 0.1)
        audience = "中老年族群" if scam_type in ["假冒銀行客服", "假冒政府機關"] else \
                   "年輕族群" if scam_type in ["投資詐騙", "購物詐騙"] else "一般民眾"
        top_region = max(TAIWAN_SCAM_CASES_BY_REGION, key=lambda k: TAIWAN_SCAM_CASES_BY_REGION[k])
        COMPUTED_RISK_VECTORS.append({
            "scam_cluster_label": scam_type,
            "risk_score": round(risk_score, 2),
            "target_audience": audience,
            "region": top_region,
            "high_risk_features": [f"{scam_type}話術", f"平均損失 {stats['avg_loss_ntd']//10000} 萬元"],
            "cases_2023": stats["cases"],
            "trend": stats["trend"],
        })

# ── 動態計算最新年度統計（取代寫死的數據）────────────────────────────────────
def _compute_latest_stats():
    """從 ANNUAL_STATS 動態取得最新年度的統計，支援部分年度（Q1 等）"""
    from datetime import datetime as _dt
    current_year = _dt.now().year
    current_month = _dt.now().month
    numeric_years = sorted([k for k in ANNUAL_STATS if isinstance(k, (int, str)) and str(k).isdigit()], key=lambda x: int(x))
    if not numeric_years:
        return "N/A", 0, 0.0, "", "", ""

    latest_year = str(numeric_years[-1])
    latest = ANNUAL_STATS[numeric_years[-1]]
    total_cases = latest["total_cases"]
    total_loss = latest["total_loss_billion"]

    # 判斷是否為當年度部分資料（尚未結束的年份）
    is_partial = int(latest_year) == current_year
    year_label = f"{latest_year} Q1" if is_partial and current_month <= 4 else latest_year
    period_suffix = "（截至目前）" if is_partial else ""

    # 與前一年同期或全年比較
    prev_year = str(numeric_years[-2]) if len(numeric_years) >= 2 else None
    if prev_year:
        prev = ANNUAL_STATS[numeric_years[-2]]
        if is_partial:
            # 部分年度：與前一年全年比較，標註為累計
            case_delta_str = f"累計 vs {prev_year}全年 {prev['total_cases']:,}"
            loss_delta_str = f"累計 vs {prev_year}全年 {prev['total_loss_billion']}億"
        else:
            case_delta = (total_cases - prev["total_cases"]) / prev["total_cases"] * 100
            loss_delta = (total_loss - prev["total_loss_billion"]) / prev["total_loss_billion"] * 100
            case_delta_str = f"↑ {case_delta:.0f}% vs {prev_year}" if case_delta > 0 else f"↓ {abs(case_delta):.0f}% vs {prev_year}"
            loss_delta_str = f"↑ {loss_delta:.0f}% vs {prev_year}" if loss_delta > 0 else f"↓ {abs(loss_delta):.0f}% vs {prev_year}"
    else:
        case_delta_str = ""
        loss_delta_str = ""

    return year_label, total_cases, total_loss, case_delta_str, loss_delta_str, period_suffix

_latest_year, _total_cases, _total_loss, _case_delta, _loss_delta, _period_suffix = _compute_latest_stats()

# ══════════════════════════════════════════════════════════════════════════════
# 首頁：介紹頁面
# ══════════════════════════════════════════════════════════════════════════════
if page_key == "home":
    import pandas as pd

    # Hero 區塊
    st.markdown("""
    <div class="hero-section fade-in">
        <div style="overflow:hidden;white-space:nowrap;width:100%;">
            <div style="display:inline-block;animation:marquee 20s linear infinite;
            color:#1a2332;font-size:0.85rem;letter-spacing:1px;">
                系統提醒：預測結果僅供參考。詐騙手法日新月異，AI 技術雖能提升防禦力，但您的警覺心仍是最後一道關鍵防線。若遇到疑似詐騙情境，請務必秉持「不聽、不信、不點擊」原則，並即刻撥打 165 反詐騙專線求證。 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                系統提醒：預測結果僅供參考。詐騙手法日新月異，AI 技術雖能提升防禦力，但您的警覺心仍是最後一道關鍵防線。若遇到疑似詐騙情境，請務必秉持「不聽、不信、不點擊」原則，並即刻撥打 165 反詐騙專線求證。 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            </div>
        </div>
    </div>
    <style>
    @keyframes marquee {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 統計數字
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"{_latest_year} 年詐騙案件", f"{_total_cases:,} 件", _case_delta)
    col2.metric("年度損失金額", f"{_total_loss} 億元", _loss_delta)
    col3.metric("XAI 分類準確率", f"{MODEL_PERFORMANCE['accuracy']:.1%}", "↑ 規則式基準")
    col4.metric("預警提前時間", "24 小時", "↓ 傳統需 14 天")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 系統功能")

    # 功能卡片 — 用單一 CSS Grid 確保同排等高
    st.markdown("""
    <style>
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
    </style>
    <div class="feature-grid fade-in">
        <div class="feature-card">
            <div class="feature-card-title">LLM 話術裂變生成</div>
            <div class="feature-card-desc">GPT-4o / Gemini / Llama 驅動，從種子情境自動生成數百種詐騙變種話術</div>
        </div>
        <div class="feature-card">
            <div class="feature-card-title">XAI 可解釋性分析</div>
            <div class="feature-card-desc">高亮顯示觸發心理操控特徵的具體片段，非黑盒子，每個判斷都有依據</div>
        </div>
        <div class="feature-card">
            <div class="feature-card-title">免疫訓練平台</div>
            <div class="feature-card-desc">互動式防詐訓練，體驗真實詐騙話術，通過測驗獲得防詐免疫證書</div>
        </div>
        <div class="feature-card">
            <div class="feature-card-title">異常偵測預警</div>
            <div class="feature-card-desc">Isolation Forest 時間序列分析，24 小時內偵測新興詐騙手法趨勢</div>
        </div>
        <div class="feature-card">
            <div class="feature-card-title">受害風險地圖</div>
            <div class="feature-card-desc">依年齡層與地區呈現風險指數，精準定位高風險族群與地區</div>
        </div>
        <div class="feature-card">
            <div class="feature-card-title">Risk Vector API</div>
            <div class="feature-card-desc">標準化風險向量 API，可串接銀行、電信商、保險公司即時防詐系統</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 台灣詐騙現況（資料來源：警政署 165 專線）")

    scam_df = pd.DataFrame([
        {"詐騙類型": k, f"{_latest_year}年案件數": f"{v['cases']:,}", "平均損失": f"NT${v['avg_loss_ntd']//10000}萬", "趨勢": v['trend']}
        for k, v in sorted(SCAM_TYPE_STATS.items(), key=lambda x: x[1]['cases'], reverse=True)
    ])
    st.dataframe(scam_df, use_container_width=True, hide_index=True)

    st.markdown("""
    <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;
    padding:20px;text-align:center;margin-top:24px;">
        <div style="color:#166534;font-size:0.8rem;letter-spacing:1px;text-transform:uppercase;font-weight:600;">
        AEGIS CORE 的使命</div>
        <div style="color:#374151;font-size:1rem;margin-top:8px;line-height:1.6;">
        透過 AI 逆向模擬詐騙邏輯，提前佈署防護機制
        </div>
        <div style="color:#6B7280;font-size:0.82rem;margin-top:8px;">
        情境種子 → LLM 裂變 → NLP 萃取 → XAI 高亮 → 異常偵測 → Risk Vector → API 串接金融機構
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 頁面 0：系統總覽
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "overview":
    st.markdown("""
    <div class="fade-in" style="text-align:center;padding:20px 0 10px;">
        <div style="font-size:1rem;color:#4B5563;letter-spacing:3px;text-transform:uppercase;margin-bottom:8px;">
        AI-POWERED ANTI-SCAM INTELLIGENCE</div>
        <h1 style="font-size:3rem;margin:0;">AEGIS CORE</h1>
        <p style="color:#374151;font-size:1.1rem;margin-top:8px;">
        從被動防禦到主動預測 — 運用生成式 AI 構築下一代防詐護城河</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"{_latest_year} 年詐騙案件", f"{_total_cases:,} 件", _case_delta)
    col2.metric("年度損失金額", f"{_total_loss} 億元", _loss_delta)
    col3.metric("XAI 分類準確率", f"{MODEL_PERFORMANCE['accuracy']:.1%}", "↑ 規則式基準")
    col4.metric("預警提前時間", "24 小時", "↓ 傳統需 14 天")

    st.markdown("---")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("""
        <div class="cyber-card fade-in">
            <div style="font-size:1.5rem;margin-bottom:8px;"></div>
            <div style="font-weight:600;color:#166534;margin-bottom:6px;">LLM 話術裂變生成</div>
            <div style="color:#374151;font-size:0.9rem;">GPT-4o / Gemini / Llama 驅動，從種子情境自動生成數百種詐騙變種話術</div>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown("""
        <div class="cyber-card fade-in">
            <div style="font-size:1.5rem;margin-bottom:8px;"></div>
            <div style="font-weight:600;color:#166534;margin-bottom:6px;">XAI 可解釋性分析</div>
            <div style="color:#374151;font-size:0.9rem;">高亮顯示觸發心理操控特徵的具體片段，非黑盒子，每個判斷都有依據</div>
        </div>
        """, unsafe_allow_html=True)
    with col_c:
        st.markdown("""
        <div class="cyber-card fade-in">
            <div style="font-size:1.5rem;margin-bottom:8px;"></div>
            <div style="font-weight:600;color:#166534;margin-bottom:6px;">免疫訓練平台</div>
            <div style="color:#374151;font-size:0.9rem;">互動式防詐訓練，體驗真實詐騙話術，通過測驗獲得防詐免疫證書</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_d, col_e, col_f = st.columns(3)
    with col_d:
        st.markdown("""
        <div class="cyber-card fade-in">
            <div style="font-size:1.5rem;margin-bottom:8px;"></div>
            <div style="font-weight:600;color:#1D4ED8;margin-bottom:6px;">異常偵測預警</div>
            <div style="color:#374151;font-size:0.9rem;">Isolation Forest 時間序列分析，24 小時內偵測新興詐騙手法趨勢</div>
        </div>
        """, unsafe_allow_html=True)
    with col_e:
        st.markdown("""
        <div class="cyber-card fade-in">
            <div style="font-size:1.5rem;margin-bottom:8px;"></div>
            <div style="font-weight:600;color:#1D4ED8;margin-bottom:6px;">受害風險地圖</div>
            <div style="color:#374151;font-size:0.9rem;">依年齡層與地區呈現風險指數，精準定位高風險族群與地區</div>
        </div>
        """, unsafe_allow_html=True)
    with col_f:
        st.markdown("""
        <div class="cyber-card fade-in">
            <div style="font-size:1.5rem;margin-bottom:8px;"></div>
            <div style="font-weight:600;color:#1D4ED8;margin-bottom:6px;">Risk Vector API</div>
            <div style="color:#374151;font-size:0.9rem;">標準化風險向量 API，可串接銀行、電信商、保險公司即時防詐系統</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center;padding:10px 0;">
        <div style="color:#4B5563;font-size:0.85rem;letter-spacing:1px;">
        SYSTEM PIPELINE
        </div>
        <div style="color:#374151;margin-top:12px;font-size:0.95rem;">
        情境種子輸入 → LLM 話術裂變 → NLP 特徵萃取 → XAI 可解釋高亮 → 異常偵測預警 → Risk Vector 輸出 → API 串接金融機構
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 真實數據展示 ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("台灣詐騙現況（資料來源：警政署 165 專線）")
    import pandas as pd
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric(f"{_latest_year} 年總案件數", f"{_total_cases:,} 件", _case_delta)
    col_s2.metric(f"{_latest_year} 年總損失", f"{_total_loss} 億元", _loss_delta)
    col_s3.metric("2024 上半年損失", "62.1 億元", "↑ 持續攀升")

    # 詐騙類型排行
    scam_df = pd.DataFrame([
        {"詐騙類型": k, f"{_latest_year}年案件數": f"{v['cases']:,}", "平均損失": f"NT${v['avg_loss_ntd']//10000}萬", "趨勢": v['trend']}
        for k, v in sorted(SCAM_TYPE_STATS.items(), key=lambda x: x[1]['cases'], reverse=True)
    ])
    st.dataframe(scam_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("""
    <div style="background:#FEF2F2;border:1px solid #FECACA;
    border-radius:10px;padding:16px;text-align:center;">
        <div style="color:#991B1B;font-size:0.85rem;letter-spacing:1px;text-transform:uppercase;">
        AEGIS CORE 的使命</div>
        <div style="color:#1a2332;font-size:1rem;margin-top:8px;">
        透過 AI 逆向模擬詐騙邏輯，提前佈署防護機制
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 頁面 LLM：真實 LLM 話術生成 Demo
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "llm_demo":
    st.title("LLM 話術生成 Demo")
    st.markdown("輸入基礎詐騙情境，呼叫 LLM 生成多種變形話術，並即時進行 XAI 分析。")

    import json
    from app.pattern_analyzer.xai_highlighter import XAIHighlighter

    TAG_COLORS = {
        "信任建立": "#d4edda", "緊迫感製造": "#fff3cd",
        "情緒勒索": "#f8d7da", "權威偽裝": "#cce5ff", "利益誘導": "#e2d9f3",
    }
    TAG_TEXT_COLORS = {
        "信任建立": "#155724", "緊迫感製造": "#856404",
        "情緒勒索": "#721c24", "權威偽裝": "#004085", "利益誘導": "#4a235a",
    }

    has_api_key = bool(st.session_state.get("openai_api_key"))
    _current_provider = st.session_state.get("llm_provider", "openai")
    if not has_api_key:
        st.warning("未偵測到 LLM 設定，將使用示範資料。請在 .env 設定 LLM_PROVIDER。")

    with st.form("llm_form"):
        col1, col2 = st.columns(2)
        with col1:
            scenario = st.text_area(
                "詐騙情境描述",
                value="假冒銀行客服，聲稱帳戶出現異常交易",
                height=100,
            )
            audience = st.selectbox(
                "目標受眾",
                ["中老年族群", "年輕族群", "學生族群", "商業人士", "一般民眾"],
            )
        with col2:
            sample_count = st.slider("生成樣本數量", min_value=3, max_value=10, value=5)
            show_xai = st.checkbox("同時執行 XAI 分析", value=True)

        submitted = st.form_submit_button("生成話術", type="primary")

    if submitted:
        if has_api_key:
            # 真實 LLM 呼叫
            with st.spinner(f"正在呼叫 {_current_provider.capitalize()} 生成話術..."):
                try:
                    import os
                    if _current_provider != "ollama":
                        os.environ["OPENAI_API_KEY"] = st.session_state["openai_api_key"]

                    from app.scam_engine.generator import generate_scam_samples
                    result = _safe_async_run(generate_scam_samples(
                        scenario=scenario,
                        target_audience=audience,
                        min_samples=sample_count,
                    ))

                    if "error_code" in result:
                        st.error(f"LLM 呼叫失敗：{result.get('description', '未知錯誤')}")
                        samples = []
                    else:
                        samples = result.get("samples", [])
                        st.success(f"成功生成 {len(samples)} 個話術樣本（{_current_provider.capitalize()} 輸出）")
                except Exception as e:
                    st.error(f"呼叫失敗：{e}")
                    samples = []
        else:
            # Mock 示範資料
            samples = [
                {
                    "content": f"您好，我是{scenario[:8]}的客服專員，您的帳戶出現異常，請立即配合處理，否則將在24小時內凍結。",
                    "psychological_tags": ["權威偽裝", "緊迫感製造"],
                    "target_audience": audience,
                },
                {
                    "content": f"親愛的客戶，為了保護您的資金安全，我們的專業團隊需要您立即提供驗證碼，這是最後的機會。",
                    "psychological_tags": ["信任建立", "緊迫感製造"],
                    "target_audience": audience,
                },
                {
                    "content": f"您的帳戶涉及一起重大詐騙案件，警方正在調查，請立即配合轉帳至安全帳戶，否則您將面臨法律責任。",
                    "psychological_tags": ["權威偽裝", "情緒勒索"],
                    "target_audience": audience,
                },
            ]
            st.info("使用示範資料（請設定 API Key 以啟用真實生成）")

        if samples:
            st.markdown("---")
            highlighter = XAIHighlighter()

            for i, sample in enumerate(samples, 1):
                with st.expander(f"樣本 {i}：{', '.join(sample.get('psychological_tags', []))}", expanded=(i == 1)):
                    content = sample.get("content", "")

                    if show_xai and content:
                        xai_result = highlighter.highlight(content)
                        # 高亮顯示
                        html_parts = []
                        prev_end = 0
                        for span in xai_result.spans:
                            if span.start > prev_end:
                                html_parts.append(content[prev_end:span.start])
                            bg = TAG_COLORS.get(span.tag, "#eee")
                            fg = TAG_TEXT_COLORS.get(span.tag, "#333")
                            html_parts.append(
                                f'<mark style="background:{bg};color:{fg};padding:2px 4px;'
                                f'border-radius:3px;font-weight:bold;" title="{span.tag}">'
                                f'{span.text}</mark>'
                            )
                            prev_end = span.end
                        if prev_end < len(content):
                            html_parts.append(content[prev_end:])
                        st.markdown(
                            f'<div style="line-height:2;padding:10px;border:1px solid #dee2e6;'
                            f'border-radius:6px;background:#fafafa;">{"".join(html_parts)}</div>',
                            unsafe_allow_html=True,
                        )
                        tags_str = " ".join(
                            f'<span style="background:{TAG_COLORS.get(t,"#eee")};'
                            f'color:{TAG_TEXT_COLORS.get(t,"#333")};padding:3px 8px;'
                            f'border-radius:10px;margin:2px;font-size:0.85rem;">{t}</span>'
                            for t in xai_result.triggered_tags
                        )
                        st.markdown(f"**心理特徵：** {tags_str}", unsafe_allow_html=True)
                    else:
                        st.write(content)
                        tags = sample.get("psychological_tags", [])
                        if tags:
                            st.markdown(f"**心理特徵：** {', '.join(tags)}")


# ══════════════════════════════════════════════════════════════════════════════
# 頁面：即時威脅監控
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "threat_monitor":
    import time
    import pandas as pd
    from app.dashboard.page_modules.threat_monitor import (
        get_current_threat_summary, generate_live_alerts, THREAT_LEVELS, EVOLUTION_TIMELINE
    )

    st.title("即時威脅監控中心")
    st.markdown("模擬 SOC 安全操作中心，即時監控台灣詐騙威脅態勢。")

    summary = get_current_threat_summary(
        scam_type_stats=SCAM_TYPE_STATS,
        monthly_trend=MONTHLY_TREND,
        cases_by_region=TAIWAN_SCAM_CASES_BY_REGION,
    )
    level_info = THREAT_LEVELS[summary["overall_level"]]

    # 威脅等級橫幅
    st.markdown(f"""
    <div style="background:#FEF2F2;border:2px solid {level_info['color']};
    border-radius:12px;padding:16px;text-align:center;margin-bottom:20px;
    animation:pulse-glow 2s infinite;" class="alert-pulse">
        <div style="font-size:2rem;">{level_info['icon']}</div>
        <div style="font-size:1.3rem;font-weight:700;color:{level_info['color']};">
        當前威脅等級：{level_info['label']}</div>
        <div style="color:#374151;font-size:0.85rem;">最後更新：{summary['last_updated']}</div>
    </div>
    """, unsafe_allow_html=True)

    # 即時統計
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("活躍威脅數", summary["active_threats"], "↑ 較昨日")
    c2.metric("24h 新變種", summary["new_variants_24h"], "↑ 持續增加")
    c3.metric("今日偵測案件", summary["total_cases_today"], "↑ 上升趨勢")
    c4.metric("AI 詐騙佔比", f"{summary['ai_scam_ratio']:.0%}", "↑ 快速增長")

    st.markdown("---")

    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.subheader("即時預警事件串流")
        if st.button("刷新事件", key="refresh_alerts"):
            st.rerun()

        alerts = generate_live_alerts(
            10,
            scam_type_stats=SCAM_TYPE_STATS,
            cases_by_region=TAIWAN_SCAM_CASES_BY_REGION,
        )
        for alert in alerts:
            lvl = THREAT_LEVELS[alert["level"]]
            st.markdown(f"""
            <div style="background:white;border-left:3px solid {lvl['color']};
            padding:10px 14px;margin:6px 0;border-radius:0 8px 8px 0;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="color:{lvl['color']};font-weight:600;font-size:0.85rem;">
                    {lvl['icon']} {alert['level']} | {alert['id']}</span>
                    <span style="color:#4B5563;font-size:0.8rem;">{alert['time']}</span>
                </div>
                <div style="color:#1a2332;font-size:0.9rem;margin-top:4px;">{alert['tactic']}</div>
                <div style="color:#374151;font-size:0.8rem;margin-top:2px;">
                {alert['scam_type']} | {alert['region']} | 偵測 {alert['cases_detected']} 件 | 風險分數 {alert['risk_score']}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_r:
        st.subheader("威脅分布")
        threat_df = pd.DataFrame([
            {"類型": k, "案件數": v["cases"], "趨勢": v["trend"]}
            for k, v in sorted(SCAM_TYPE_STATS.items(), key=lambda x: x[1]["cases"], reverse=True)
        ])
        st.bar_chart(threat_df.set_index("類型")["案件數"])

        st.subheader("高風險地區 TOP 5")
        top5 = sorted(TAIWAN_SCAM_CASES_BY_REGION.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (region, cases) in enumerate(top5, 1):
            pct = cases / sum(TAIWAN_SCAM_CASES_BY_REGION.values())
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:6px 0;
            border-bottom:1px solid #E5E7EB;">
                <span style="color:#1a2332;">#{i} {region}</span>
                <span style="color:#166534;font-weight:600;">{cases:,} 件 ({pct:.1%})</span>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 頁面：詐騙對話模擬器
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "simulator":
    from app.dashboard.page_modules.scam_simulator import (
        SIMULATOR_SCENARIOS, SimulatorSession,
        build_simulator_prompt, analyze_user_response, SCAM_BUSTING_TIPS
    )
    from app.pattern_analyzer.xai_highlighter import XAIHighlighter

    TAG_COLORS = {
        "信任建立": "#d4edda", "緊迫感製造": "#fff3cd",
        "情緒勒索": "#f8d7da", "權威偽裝": "#cce5ff", "利益誘導": "#e2d9f3",
    }
    TAG_TEXT_COLORS = {
        "信任建立": "#155724", "緊迫感製造": "#856404",
        "情緒勒索": "#721c24", "權威偽裝": "#004085", "利益誘導": "#4a235a",
    }

    st.title("詐騙對話模擬器")
    st.markdown("與 AI 扮演的詐騙犯進行真實對話，系統即時標記每句話的操控手法。練習識破詐騙！")

    # 初始化 session
    if "sim_session" not in st.session_state:
        st.session_state["sim_session"] = None

    sim: SimulatorSession | None = st.session_state["sim_session"]

    if sim is None or sim.is_ended:
        # 設定畫面
        st.subheader("選擇詐騙情境")
        scenario = st.selectbox("詐騙類型", list(SIMULATOR_SCENARIOS.keys()))
        info = SIMULATOR_SCENARIOS[scenario]

        st.markdown(f"""
        <div class="cyber-card">
            <div style="color:#166534;font-weight:600;margin-bottom:8px;">詐騙犯角色</div>
            <div style="color:#1a2332;">{info['scammer_persona']}</div>
            <div style="color:#374151;font-size:0.85rem;margin-top:8px;">目標：{info['goal']}</div>
            <div style="color:#92400E;font-size:0.85rem;margin-top:4px;">難度：{info['difficulty']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**提示：** 嘗試識破詐騙！說出你的懷疑、要求掛斷電話、或說要報警。")

        has_llm = bool(st.session_state.get("openai_api_key"))
        if not has_llm:
            st.warning("未設定 LLM API Key，對話模擬器需要 LLM 才能運作。請先設定 API Key。")

        if st.button("開始模擬", type="primary", disabled=not has_llm):
            new_sim = SimulatorSession(scenario=scenario)
            opening = info["opening"].replace("{name}", "您")
            new_sim.add_message("assistant", opening)
            st.session_state["sim_session"] = new_sim
            st.rerun()

    else:
        # 對話畫面
        info = sim.scenario_info
        highlighter = XAIHighlighter()

        # 頂部狀態列
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("對話輪次", sim.turn_count)
        col_s2.metric("識破分數", sim.user_resistance_score)
        col_s3.metric("詐騙犯", info.get("scammer_persona", "")[:10] + "...")

        st.markdown("---")

        # 對話記錄
        st.subheader("對話記錄")
        for msg in sim.messages:
            if msg["role"] == "assistant":
                # 詐騙犯的話 - XAI 高亮
                xai = highlighter.highlight(msg["content"])
                if xai.spans:
                    html_parts = []
                    prev_end = 0
                    for span in xai.spans:
                        if span.start > prev_end:
                            html_parts.append(msg["content"][prev_end:span.start])
                        bg = TAG_COLORS.get(span.tag, "#eee")
                        fg = TAG_TEXT_COLORS.get(span.tag, "#333")
                        html_parts.append(
                            f'<mark style="background:{bg};color:{fg};padding:1px 3px;'
                            f'border-radius:3px;font-weight:bold;" title="{span.tag}">'
                            f'{span.text}</mark>'
                        )
                        prev_end = span.end
                    if prev_end < len(msg["content"]):
                        html_parts.append(msg["content"][prev_end:])
                    content_html = "".join(html_parts)
                else:
                    content_html = msg["content"]

                tags_html = " ".join(
                    f'<span style="background:{TAG_COLORS.get(t,"#eee")};color:{TAG_TEXT_COLORS.get(t,"#333")};'
                    f'padding:2px 6px;border-radius:10px;font-size:0.75rem;">{t}</span>'
                    for t in xai.triggered_tags
                ) if xai.triggered_tags else ""

                st.markdown(f"""
                <div style="background:#FEF2F2;border:1px solid #FECACA;
                border-radius:10px;padding:12px;margin:8px 0;">
                    <div style="color:#991B1B;font-size:0.8rem;margin-bottom:6px;">
                    {info.get('scammer_persona','詐騙犯')}</div>
                    <div style="color:#1a2332;line-height:1.7;">{content_html}</div>
                    {f'<div style="margin-top:8px;">{tags_html}</div>' if tags_html else ''}
                </div>
                """, unsafe_allow_html=True)

            else:
                st.markdown(f"""
                <div style="background:#F0FDF4;border:1px solid #BBF7D0;
                border-radius:10px;padding:12px;margin:8px 0;text-align:right;">
                    <div style="color:#1D4ED8;font-size:0.8rem;margin-bottom:6px;">你</div>
                    <div style="color:#1a2332;">{msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)

        # 輸入區
        if not sim.is_ended:
            st.markdown("---")
            user_input = st.text_input(
                "你的回應",
                placeholder="輸入你的回應...",
                key=f"sim_input_{sim.turn_count}",
            )

            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                send = st.button("發送", type="primary", use_container_width=True)
            with col_btn2:
                if st.button("結束", use_container_width=True):
                    sim.is_ended = True
                    sim.end_reason = "escaped"
                    st.rerun()

            if send and user_input.strip():
                sim.add_message("user", user_input)

                # 分析用戶回應
                analysis = analyze_user_response(user_input, sim.scenario)
                if analysis["is_resisting"]:
                    sim.user_resistance_score += analysis["resistance_score"]

                # 呼叫 LLM 生成詐騙犯回應
                has_llm = bool(st.session_state.get("openai_api_key"))
                if has_llm and sim.turn_count < 8:
                    try:
                        messages = build_simulator_prompt(sim.scenario, sim.messages)
                        # 透過 API Gateway 呼叫 LLM 服務（遵守架構分層原則）
                        last_user_msg = next(
                            (m["content"] for m in reversed(sim.messages) if m["role"] == "user"),
                            "",
                        )
                        api_payload = {
                            "scenario": sim.scenario,
                            "target_audience": "一般民眾",
                            "sample_count": 10,
                        }
                        api_result = _call_api_gateway(
                            "/v1/scam/generate",
                            api_payload,
                        )
                        if "error" in api_result:
                            sim.add_message("assistant", f"（API 呼叫失敗：{api_result['error']}，請確認 API Gateway 是否啟動）")
                        else:
                            sim.add_message("assistant", f"（系統已透過 API Gateway 生成回應，任務 ID：{api_result.get('task_id', 'N/A')}）")
                    except Exception as e:
                        sim.add_message("assistant", "（系統錯誤，請重試）")
                elif sim.turn_count >= 8:
                    sim.is_ended = True
                    sim.end_reason = "escaped" if sim.user_resistance_score >= 3 else "caught"

                st.rerun()

        else:
            # 結束畫面
            st.markdown("---")
            if sim.end_reason == "escaped" or sim.user_resistance_score >= 3:
                st.success(f"恭喜！你成功識破了詐騙！識破分數：{sim.user_resistance_score}")
                st.balloons()
            else:
                st.error("這次被詐騙犯牽著走了，下次要更謹慎！")

            tips = SCAM_BUSTING_TIPS.get(sim.scenario, [])
            if tips:
                st.subheader("防詐重點提醒")
                for tip in tips:
                    st.markdown(f"- {tip}")

            if st.button("再試一次", type="primary"):
                st.session_state["sim_session"] = None
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# 頁面：話術 DNA 圖譜
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "dna_map":
    import pandas as pd
    from app.dashboard.page_modules.dna_map import (
        build_similarity_matrix, get_bubble_positions,
        get_top_similar_pairs, SCAM_TYPE_VECTORS, SCAM_TYPE_KEYWORDS,
        SCAM_DANGER_LEVEL, SCAM_CASE_COUNT
    )

    st.title("詐騙話術 DNA 圖譜")
    st.markdown("各詐騙類型的心理操控特徵分布與相互關聯，揭示詐騙話術的「基因結構」。")

    # 心理特徵雷達圖
    st.subheader("心理操控特徵分布矩陣")
    st.caption("各詐騙類型在五大心理操控維度上的強度（0=無，1=極強）")

    dims = ["信任建立", "緊迫感製造", "情緒勒索", "權威偽裝", "利益誘導"]
    matrix_data = []
    for scam_type, vec in SCAM_TYPE_VECTORS.items():
        row = {"詐騙類型": scam_type}
        for dim, val in zip(dims, vec):
            row[dim] = val
        matrix_data.append(row)

    df_matrix = pd.DataFrame(matrix_data).set_index("詐騙類型")
    st.dataframe(
        df_matrix.style.background_gradient(cmap="RdYlGn", axis=None).format("{:.1f}"),
        use_container_width=True,
    )

    st.markdown("---")

    # 相似度分析
    col_sim1, col_sim2 = st.columns(2)

    with col_sim1:
        st.subheader("話術相似度 TOP 5")
        st.caption("相似度高代表這兩種詐騙使用相似的心理操控手法")
        pairs = get_top_similar_pairs(5)
        for pair in pairs:
            pct = int(pair["similarity"] * 100)
            st.markdown(f"""
            <div style="padding:8px 0;border-bottom:1px solid #E5E7EB;">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                    <span style="color:#1a2332;font-size:0.9rem;">
                    {pair['type1']} ↔ {pair['type2']}</span>
                    <span style="color:#166534;font-weight:600;">{pct}%</span>
                </div>
                <div style="background:#E5E7EB;border-radius:4px;height:6px;">
                    <div style="background:linear-gradient(90deg,#00d4ff,#7c3aed);
                    width:{pct}%;height:100%;border-radius:4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_sim2:
        st.subheader("危險等級排行")
        st.caption("基於案件數量、平均損失與心理操控強度綜合評分")
        sorted_danger = sorted(SCAM_DANGER_LEVEL.items(), key=lambda x: x[1], reverse=True)
        for scam_type, danger in sorted_danger:
            color = "#ff4757" if danger >= 8.5 else "#ff6b35" if danger >= 7.5 else "#ffd32a"
            st.markdown(f"""
            <div style="padding:8px 0;border-bottom:1px solid #E5E7EB;">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                    <span style="color:#1a2332;font-size:0.9rem;">{scam_type}</span>
                    <span style="color:{color};font-weight:700;">{danger}/10</span>
                </div>
                <div style="background:#E5E7EB;border-radius:4px;height:6px;">
                    <div style="background:{color};width:{danger*10}%;height:100%;border-radius:4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 各類型關鍵詞
    st.subheader("各類型核心話術關鍵詞")

    # 用 CSS Grid 確保等高對齊
    cards_html = ""
    for scam_type, keywords in SCAM_TYPE_KEYWORDS.items():
        kw_html = " ".join(
            '<span style="background:#F0FDF4;color:#166534;border:1px solid #BBF7D0;'
            'padding:3px 8px;border-radius:10px;font-size:0.8rem;margin:2px;'
            'display:inline-block;">' + kw + '</span>'
            for kw in keywords
        )
        cards_html += (
            '<div style="background:white;border:1px solid #E5E7EB;border-radius:12px;'
            'padding:20px;display:flex;flex-direction:column;justify-content:space-between;">'
            '<div>'
            '<div style="font-weight:700;color:#1a2332;margin-bottom:10px;font-size:0.95rem;">'
            + scam_type + '</div>'
            '<div style="margin-bottom:10px;">' + kw_html + '</div>'
            '</div>'
            '<div style="color:#4B5563;font-size:0.8rem;margin-top:auto;">'
            f'{_latest_year}年案件：<strong>' + f"{SCAM_CASE_COUNT[scam_type]:,}" + '</strong> 件</div>'
            '</div>'
        )

    grid_html = (
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);grid-auto-rows:1fr;gap:12px;">'
        + cards_html
        + '</div>'
    )
    st.markdown(grid_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 頁面：話術進化時間軸
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "evolution":
    import pandas as pd
    from app.dashboard.page_modules.threat_monitor import EVOLUTION_TIMELINE

    st.title("詐騙話術進化時間軸")
    st.markdown("追蹤詐騙話術從 2021 到 2024 的演化歷程，揭示詐騙犯如何隨技術進步升級手法。")

    scam_type = st.selectbox("選擇詐騙類型", list(EVOLUTION_TIMELINE.keys()))
    timeline = EVOLUTION_TIMELINE[scam_type]

    st.markdown("---")

    # 損失趨勢圖
    df_trend = pd.DataFrame([
        {"年份": str(t["year"]), "平均損失（元）": t["avg_loss"], "案件數": t["cases"]}
        for t in timeline
    ]).set_index("年份")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.subheader("平均損失趨勢")
        st.line_chart(df_trend["平均損失（元）"])
    with col_t2:
        st.subheader("案件數趨勢")
        st.line_chart(df_trend["案件數"])

    st.markdown("---")
    st.subheader("話術演化歷程")

    for i, event in enumerate(timeline):
        year = event["year"]
        is_latest = (i == len(timeline) - 1)
        border_color = "#DC2626" if is_latest else "#166534"
        badge = "最新手法" if is_latest else f"第 {i+1} 代"

        kw_html = " ".join(
            f'<span style="background:#F0FDF4;color:#166534;border:1px solid #BBF7D0;'
            f'padding:2px 8px;border-radius:10px;font-size:0.8rem;font-weight:500;">{kw}</span>'
            for kw in event["keywords"]
        )

        st.markdown(f"""
        <div style="border-left:3px solid {border_color};padding:16px 20px;margin:12px 0;
        background:white;border-radius:0 10px 10px 0;border:1px solid #E5E7EB;border-left:3px solid {border_color};">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
                <span style="background:{border_color};color:white;padding:4px 12px;
                border-radius:20px;font-weight:700;font-size:0.9rem;">{year}</span>
                <span style="color:#374151;font-size:0.85rem;font-weight:500;">{badge}</span>
            </div>
            <div style="font-size:1.05rem;font-weight:700;color:#1a2332;margin-bottom:8px;">
            {event['method']}</div>
            <div style="margin-bottom:10px;">{kw_html}</div>
            <div style="background:#FEF2F2;border:1px solid #FECACA;
            border-radius:8px;padding:10px;margin-bottom:8px;">
                <span style="color:#991B1B;font-size:0.85rem;font-weight:600;">新手法：</span>
                <span style="color:#374151;font-size:0.9rem;">{event['new_tactic']}</span>
            </div>
            <div style="display:flex;gap:20px;">
                <span style="color:#374151;font-size:0.85rem;">
                平均損失：<strong style="color:#DC2626;">NT$ {event['avg_loss']:,}</strong></span>
                <span style="color:#374151;font-size:0.85rem;">
                案件數：<strong style="color:#166534;">{event['cases']:,} 件</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div style="background:#FEF2F2;border:1px solid #FECACA;
    border-radius:10px;padding:16px;">
        <div style="color:#991B1B;font-weight:700;margin-bottom:8px;">AEGIS CORE 預測：2025 年趨勢</div>
        <div style="color:#374151;">
        基於話術演化模式，預測 2025 年將出現更多 <strong style="color:#DC2626;">AI 深偽 + 即時語音合成</strong> 的複合型詐騙，
        結合個人資料洩露進行精準詐騙。AEGIS CORE 的 LLM 生成引擎已開始模擬這類新型話術，
        提前訓練防詐模型。
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 頁面：詐騙免疫訓練
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "training":
    st.title("詐騙免疫訓練")
    st.markdown("透過真實詐騙話術練習，提升你的防詐識別能力，完成訓練後獲得防詐免疫證書。")

    from app.dashboard.page_modules.training import (
        DIFFICULTY_LEVELS, SCAM_TYPES, TAG_EXPLANATIONS,
        TrainingSession, TrainingQuestion,
        build_training_prompt, evaluate_answer, generate_certificate_html,
    )
    from app.pattern_analyzer.xai_highlighter import XAIHighlighter
    from app.pattern_analyzer.psych_classifier import VALID_PSYCHOLOGICAL_TAGS

    TAG_COLORS = {
        "信任建立": "#d4edda", "緊迫感製造": "#fff3cd",
        "情緒勒索": "#f8d7da", "權威偽裝": "#cce5ff", "利益誘導": "#e2d9f3",
    }
    TAG_TEXT_COLORS = {
        "信任建立": "#155724", "緊迫感製造": "#856404",
        "情緒勒索": "#721c24", "權威偽裝": "#004085", "利益誘導": "#4a235a",
    }

    # ── 初始化 session state ──────────────────────────────────────────────────
    if "training_session" not in st.session_state:
        st.session_state["training_session"] = None
    if "training_answered" not in st.session_state:
        st.session_state["training_answered"] = False
    if "training_last_result" not in st.session_state:
        st.session_state["training_last_result"] = None

    session: TrainingSession | None = st.session_state["training_session"]

    # ── 設定畫面（尚未開始）──────────────────────────────────────────────────
    if session is None or (session.completed and st.session_state.get("training_restart")):
        st.session_state["training_restart"] = False
        st.subheader("訓練設定")

        col1, col2 = st.columns(2)
        with col1:
            difficulty = st.selectbox("選擇難度", list(DIFFICULTY_LEVELS.keys()))
            diff_info = DIFFICULTY_LEVELS[difficulty]
            st.caption(diff_info["description"])
            st.caption(f"通過門檻：{diff_info['pass_score']}% 正確率")
        with col2:
            scam_type = st.selectbox("選擇詐騙類型", SCAM_TYPES)

        st.markdown("---")
        st.subheader("訓練說明")
        st.markdown("""
        1. 系統會生成真實詐騙話術樣本
        2. 閱讀後選擇你認為包含的**心理操控特徵**
        3. 系統給出 XAI 解析與得分
        4. 累積達到通過門檻即可獲得**防詐免疫證書** 
        """)

        has_llm = bool(st.session_state.get("openai_api_key"))
        if not has_llm:
            st.warning("未設定 LLM API Key，將使用內建示範題目進行訓練")

        if st.button("開始訓練", type="primary", use_container_width=True):
            with st.spinner("正在生成訓練題目..."):
                questions = []

                if has_llm:
                    try:
                        from app.scam_engine.generator import generate_scam_samples
                        scenario, audience = build_training_prompt(scam_type, difficulty)
                        result = _safe_async_run(generate_scam_samples(
                            scenario=scenario,
                            target_audience=audience,
                            min_samples=diff_info["min_samples"],
                        ))
                        if "error_code" not in result:
                            highlighter = XAIHighlighter()
                            for s in result.get("samples", []):
                                xai = highlighter.highlight(s["content"])
                                questions.append(TrainingQuestion(
                                    content=s["content"],
                                    is_scam=True,
                                    psychological_tags=xai.triggered_tags,
                                    difficulty=difficulty,
                                    scam_type=scam_type,
                                ))
                    except Exception:
                        pass

                # 若 LLM 失敗或無 key，使用真實詐騙話術樣本
                if not questions:
                    from app.pattern_analyzer.xai_highlighter import XAIHighlighter
                    import random
                    highlighter = XAIHighlighter()
                    matching = [s for s in REAL_SCAM_SCRIPTS if s["scam_type"] == scam_type]
                    if not matching:
                        matching = REAL_SCAM_SCRIPTS
                    selected = random.sample(matching, min(diff_info["min_samples"], len(matching)))
                    while len(selected) < diff_info["min_samples"]:
                        selected.append(random.choice(REAL_SCAM_SCRIPTS))
                    for s in selected:
                        xai = highlighter.highlight(s["content"])
                        questions.append(TrainingQuestion(
                            content=s["content"],
                            is_scam=True,
                            psychological_tags=xai.triggered_tags or s.get("psychological_tags", []),
                            difficulty=difficulty,
                            scam_type=s["scam_type"],
                        ))

                new_session = TrainingSession(
                    difficulty=difficulty,
                    scam_type=scam_type,
                    questions=questions,
                    total_questions=len(questions),
                )
                st.session_state["training_session"] = new_session
                st.session_state["training_answered"] = False
                st.session_state["training_last_result"] = None
                st.rerun()

    # ── 訓練進行中 ────────────────────────────────────────────────────────────
    elif session is not None and not session.completed:
        q = session.current_question
        if q is None:
            session.completed = True
            st.rerun()
        else:
            # 進度條
            progress = session.current_index / session.total_questions
            st.progress(progress)
            st.caption(f"題目 {session.current_index + 1} / {session.total_questions}　｜　目前得分：{session.score}/{session.current_index}")

            st.markdown("---")
            st.subheader(f"詐騙話術樣本 #{session.current_index + 1}")

            # 顯示話術文本
            st.markdown(
                f'<div style="background:#fff8e1;border-left:4px solid #f39c12;'
                f'padding:15px;border-radius:6px;font-size:1.05rem;line-height:1.8;">'
                f'{q.content}</div>',
                unsafe_allow_html=True,
            )

            st.markdown("---")

            if not st.session_state["training_answered"]:
                # 作答區
                st.subheader("你認為這段話術包含哪些心理操控手法？")
                st.caption("可多選，選完後按「提交答案」")

                selected_tags = []
                cols = st.columns(3)
                for i, tag in enumerate(sorted(VALID_PSYCHOLOGICAL_TAGS)):
                    with cols[i % 3]:
                        bg = TAG_COLORS.get(tag, "#eee")
                        fg = TAG_TEXT_COLORS.get(tag, "#333")
                        if st.checkbox(
                            tag,
                            key=f"tag_{session.current_index}_{tag}",
                        ):
                            selected_tags.append(tag)

                if st.button("提交答案", type="primary", use_container_width=True):
                    result = evaluate_answer(q, selected_tags)
                    if result["is_correct"]:
                        session.score += 1
                    session.answers.append({
                        "question_index": session.current_index,
                        "result": result,
                    })
                    st.session_state["training_answered"] = True
                    st.session_state["training_last_result"] = result
                    st.rerun()

            else:
                # 顯示解析結果
                result = st.session_state["training_last_result"]
                if result:
                    if result["is_correct"]:
                        st.success(f"答對了！{result['feedback']}")
                    else:
                        st.error(f"答錯了。{result['feedback']}")

                    # XAI 高亮顯示
                    st.subheader("XAI 解析")
                    highlighter = XAIHighlighter()
                    xai = highlighter.highlight(q.content)

                    if xai.spans:
                        html_parts = []
                        prev_end = 0
                        for span in xai.spans:
                            if span.start > prev_end:
                                html_parts.append(q.content[prev_end:span.start])
                            bg = TAG_COLORS.get(span.tag, "#eee")
                            fg = TAG_TEXT_COLORS.get(span.tag, "#333")
                            html_parts.append(
                                f'<mark style="background:{bg};color:{fg};padding:2px 4px;'
                                f'border-radius:3px;font-weight:bold;" title="{span.tag}">'
                                f'{span.text}</mark>'
                            )
                            prev_end = span.end
                        if prev_end < len(q.content):
                            html_parts.append(q.content[prev_end:])
                        st.markdown(
                            f'<div style="line-height:2;padding:12px;border:1px solid #dee2e6;'
                            f'border-radius:6px;background:#fafafa;">{"".join(html_parts)}</div>',
                            unsafe_allow_html=True,
                        )

                    # 特徵說明
                    if result["correct_tags"]:
                        st.subheader("心理操控特徵解說")
                        for tag in result["correct_tags"]:
                            bg = TAG_COLORS.get(tag, "#eee")
                            fg = TAG_TEXT_COLORS.get(tag, "#333")
                            explanation = TAG_EXPLANATIONS.get(tag, "")
                            st.markdown(
                                f'<div style="background:{bg};color:{fg};padding:10px 14px;'
                                f'border-radius:6px;margin:6px 0;">'
                                f'<strong>{tag}</strong>：{explanation}</div>',
                                unsafe_allow_html=True,
                            )

                if st.button("下一題", type="primary", use_container_width=True):
                    session.current_index += 1
                    st.session_state["training_answered"] = False
                    st.session_state["training_last_result"] = None
                    if session.current_index >= session.total_questions:
                        session.completed = True
                    st.rerun()

    # ── 訓練完成 ──────────────────────────────────────────────────────────────
    elif session is not None and session.completed:
        score_pct = session.final_score_pct
        passed = session.passed
        threshold = DIFFICULTY_LEVELS.get(session.difficulty, {}).get("pass_score", 70)

        st.markdown("---")
        st.subheader("訓練完成！")

        col1, col2, col3 = st.columns(3)
        col1.metric("最終得分", f"{score_pct:.0f}%")
        col2.metric("答對題數", f"{session.score}/{session.total_questions}")
        col3.metric("通過門檻", f"{threshold}%", delta=f"{score_pct - threshold:+.0f}%")

        if passed:
            st.balloons()
            st.success(f"恭喜通過 {session.difficulty} 訓練！你已具備識別「{session.scam_type}」的能力。")
            st.subheader(" 你的防詐免疫證書")
            cert_html = generate_certificate_html(session)
            st.markdown(cert_html, unsafe_allow_html=True)
            st.caption("截圖保存或分享給家人朋友，一起提升防詐意識！")
        else:
            st.warning(f"未達通過門檻（{threshold}%），建議再練習一次。")
            st.info("提示：仔細觀察話術中的緊迫感用詞、權威身份聲稱和利益誘惑。")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("再練一次（相同設定）", use_container_width=True):
                st.session_state["training_session"] = None
                st.session_state["training_answered"] = False
                st.session_state["training_last_result"] = None
                st.rerun()
        with col_b:
            if st.button("更換設定重新開始", use_container_width=True):
                st.session_state["training_session"] = None
                st.session_state["training_answered"] = False
                st.session_state["training_last_result"] = None
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# 頁面 1：熱詞排行榜
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "hotwords":
    st.title("熱詞排行榜")
    st.markdown("顯示近期詐騙話術中出現頻率最高的關鍵詞，每 24 小時自動更新。")

    from app.dashboard.page_modules.hotwords import compute_hotword_ranking, get_hotword_page_data

    def fetch_hotword_data():
        """從後端取得熱詞資料（示範：直接使用 mock 資料）"""
        return MOCK_KEYWORD_FREQ

    # 帶快取降級的資料載入
    data, is_from_cache, cached_at = cache.fetch_with_fallback(
        key="hotword_freq",
        fetch_fn=fetch_hotword_data,
    )
    show_cache_warning(is_from_cache, cached_at)

    # 計算排行榜
    page_data = get_hotword_page_data(data)
    ranking = page_data["ranking"]

    col1, col2, col3 = st.columns(3)
    col1.metric("關鍵詞總數", page_data["total_keywords"])
    col2.metric("顯示筆數", page_data["displayed_count"])
    col3.metric("最高頻詞", ranking[0] if ranking else "—")

    st.markdown("---")

    if ranking:
        # 建立圖表資料（保留頻率值以供顯示）
        chart_data = {word: data[word] for word in ranking if word in data}

        st.subheader("熱詞頻率長條圖")
        import pandas as pd
        df_chart = pd.DataFrame(
            list(chart_data.items()), columns=["關鍵詞", "出現次數"]
        ).set_index("關鍵詞")
        st.bar_chart(df_chart)

        st.subheader("排行榜明細")
        import pandas as pd
        rank_df = pd.DataFrame(
            [{"排名": i + 1, "關鍵詞": word, "出現次數": data.get(word, 0)}
             for i, word in enumerate(ranking)]
        )
        st.dataframe(rank_df, use_container_width=True, hide_index=True)
    else:
        st.info("目前無熱詞資料。")


# ══════════════════════════════════════════════════════════════════════════════
# 頁面 2：XAI 話術分析
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "xai":
    st.title("XAI 話術分析")
    st.markdown("輸入詐騙話術文字，系統將高亮顯示觸發心理操控特徵的片段，並列出對應標籤。")

    from app.pattern_analyzer.xai_highlighter import XAIHighlighter

    # 標籤對應顏色（每個心理特徵使用不同背景色）
    TAG_COLORS: dict[str, str] = {
        "信任建立":   "#d4edda",   # 綠色
        "緊迫感製造": "#fff3cd",   # 黃色
        "情緒勒索":   "#f8d7da",   # 紅色
        "權威偽裝":   "#cce5ff",   # 藍色
        "利益誘導":   "#e2d9f3",   # 紫色
    }
    TAG_TEXT_COLORS: dict[str, str] = {
        "信任建立":   "#155724",
        "緊迫感製造": "#856404",
        "情緒勒索":   "#721c24",
        "權威偽裝":   "#004085",
        "利益誘導":   "#4a235a",
    }

    # 範例文字
    EXAMPLE_TEXT = (
        "您好，我是台灣銀行客服專員，您的帳戶出現異常交易，"
        "請立即撥打我們的官方電話，否則帳戶將在24小時內凍結。"
        "為了保護您的資金安全，請馬上提供驗證碼，我們的專業團隊會幫助您解決問題。"
    )

    input_text = st.text_area(
        "輸入話術文字",
        value=EXAMPLE_TEXT,
        height=150,
        placeholder="請輸入要分析的詐騙話術文字...",
    )

    if st.button("開始分析", type="primary"):
        if not input_text.strip():
            st.warning("請輸入文字後再進行分析。")
        else:
            highlighter = XAIHighlighter()
            result = highlighter.highlight(input_text)

            # ── 統計資訊 ──────────────────────────────────────────────────
            col1, col2, col3 = st.columns(3)
            col1.metric("觸發片段數", len(result.spans))
            col2.metric("觸發標籤數", len(result.triggered_tags))
            col3.metric("覆蓋率", f"{result.coverage_ratio:.1%}")

            st.markdown("---")

            # ── 高亮顯示 ──────────────────────────────────────────────────
            st.subheader("高亮分析結果")

            if result.spans:
                # 建立 HTML 高亮文字
                html_parts: list[str] = []
                prev_end = 0
                for span in result.spans:
                    # 未高亮的部分
                    if span.start > prev_end:
                        plain = input_text[prev_end:span.start]
                        html_parts.append(plain.replace("\n", "<br>"))
                    # 高亮片段
                    bg = TAG_COLORS.get(span.tag, "#eeeeee")
                    fg = TAG_TEXT_COLORS.get(span.tag, "#333333")
                    html_parts.append(
                        f'<mark style="background-color:{bg};color:{fg};'
                        f'padding:2px 4px;border-radius:3px;font-weight:bold;" '
                        f'title="{span.tag}（信心：{span.score:.0%}）">'
                        f'{span.text}</mark>'
                    )
                    prev_end = span.end
                # 剩餘文字
                if prev_end < len(input_text):
                    html_parts.append(input_text[prev_end:].replace("\n", "<br>"))

                st.markdown(
                    f'<div style="line-height:2;font-size:1.05rem;padding:12px;'
                    f'border:1px solid #dee2e6;border-radius:6px;background:#fafafa;">'
                    f'{"".join(html_parts)}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.info("未偵測到心理操控特徵片段。")

            # ── 標籤圖例 ──────────────────────────────────────────────────
            st.markdown("---")
            st.subheader("顏色圖例")
            legend_cols = st.columns(len(TAG_COLORS))
            for col, (tag, bg) in zip(legend_cols, TAG_COLORS.items()):
                fg = TAG_TEXT_COLORS[tag]
                col.markdown(
                    f'<div style="background:{bg};color:{fg};padding:6px 10px;'
                    f'border-radius:4px;text-align:center;font-weight:bold;">{tag}</div>',
                    unsafe_allow_html=True,
                )

            # ── 觸發標籤列表 ──────────────────────────────────────────────
            st.markdown("---")
            st.subheader("觸發的心理特徵標籤")
            if result.triggered_tags:
                for tag in result.triggered_tags:
                    bg = TAG_COLORS.get(tag, "#eeeeee")
                    fg = TAG_TEXT_COLORS.get(tag, "#333333")
                    # 計算該標籤的片段數與平均信心
                    tag_spans = [s for s in result.spans if s.tag == tag]
                    avg_score = sum(s.score for s in tag_spans) / len(tag_spans)
                    st.markdown(
                        f'<span style="background:{bg};color:{fg};padding:4px 10px;'
                        f'border-radius:12px;margin-right:8px;font-weight:bold;">'
                        f'{tag}</span> '
                        f'觸發 {len(tag_spans)} 個片段，平均信心 {avg_score:.0%}',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("本文字未觸發任何心理特徵標籤。")


# ══════════════════════════════════════════════════════════════════════════════
# 頁面 3：沙盤推演
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "sandbox":
    st.title("沙盤推演")
    st.markdown("設定詐騙情境參數，模擬預測可能出現的詐騙變種特徵與風險等級。")

    from app.dashboard.page_modules.sandbox import (
        SandboxParams, run_sandbox_simulation,
        VALID_SCENARIO_TYPES, VALID_TARGET_AUDIENCES,
    )

    with st.form("sandbox_form"):
        col1, col2 = st.columns(2)
        with col1:
            scenario_type = st.selectbox(
                "詐騙情境類型",
                sorted(VALID_SCENARIO_TYPES),
                index=0,
            )
            target_audience = st.selectbox(
                "目標受眾",
                sorted(VALID_TARGET_AUDIENCES),
                index=0,
            )
        with col2:
            risk_filter = st.selectbox(
                "風險等級篩選（可選）",
                ["不篩選", "高", "中", "低"],
                index=0,
            )
            time_window = st.slider(
                "分析時間視窗（天）",
                min_value=1, max_value=90, value=7,
            )

        submitted = st.form_submit_button("執行推演", type="primary")

    if submitted:
        def fetch_sandbox_result():
            params = SandboxParams(
                scenario_type=scenario_type,
                target_audience=target_audience,
                risk_level_filter=risk_filter if risk_filter != "不篩選" else None,
                time_window_days=time_window,
            )
            return run_sandbox_simulation(params, risk_vectors=COMPUTED_RISK_VECTORS)

        result, is_from_cache, cached_at = cache.fetch_with_fallback(
            key=f"sandbox_{scenario_type}_{target_audience}_{risk_filter}_{time_window}",
            fetch_fn=fetch_sandbox_result,
        )
        show_cache_warning(is_from_cache, cached_at)

        # ── 結果顯示 ──────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("推演結果")

        risk_color = {"高": "●", "中": "●", "低": "●"}.get(result.predicted_risk_level, "○")
        col1, col2, col3 = st.columns(3)
        col1.metric("預測風險等級", f"{risk_color} {result.predicted_risk_level}")
        col2.metric("預測信心分數", f"{result.confidence_score:.0%}")
        col3.metric("識別特徵數", len(result.predicted_features))

        st.info(result.summary)

        if result.predicted_features:
            st.subheader("預測高風險特徵")
            for i, feature in enumerate(result.predicted_features, 1):
                st.markdown(f"**{i}.** {feature}")

        if result.related_cluster_labels:
            st.subheader("相關詐騙類群")
            st.write("、".join(result.related_cluster_labels))


# ══════════════════════════════════════════════════════════════════════════════
# 頁面 4：受害風險地圖
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "risk_map":
    st.title("受害風險地圖")
    st.markdown("依年齡層與地區維度呈現受害風險指數，資料來源為預測層輸出的風險向量。")

    from app.dashboard.page_modules.risk_map import build_risk_map, get_risk_map_summary, VALID_REGIONS, VALID_AGE_GROUPS
    import pandas as pd

    # 篩選選項
    with st.expander("篩選設定", expanded=False):
        selected_regions = st.multiselect(
            "選擇地區（留空顯示全部）",
            sorted(VALID_REGIONS),
            default=[],
        )
        selected_ages = st.multiselect(
            "選擇年齡層（留空顯示全部）",
            sorted(VALID_AGE_GROUPS),
            default=[],
        )

    def fetch_risk_map():
        regions = selected_regions if selected_regions else None
        ages = selected_ages if selected_ages else None
        # 用真實縣市案件數計算風險指數
        real_vectors = []
        for region, cases in TAIWAN_SCAM_CASES_BY_REGION.items():
            risk_score = min(0.95, cases / 12000)
            for age_group, ratio in VICTIM_AGE_DISTRIBUTION.items():
                real_vectors.append({
                    "scam_cluster_label": "綜合詐騙",
                    "risk_score": round(risk_score * ratio * 3, 2),
                    "target_audience": age_group,
                    "region": region,
                })
        return build_risk_map(real_vectors, age_groups=ages, regions=regions)

    risk_map, is_from_cache, cached_at = cache.fetch_with_fallback(
        key=f"risk_map_{','.join(selected_regions)}_{','.join(selected_ages)}",
        fetch_fn=fetch_risk_map,
    )
    show_cache_warning(is_from_cache, cached_at)

    # ── 摘要指標 ──────────────────────────────────────────────────────────
    summary = get_risk_map_summary(risk_map)
    overall_icon = {"高": "●", "中": "●", "低": "●"}.get(summary["overall_risk_level"], "○")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("整體風險等級", f"{overall_icon} {summary['overall_risk_level']}")
    col2.metric("高風險區域", summary["high_risk_count"])
    col3.metric("中風險區域", summary["medium_risk_count"])
    col4.metric("低風險區域", summary["low_risk_count"])

    if summary.get("highest_risk"):
        hr = summary["highest_risk"]
        st.error(
            f"最高風險：**{hr['age_group']}** × **{hr['region']}**"
            f"（風險指數 {hr['risk_index']:.2f}，主要詐騙類型：{hr['dominant_scam_type']}）"
        )

    st.markdown("---")

    # ── 風險地圖表格 ──────────────────────────────────────────────────────
    st.subheader("風險指數明細表")

    if risk_map.entries:
        rows = []
        for entry in risk_map.entries:
            risk_icon = {"高": "●", "中": "●", "低": "●"}.get(entry.risk_level, "○")
            rows.append({
                "年齡層": entry.age_group,
                "地區": entry.region,
                "風險指數": round(entry.risk_index, 4),
                "風險等級": f"{risk_icon} {entry.risk_level}",
                "相關案件數": entry.case_count,
                "主要詐騙類型": entry.dominant_scam_type,
            })

        df = pd.DataFrame(rows)
        # 依風險指數降序排列
        df = df.sort_values("風險指數", ascending=False).reset_index(drop=True)
        df.index += 1

        st.dataframe(df, use_container_width=True)
    else:
        st.info("目前無風險地圖資料。")


# ══════════════════════════════════════════════════════════════════════════════
# 頁面 7：模型準確率評估
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "evaluation":
    st.title("模型準確率評估")
    st.markdown("基於 165 反詐騙通報案例與正常對話的混合測試集，評估 XAI 規則式分類器效能。")

    import pandas as pd
    import numpy as np
    from app.pattern_analyzer.psych_classifier import PsychologicalClassifier
    from app.pattern_analyzer.xai_highlighter import XAIHighlighter

    # ── 真實效能指標（直接展示）──────────────────────────────────────────────
    st.subheader("模型效能指標（基於真實資料測試）")
    st.caption(f"測試集：{MODEL_PERFORMANCE['test_samples']} 筆（詐騙 {MODEL_PERFORMANCE['scam_samples']} 筆 + 正常 {MODEL_PERFORMANCE['normal_samples']} 筆）｜評估日期：{MODEL_PERFORMANCE['evaluation_date']}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("整體準確率", f"{MODEL_PERFORMANCE['accuracy']:.1%}")
    c2.metric("精確率", f"{MODEL_PERFORMANCE['precision']:.1%}")
    c3.metric("召回率（攔截率）", f"{MODEL_PERFORMANCE['recall']:.1%}")
    c4.metric("F1 分數", f"{MODEL_PERFORMANCE['f1_score']:.3f}")
    c5.metric("誤判率", f"{MODEL_PERFORMANCE['false_positive_rate']:.1%}", delta=f"-{MODEL_PERFORMANCE['false_positive_rate']:.1%}", delta_color="inverse")

    st.markdown("---")

    # ── 月度趨勢圖 ────────────────────────────────────────────────────────────
    st.subheader("台灣詐騙案件月度趨勢")
    st.caption("資料來源：內政部警政署 165 反詐騙諮詢專線統計")
    df_trend = pd.DataFrame(MONTHLY_TREND)
    df_trend = df_trend.set_index("month")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("**案件數趨勢**")
        st.line_chart(df_trend["cases"])
    with col_t2:
        st.markdown("**損失金額趨勢（億元）**")
        st.line_chart(df_trend["amount_billion"])

    st.markdown("---")

    # ── 各詐騙類型統計 ────────────────────────────────────────────────────────
    st.subheader(f"各詐騙類型案件統計（{_latest_year}年）")
    scam_rows = []
    for stype, stats in SCAM_TYPE_STATS.items():
        trend_icon = "↑" if stats["trend"] == "上升" else "↓" if stats["trend"] == "下降" else "→"
        scam_rows.append({
            "詐騙類型": stype,
            "案件數": f"{stats['cases']:,}",
            "平均損失": f"NT$ {stats['avg_loss_ntd']:,}",
            "趨勢": f"{trend_icon} {stats['trend']}",
        })
    st.dataframe(pd.DataFrame(scam_rows), use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── 互動式測試（用真實詐騙樣本）─────────────────────────────────────────
    st.subheader("即時分類測試（真實詐騙話術樣本）")

    if st.button("執行評估", type="primary"):
        with st.spinner("正在分析真實詐騙話術樣本..."):
            classifier = PsychologicalClassifier()
            highlighter = XAIHighlighter()

            # 加入正常對話作為對照
            normal_texts = [
                ("今天天氣很好，適合出門散步。", False),
                ("請問您的訂單已出貨，預計明天送達，感謝您的購買。", False),
                ("您好，這是您的月結帳單，請於截止日前繳費，謝謝。", False),
                ("系統維護通知：本系統將於今晚12點進行例行維護。", False),
                ("感謝您的來電，我們的客服人員將在工作時間內回覆您。", False),
            ]

            test_cases = [(s["content"], True) for s in REAL_SCAM_SCRIPTS] + normal_texts

            y_true, y_pred, results_data = [], [], []
            for text, is_scam in test_cases:
                tags = classifier.classify(text)
                xai = highlighter.highlight(text)
                predicted_scam = len(tags) > 0 or xai.coverage_ratio > 0.05
                y_true.append(1 if is_scam else 0)
                y_pred.append(1 if predicted_scam else 0)
                results_data.append({
                    "文字摘要": text[:40] + "...",
                    "真實標籤": "詐騙" if is_scam else "正常",
                    "預測標籤": "詐騙" if predicted_scam else "正常",
                    "觸發特徵": ", ".join(tags) if tags else "無",
                    "覆蓋率": f"{xai.coverage_ratio:.1%}",
                    "結果": "正確" if (is_scam == predicted_scam) else "錯誤",
                })

            y_true_arr = np.array(y_true)
            y_pred_arr = np.array(y_pred)
            tp = int(np.sum((y_true_arr == 1) & (y_pred_arr == 1)))
            tn = int(np.sum((y_true_arr == 0) & (y_pred_arr == 0)))
            fp = int(np.sum((y_true_arr == 0) & (y_pred_arr == 1)))
            fn = int(np.sum((y_true_arr == 1) & (y_pred_arr == 0)))
            accuracy = (tp + tn) / len(y_true) if y_true else 0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        st.markdown("**即時測試結果**")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("準確率", f"{accuracy:.1%}")
        r2.metric("精確率", f"{precision:.1%}")
        r3.metric("召回率", f"{recall:.1%}")
        r4.metric("F1", f"{f1:.3f}")

        cm_df = pd.DataFrame(
            [[tp, fn], [fp, tn]],
            index=["實際：詐騙", "實際：正常"],
            columns=["預測：詐騙", "預測：正常"],
        )
        st.dataframe(cm_df.style.background_gradient(cmap="RdYlGn", axis=None), use_container_width=False)
        st.caption(f"TP={tp}（正確攔截）｜TN={tn}（正確放行）｜FP={fp}（誤判）｜FN={fn}（漏判）")

        st.markdown("**逐筆分析**")
        st.dataframe(pd.DataFrame(results_data), use_container_width=True, hide_index=True)
    else:
        st.info("點擊「執行評估」按鈕，對真實詐騙話術樣本進行即時分類測試。")
