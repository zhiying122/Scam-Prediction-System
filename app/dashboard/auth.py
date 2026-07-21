"""
ScamDNA — 登入認證模組

提供 Dashboard 註冊、登入、登出功能，整合 RBAC 角色系統。
使用 Streamlit session_state 管理登入狀態。
已註冊帳號存於 session-level in-memory store（重啟後重置）。

預設帳號（Demo 用途）：
- admin / Aegis@2026 → 系統管理員（預建帳號，無需註冊）
"""

import hashlib
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import streamlit as st

from app.access_controller.rbac import Role


@dataclass
class UserProfile:
    """使用者資料"""
    username: str
    display_name: str
    role: Role
    avatar_emoji: str
    last_login: Optional[datetime] = None


# ── 密碼雜湊 ──────────────────────────────────────────────────────────────────
def _hash_password(password: str) -> str:
    """SHA-256 密碼雜湊"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ── 使用者資料庫（in-memory，存在 session_state 確保跨 rerun 持久）────────────
def _get_user_db() -> dict[str, dict]:
    """取得使用者資料庫（首次存取時初始化預設帳號）"""
    if "_user_db" not in st.session_state:
        st.session_state["_user_db"] = {
            "admin": {
                "password_hash": _hash_password("Aegis@2026"),
                "display_name": "系統管理員",
                "role": Role.SYSTEM_ADMIN,
                "avatar_emoji": "⬡",
            },
        }
    return st.session_state["_user_db"]


# ── 註冊 ──────────────────────────────────────────────────────────────────────
def register(username: str, password: str, display_name: str) -> tuple[bool, str]:
    """
    註冊新帳號

    Args:
        username: 帳號（英數字，3-20 字元）
        password: 密碼（至少 6 字元）
        display_name: 顯示名稱

    Returns:
        (success, message)
    """
    username = username.strip().lower()
    display_name = display_name.strip()

    # 驗證
    if not username:
        return False, "請輸入帳號"
    if len(username) < 3 or len(username) > 20:
        return False, "帳號長度須為 3–20 字元"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "帳號僅允許英文字母、數字與底線"
    if not password or len(password) < 6:
        return False, "密碼長度至少 6 字元"
    if not display_name:
        return False, "請輸入顯示名稱"

    db = _get_user_db()
    if username in db:
        return False, "此帳號已被使用"

    # 建立帳號（新註冊使用者預設為詐騙分析師角色）
    db[username] = {
        "password_hash": _hash_password(password),
        "display_name": display_name,
        "role": Role.SCAM_ANALYST,
        "avatar_emoji": "🔍",
    }
    return True, "註冊成功！請登入。"


# ── 認證 ──────────────────────────────────────────────────────────────────────
def authenticate(username: str, password: str) -> Optional[UserProfile]:
    """
    驗證帳號密碼

    Returns:
        UserProfile 如果驗證成功，否則 None
    """
    db = _get_user_db()
    user_data = db.get(username.strip().lower())
    if user_data is None:
        return None

    if user_data["password_hash"] != _hash_password(password):
        return None

    return UserProfile(
        username=username.strip().lower(),
        display_name=user_data["display_name"],
        role=user_data["role"],
        avatar_emoji=user_data["avatar_emoji"],
        last_login=datetime.now(),
    )


def login(user: UserProfile) -> None:
    """將使用者資訊寫入 session_state"""
    st.session_state["authenticated"] = True
    st.session_state["user"] = user
    st.session_state["login_time"] = datetime.now()


def logout() -> None:
    """清除登入狀態"""
    st.session_state["authenticated"] = False
    st.session_state.pop("user", None)
    st.session_state.pop("login_time", None)


def is_authenticated() -> bool:
    """檢查是否已登入"""
    return st.session_state.get("authenticated", False)


def get_current_user() -> Optional[UserProfile]:
    """取得目前登入的使用者"""
    if not is_authenticated():
        return None
    return st.session_state.get("user")


# ── 登入/註冊頁面（Forest Gate）───────────────────────────────────────────────
def render_login_page() -> bool:
    """
    渲染登入/註冊頁面（Forest Gate 正式風格）

    Returns:
        True 如果使用者已成功登入
        False 如果尚未登入
    """
    if is_authenticated():
        return True

    # 品牌／插畫必須用 st.html：st.markdown 會被 DOMPurify 剝除
    st.html(_LOGIN_CSS)
    st.html(_LOGIN_STAGE_HTML)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["登入", "註冊"])

        with tab_login:
            _render_login_form()

        with tab_register:
            _render_register_form()

    return False


def _render_login_form() -> None:
    """渲染登入表單"""
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "帳號",
            placeholder="請輸入帳號",
            key="login_username",
        )
        password = st.text_input(
            "密碼",
            type="password",
            placeholder="請輸入密碼",
            key="login_password",
        )
        submitted = st.form_submit_button("登入", use_container_width=True, type="primary")

        if submitted:
            if not username or not password:
                st.error("請輸入帳號與密碼")
            else:
                user = authenticate(username, password)
                if user is None:
                    st.error("帳號或密碼錯誤")
                    time.sleep(0.5)
                else:
                    login(user)
                    st.rerun()

    st.html('<p class="scamdna-demo-hint">Demo · admin / Aegis@2026</p>')


def _render_register_form() -> None:
    """渲染註冊表單"""
    with st.form("register_form", clear_on_submit=False):
        new_username = st.text_input(
            "帳號",
            placeholder="英文字母、數字、底線（3-20 字元）",
            key="reg_username",
        )
        new_display = st.text_input(
            "顯示名稱",
            placeholder="您的暱稱或真名",
            key="reg_display_name",
        )
        new_password = st.text_input(
            "密碼",
            type="password",
            placeholder="至少 6 字元",
            key="reg_password",
        )
        new_password2 = st.text_input(
            "確認密碼",
            type="password",
            placeholder="再輸入一次密碼",
            key="reg_password2",
        )
        reg_submitted = st.form_submit_button("註冊", use_container_width=True, type="primary")

        if reg_submitted:
            if not new_username or not new_password or not new_display:
                st.error("請填寫所有欄位")
            elif new_password != new_password2:
                st.error("兩次密碼不一致")
            else:
                ok, msg = register(new_username, new_password, new_display)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)


# ── 使用者列 ──────────────────────────────────────────────────────────────────
def render_user_bar() -> str:
    """生成頂部使用者資訊 HTML"""
    user = get_current_user()
    if user is None:
        return ""

    role_badge_cls = {
        Role.SYSTEM_ADMIN: "role-admin",
        Role.SCAM_ANALYST: "role-analyst",
        Role.GENERAL_OPERATOR: "role-viewer",
        Role.EXTERNAL_CLIENT: "role-viewer",
    }.get(user.role, "role-viewer")

    login_time = st.session_state.get("login_time")
    time_str = login_time.strftime("%H:%M") if login_time else ""

    # 避免 display_name 與 role.value 相同時重複顯示（如 admin → 兩個「系統管理員」）
    name_label = user.display_name
    if name_label.strip() == user.role.value.strip():
        name_label = user.username

    time_html = (
        f'<span class="user-time">{time_str}</span>' if time_str else ""
    )

    return (
        f'<div class="user-bar" translate="no">'
        f'<span class="user-avatar" aria-hidden="true">{user.avatar_emoji}</span>'
        f'<span class="user-name">{name_label}</span>'
        f'<span class="user-role {role_badge_cls}">{user.role.value}</span>'
        f'{time_html}'
        f'</div>'
    )


# ── 登入頁面 CSS — Forest Gate ────────────────────────────────────────────────
_LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Noto+Sans+TC:wght@400;500;600;700&display=swap');

.stApp {
    background:
        radial-gradient(ellipse 90% 55% at 50% -5%, rgba(34,197,94,0.16), transparent 58%),
        linear-gradient(165deg, #07140F 0%, #0F2419 42%, #14532D 100%) !important;
    font-family: 'Noto Sans TC', 'Manrope', sans-serif !important;
}
header { visibility: hidden !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
[data-testid="stSidebar"] { display: none !important; }

.main .block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 520px !important;
}

.scamdna-stage {
    position: relative;
    z-index: 1;
    width: min(520px, 92vw);
    margin: 1.5rem auto 0.25rem;
    text-align: center;
    animation: scamdnaFadeUp 0.55s ease-out;
}
.scamdna-art {
    width: min(280px, 70vw);
    height: auto;
    margin: 0 auto 10px;
    display: block;
    filter: drop-shadow(0 12px 28px rgba(0,0,0,0.28));
    animation: scamdnaFloat 5.5s ease-in-out infinite;
}
.scamdna-mark {
    position: relative;
    width: 52px;
    height: 52px;
    margin: 4px auto 14px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.scamdna-mark-ring {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 1.5px solid rgba(134,239,172,0.5);
    box-shadow: 0 0 0 7px rgba(22,101,52,0.22);
    animation: scamdnaPulse 3.2s ease-in-out infinite;
}
.scamdna-mark-core {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: linear-gradient(145deg, #166534, #14532d);
    color: #ecfdf5;
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(187,247,208,0.4);
}
.scamdna-brand {
    margin: 0 !important;
    color: #F0FDF4 !important;
    font-family: 'Manrope', 'Noto Sans TC', sans-serif !important;
    font-size: clamp(2rem, 5vw, 2.55rem) !important;
    font-weight: 800 !important;
    letter-spacing: 0.06em !important;
    line-height: 1.1 !important;
}
.scamdna-tagline {
    margin: 10px 0 0 !important;
    color: rgba(220,252,231,0.78) !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
}
.scamdna-pills {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
}
.scamdna-pill {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    color: rgba(236,253,245,0.88);
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(134,239,172,0.28);
    border-radius: 999px;
    padding: 5px 12px;
}

.scamdna-login-bg {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}
.scamdna-login-bg .grid {
    position: absolute;
    inset: -48px;
    background-image:
      linear-gradient(rgba(134,239,172,0.07) 1px, transparent 1px),
      linear-gradient(90deg, rgba(134,239,172,0.07) 1px, transparent 1px);
    background-size: 48px 48px;
    animation: scamdnaGridDrift 18s linear infinite;
    opacity: 0.85;
}
.scamdna-login-bg .radar {
    position: absolute;
    left: 50%;
    top: 46%;
    width: min(92vw, 920px);
    aspect-ratio: 1;
    transform: translate(-50%, -50%);
    border-radius: 50%;
}
.scamdna-login-bg .radar-rings {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 1px solid rgba(134,239,172,0.18);
    background:
      repeating-radial-gradient(
        circle at center,
        transparent 0,
        transparent 54px,
        rgba(134,239,172,0.11) 55px,
        rgba(134,239,172,0.11) 56px
      );
    box-shadow:
      inset 0 0 0 1px rgba(134,239,172,0.08),
      0 0 60px rgba(22,101,52,0.15);
}
.scamdna-login-bg .radar-cross::before,
.scamdna-login-bg .radar-cross::after {
    content: "";
    position: absolute;
    left: 50%;
    top: 50%;
    background: rgba(134,239,172,0.14);
}
.scamdna-login-bg .radar-cross::before {
    width: 1px;
    height: 100%;
    transform: translate(-50%, -50%);
}
.scamdna-login-bg .radar-cross::after {
    width: 100%;
    height: 1px;
    transform: translate(-50%, -50%);
}
.scamdna-login-bg .radar-sweep {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background: conic-gradient(
      from 0deg,
      transparent 0deg,
      rgba(134,239,172,0.05) 8deg,
      rgba(187,247,208,0.28) 28deg,
      rgba(134,239,172,0.06) 48deg,
      transparent 70deg
    );
    -webkit-mask-image: radial-gradient(circle, #000 0%, #000 68%, transparent 70%);
    mask-image: radial-gradient(circle, #000 0%, #000 68%, transparent 70%);
    animation: scamdnaRadarSpin 4.5s linear infinite;
    transform-origin: center center;
}
.scamdna-login-bg .radar-blip {
    position: absolute;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #86efac;
    box-shadow: 0 0 10px rgba(134,239,172,0.9);
    animation: scamdnaBlip 4.5s ease-in-out infinite;
}
.scamdna-login-bg .radar-blip.b1 { left: 62%; top: 34%; animation-delay: 0s; }
.scamdna-login-bg .radar-blip.b2 { left: 28%; top: 58%; animation-delay: 1.4s; }
.scamdna-login-bg .radar-blip.b3 { left: 70%; top: 66%; animation-delay: 2.6s; }
.scamdna-login-bg .glow {
    position: absolute;
    top: -10%;
    left: 50%;
    transform: translateX(-50%);
    width: 75vw;
    max-width: 780px;
    height: 45vh;
    background: radial-gradient(ellipse, rgba(22,101,52,0.4) 0%, transparent 70%);
}
.scamdna-side-art {
    position: absolute;
    top: 18%;
    width: min(220px, 18vw);
    opacity: 0.35;
}
.scamdna-side-art.left { left: 4%; }
.scamdna-side-art.right { right: 4%; transform: scaleX(-1); }
@media (max-width: 960px) {
    .scamdna-side-art { display: none; }
}

.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.22) !important;
    gap: 0 !important;
    padding: 0 !important;
    justify-content: center !important;
}
.stTabs [data-baseweb="tab"],
.stTabs [data-baseweb="tab"] p,
.stTabs [data-baseweb="tab"] span,
.stTabs [data-baseweb="tab"] div {
    background: transparent !important;
    color: rgba(236,253,245,0.88) !important;
    -webkit-text-fill-color: rgba(236,253,245,0.88) !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    border-radius: 0 !important;
    opacity: 1 !important;
}
.stTabs [data-baseweb="tab"] {
    padding: 10px 28px !important;
}
.stTabs [aria-selected="true"],
.stTabs [aria-selected="true"] p,
.stTabs [aria-selected="true"] span,
.stTabs [aria-selected="true"] div {
    background: transparent !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 700 !important;
    opacity: 1 !important;
}
.stTabs [data-baseweb="tab"]:hover,
.stTabs [data-baseweb="tab"]:hover p,
.stTabs [data-baseweb="tab"]:hover span {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background: #86efac !important;
    height: 2px !important;
}
.stTabs [data-baseweb="tab-border"] { display: none !important; }

div[data-testid="stForm"],
.stForm {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    padding: 26px 24px 20px !important;
    box-shadow:
        0 1px 2px rgba(15,36,25,0.06),
        0 22px 48px rgba(7,20,15,0.35) !important;
    margin-top: 0.85rem !important;
}

/* ── 輸入框：整平外層，消除密碼欄黑邊／黑三角接縫 ───────────────────────── */
div[data-testid="stForm"] .stTextInput > div,
.stForm .stTextInput > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
div[data-testid="stForm"] .stTextInput [data-baseweb="input"],
div[data-testid="stForm"] .stTextInput [data-baseweb="base-input"],
.stForm .stTextInput [data-baseweb="input"],
.stForm .stTextInput [data-baseweb="base-input"] {
    background: #F3F6F4 !important;
    background-color: #F3F6F4 !important;
    border: 1px solid #D1D5DB !important;
    border-color: #D1D5DB !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    outline: none !important;
    overflow: hidden !important;
    gap: 0 !important;
}
/* 內層所有容器同色，避免黑底透出 */
div[data-testid="stForm"] .stTextInput [data-baseweb="input"] *,
div[data-testid="stForm"] .stTextInput [data-baseweb="base-input"] *,
.stForm .stTextInput [data-baseweb="input"] *,
.stForm .stTextInput [data-baseweb="base-input"] * {
    background-color: transparent !important;
    box-shadow: none !important;
    border-color: transparent !important;
}
div[data-testid="stForm"] .stTextInput input,
.stForm .stTextInput input,
.stForm .stTextInput > div > div > input {
    background: #F3F6F4 !important;
    background-color: #F3F6F4 !important;
    border: none !important;
    border-radius: 8px !important;
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    caret-color: #14532d !important;
    font-size: 0.9rem !important;
    box-shadow: none !important;
    outline: none !important;
    width: 100% !important;
    min-width: 100% !important;
    flex: 1 1 auto !important;
}
div[data-testid="stForm"] .stTextInput input:-webkit-autofill,
div[data-testid="stForm"] .stTextInput input:-webkit-autofill:hover,
div[data-testid="stForm"] .stTextInput input:-webkit-autofill:focus,
.stForm .stTextInput input:-webkit-autofill,
.stForm .stTextInput input:-webkit-autofill:hover,
.stForm .stTextInput input:-webkit-autofill:focus {
    -webkit-box-shadow: 0 0 0 1000px #F3F6F4 inset !important;
    -webkit-text-fill-color: #111827 !important;
    caret-color: #14532d !important;
    transition: background-color 99999s ease-out;
}
div[data-testid="stForm"] .stTextInput [data-baseweb="input"]:focus-within,
.stForm .stTextInput [data-baseweb="input"]:focus-within {
    border-color: #166534 !important;
    box-shadow: 0 0 0 3px rgba(22,101,52,0.14) !important;
}
/* 隱藏密碼顯示鈕：此鈕是黑塊／黑三角來源 */
div[data-testid="stForm"] .stTextInput button,
.stForm .stTextInput button,
div[data-testid="stForm"] .stTextInput [data-testid="stBaseButton-secondary"],
.stForm .stTextInput [data-testid="stBaseButton-secondary"] {
    display: none !important;
    width: 0 !important;
    min-width: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

.stForm button[kind="primary"],
.stForm button[data-testid="stBaseButton-primary"],
.stForm [data-testid="stFormSubmitButton"] button,
div[data-testid="stForm"] button[kind="primary"],
div[data-testid="stForm"] [data-testid="stFormSubmitButton"] > button {
    background: #166534 !important;
    background-color: #166534 !important;
    background-image: none !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.14em !important;
    margin-top: 8px !important;
    box-shadow: 0 2px 10px rgba(22,101,52,0.3) !important;
}
.stForm button[kind="primary"]:hover,
.stForm [data-testid="stFormSubmitButton"] button:hover,
div[data-testid="stForm"] [data-testid="stFormSubmitButton"] > button:hover {
    background: #14532d !important;
    background-color: #14532d !important;
}
.stForm button[kind="primary"] p,
.stForm button[kind="primary"] span,
.stForm [data-testid="stFormSubmitButton"] button p,
.stForm [data-testid="stFormSubmitButton"] button span,
div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button p,
div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button span {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

.stForm label,
.stForm [data-testid="stWidgetLabel"] p {
    color: #374151 !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
}

.scamdna-demo-hint {
    text-align: center;
    margin: 14px 0 0 !important;
    color: rgba(220,252,231,0.4) !important;
    font-size: 0.68rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
}

@keyframes scamdnaFadeUp {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes scamdnaPulse {
    0%, 100% { opacity: 0.55; transform: scale(1); }
    50% { opacity: 0.95; transform: scale(1.05); }
}
@keyframes scamdnaFloat {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-6px); }
}
@keyframes scamdnaGridDrift {
    from { background-position: 0 0; }
    to { background-position: 48px 48px; }
}
@keyframes scamdnaRadarSpin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
@keyframes scamdnaBlip {
    0%, 70%, 100% { opacity: 0.15; transform: scale(0.7); }
    78%, 86% { opacity: 1; transform: scale(1.15); }
}
</style>
"""

