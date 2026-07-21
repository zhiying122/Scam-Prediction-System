"""
AEGIS CORE — 登入認證模組

提供 Dashboard 註冊、登入、登出功能，整合 RBAC 角色系統。
使用 Streamlit session_state 管理登入狀態。
已註冊帳號存於 session-level in-memory store（重啟後重置）。

預設帳號（Demo 用途）：
- admin / admin123 → 系統管理員（預建帳號，無需註冊）
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


# ── 登入/註冊頁面 ─────────────────────────────────────────────────────────────
def render_login_page() -> bool:
    """
    渲染登入/註冊頁面（含 tab 切換）

    Returns:
        True 如果使用者已成功登入
        False 如果尚未登入
    """
    if is_authenticated():
        return True

    # 注入專用 CSS + 背景
    st.html(_LOGIN_CSS)
    st.html(_LOGIN_HTML)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div style="height: 180px;"></div>', unsafe_allow_html=True)

        # 品牌標題
        st.markdown(
            '<p style="color:#86efac;font-weight:700;font-size:1.4rem;'
            'text-align:center;margin-bottom:2px;font-family:Orbitron,monospace;'
            'letter-spacing:3px;">AEGIS CORE</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="color:rgba(255,255,255,0.6);font-size:0.78rem;text-align:center;'
            'margin-bottom:24px;">AI 詐騙話術進化預警系統</p>',
            unsafe_allow_html=True,
        )

        # Tab 切換：登入 / 註冊
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
        submitted = st.form_submit_button("登 入", use_container_width=True, type="primary")

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

    # Demo 帳號提示
    st.markdown(
        '<div style="text-align:center;margin-top:12px;padding:10px 14px;'
        'background:rgba(240,253,244,0.95);border:1px solid #BBF7D0;border-radius:8px;">'
        '<p style="color:#166534;font-size:0.72rem;font-weight:600;margin-bottom:4px;">預設帳號</p>'
        '<p style="color:#374151;font-size:0.75rem;margin:0;">'
        '<code>admin</code> ／ <code>Aegis@2026</code></p>'
        '</div>',
        unsafe_allow_html=True,
    )


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
        reg_submitted = st.form_submit_button("註 冊", use_container_width=True, type="primary")

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

    return (
        f'<div class="user-bar">'
        f'<span class="user-avatar">{user.avatar_emoji}</span>'
        f'<span class="user-name">{user.display_name}</span>'
        f'<span class="user-role {role_badge_cls}">{user.role.value}</span>'
        f'<span class="user-time">{time_str}</span>'
        f'</div>'
    )


# ── 登入頁面 CSS ──────────────────────────────────────────────────────────────
_LOGIN_CSS = """
<style>
/* 登入頁面背景 */
.stApp {
    background: linear-gradient(135deg, #0f2419 0%, #14532d 40%, #1a3a2a 100%) !important;
}

/* 隱藏預設 Streamlit header */
header { visibility: hidden !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }

/* Tab 樣式（暗色背景上） */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.05) !important;
    border-radius: 8px !important;
    padding: 4px !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    color: rgba(255,255,255,0.6) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    border-radius: 6px !important;
    padding: 8px 24px !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(255,255,255,0.12) !important;
    color: white !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background: #22c55e !important;
}
.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

/* 表單容器 */
.stForm {
    background: rgba(255, 255, 255, 0.97) !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 14px !important;
    padding: 28px 24px !important;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 40px rgba(22, 101, 52, 0.08) !important;
}

/* 表單內輸入框 */
.stForm .stTextInput > div > div > input {
    background: #F9FAFB !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    font-size: 0.88rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stForm .stTextInput > div > div > input:focus {
    border-color: #166534 !important;
    box-shadow: 0 0 0 3px rgba(22, 101, 52, 0.1) !important;
}
.stForm .stTextInput [data-baseweb="input"] {
    background: #F9FAFB !important;
    border-color: #E5E7EB !important;
    border-radius: 8px !important;
}

/* 按鈕 */
.stForm .stButton > button[data-testid="stBaseButton-primary"],
.stForm button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #166534 0%, #14532d 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 11px !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: 4px !important;
    margin-top: 8px !important;
    box-shadow: 0 4px 12px rgba(22, 101, 52, 0.25) !important;
    transition: transform 0.1s, box-shadow 0.2s !important;
}
.stForm .stButton > button[data-testid="stBaseButton-primary"]:hover,
.stForm button[data-testid="stBaseButton-primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(22, 101, 52, 0.35) !important;
}
.stForm .stButton > button[data-testid="stBaseButton-primary"] p,
.stForm .stButton > button[data-testid="stBaseButton-primary"] span,
.stForm button[data-testid="stBaseButton-primary"] p,
.stForm button[data-testid="stBaseButton-primary"] span {
    color: white !important;
    -webkit-text-fill-color: white !important;
}

/* Label 樣式 */
.stForm label,
.stForm [data-testid="stWidgetLabel"] p {
    color: #374151 !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
}
</style>
"""

# ── 登入頁面背景裝飾 HTML ─────────────────────────────────────────────────────
_LOGIN_HTML = """
<div style="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;">
    <div style="position:absolute;top:0;left:0;width:100%;height:100%;
    background-image:
        linear-gradient(rgba(22,101,52,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(22,101,52,0.04) 1px, transparent 1px);
    background-size: 60px 60px;"></div>
    <div style="position:absolute;top:12%;right:8%;width:350px;height:350px;
    background:radial-gradient(circle, rgba(34,197,94,0.07) 0%, transparent 70%);
    border-radius:50%;"></div>
    <div style="position:absolute;bottom:15%;left:6%;width:280px;height:280px;
    background:radial-gradient(circle, rgba(22,101,52,0.05) 0%, transparent 70%);
    border-radius:50%;"></div>
</div>
"""


# ── 使用者列 CSS（嵌入主頁面 header）──────────────────────────────────────────
USER_BAR_CSS = """
.user-bar {
    display: flex;
    align-items: center;
    gap: 8px;
}
.user-avatar {
    font-size: 1.1rem;
}
.user-name {
    color: rgba(255,255,255,0.92);
    font-size: 0.75rem;
    font-weight: 600;
}
.user-role {
    font-size: 0.65rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 12px;
}
.role-admin {
    background: rgba(239,68,68,0.2);
    color: #fca5a5;
    border: 1px solid rgba(239,68,68,0.3);
}
.role-analyst {
    background: rgba(59,130,246,0.2);
    color: #93c5fd;
    border: 1px solid rgba(59,130,246,0.3);
}
.role-viewer {
    background: rgba(156,163,175,0.2);
    color: #d1d5db;
    border: 1px solid rgba(156,163,175,0.3);
}
.user-time {
    color: rgba(255,255,255,0.45);
    font-size: 0.65rem;
}
.logout-btn {
    background: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    color: rgba(255,255,255,0.8) !important;
    padding: 3px 10px !important;
    border-radius: 6px !important;
    font-size: 0.68rem !important;
    cursor: pointer !important;
    transition: background 0.15s !important;
    text-decoration: none !important;
}
.logout-btn:hover {
    background: rgba(239,68,68,0.2) !important;
    border-color: rgba(239,68,68,0.4) !important;
    color: #fca5a5 !important;
}
"""