_DNA_SVG = """
<svg class="scamdna-art" viewBox="0 0 280 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ScamDNA">
  <defs>
    <linearGradient id="strandA" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#86EFAC"/>
      <stop offset="100%" stop-color="#166534"/>
    </linearGradient>
    <linearGradient id="strandB" x1="100%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#BBF7D0"/>
      <stop offset="100%" stop-color="#14532D"/>
    </linearGradient>
    <filter id="softGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="2.2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <ellipse cx="140" cy="80" rx="118" ry="58" fill="rgba(22,101,52,0.18)"/>
  <path d="M40 40 C80 10, 120 150, 140 80 C160 10, 200 150, 240 120"
        fill="none" stroke="url(#strandA)" stroke-width="3.2" stroke-linecap="round" filter="url(#softGlow)"/>
  <path d="M40 120 C80 150, 120 10, 140 80 C160 150, 200 10, 240 40"
        fill="none" stroke="url(#strandB)" stroke-width="3.2" stroke-linecap="round" filter="url(#softGlow)"/>
  <g stroke="rgba(187,247,208,0.55)" stroke-width="1.4">
    <line x1="70" y1="52" x2="70" y2="108"/>
    <line x1="100" y1="38" x2="100" y2="122"/>
    <line x1="140" y1="48" x2="140" y2="112"/>
    <line x1="180" y1="38" x2="180" y2="122"/>
    <line x1="210" y1="52" x2="210" y2="108"/>
  </g>
  <circle cx="70" cy="52" r="4.2" fill="#86EFAC"/>
  <circle cx="70" cy="108" r="4.2" fill="#4ADE80"/>
  <circle cx="100" cy="38" r="4.2" fill="#BBF7D0"/>
  <circle cx="100" cy="122" r="4.2" fill="#22C55E"/>
  <circle cx="140" cy="48" r="5" fill="#ECFDF5"/>
  <circle cx="140" cy="112" r="5" fill="#86EFAC"/>
  <circle cx="180" cy="38" r="4.2" fill="#4ADE80"/>
  <circle cx="180" cy="122" r="4.2" fill="#BBF7D0"/>
  <circle cx="210" cy="52" r="4.2" fill="#22C55E"/>
  <circle cx="210" cy="108" r="4.2" fill="#86EFAC"/>
</svg>
"""

_SIDE_DNA_SVG = """
<svg viewBox="0 0 120 320" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <path d="M30 20 C55 60, 55 100, 30 140 C5 180, 5 220, 30 260 C55 290, 70 300, 90 310"
        fill="none" stroke="rgba(134,239,172,0.55)" stroke-width="2.2"/>
  <path d="M90 20 C65 60, 65 100, 90 140 C115 180, 115 220, 90 260 C65 290, 50 300, 30 310"
        fill="none" stroke="rgba(74,222,128,0.4)" stroke-width="2.2"/>
  <g stroke="rgba(187,247,208,0.35)" stroke-width="1">
    <line x1="38" y1="50" x2="82" y2="50"/>
    <line x1="38" y1="100" x2="82" y2="100"/>
    <line x1="38" y1="150" x2="82" y2="150"/>
    <line x1="38" y1="200" x2="82" y2="200"/>
    <line x1="38" y1="250" x2="82" y2="250"/>
  </g>
</svg>
"""

_LOGIN_STAGE_HTML = f"""
<div class="scamdna-login-bg" aria-hidden="true">
  <div class="grid"></div>
  <div class="radar">
    <div class="radar-rings"></div>
    <div class="radar-cross"></div>
    <div class="radar-sweep"></div>
    <span class="radar-blip b1"></span>
    <span class="radar-blip b2"></span>
    <span class="radar-blip b3"></span>
  </div>
  <div class="glow"></div>
  <div class="scamdna-side-art left">{_SIDE_DNA_SVG}</div>
  <div class="scamdna-side-art right">{_SIDE_DNA_SVG}</div>
</div>
<div class="scamdna-stage" translate="no" lang="zh-Hant">
  {_DNA_SVG}
  <div class="scamdna-mark" aria-hidden="true">
    <span class="scamdna-mark-ring"></span>
    <span class="scamdna-mark-core">S</span>
  </div>
  <div class="scamdna-brand">ScamDNA</div>
  <p class="scamdna-tagline">AI 詐騙話術進化預警系統</p>
  <div class="scamdna-pills">
    <span class="scamdna-pill">話術 DNA</span>
    <span class="scamdna-pill">進化預警</span>
    <span class="scamdna-pill">XAI 解析</span>
  </div>
</div>
"""

_LOGIN_HTML = _LOGIN_STAGE_HTML

# ── 使用者列 CSS（嵌入主頁面 header）──────────────────────────────────────────
USER_BAR_CSS = """
.user-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
}
.user-avatar {
    font-size: 1rem;
    line-height: 1;
    color: #ffffff;
}
.user-name {
    color: #ffffff;
    font-size: 0.75rem;
    font-weight: 600;
    white-space: nowrap;
}
.user-role {
    font-size: 0.65rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 12px;
    white-space: nowrap;
}
.role-admin {
    background: rgba(255,255,255,0.18);
    color: #ffffff;
    border: 1px solid rgba(255,255,255,0.35);
}
.role-analyst {
    background: rgba(255,255,255,0.14);
    color: #e0f2fe;
    border: 1px solid rgba(255,255,255,0.28);
}
.role-viewer {
    background: rgba(255,255,255,0.12);
    color: #f3f4f6;
    border: 1px solid rgba(255,255,255,0.25);
}
.user-time {
    color: rgba(255,255,255,0.7);
    font-size: 0.65rem;
    white-space: nowrap;
}
"""
