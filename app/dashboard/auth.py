"""
ScamDNA — 登入認證模組

提供 Dashboard 註冊、登入、登出功能，整合 RBAC 角色系統。
使用 Streamlit session_state 管理登入狀態。
已註冊帳號存於 session-level in-memory store（重啟後重置）。

預設帳號（Demo 用途，定義於 DEMO_USERNAME / DEMO_PASSWORD 常數）：
- admin / Aegis@2026 → 系統管理員（預建帳號，無需註冊）
  ※ 修改密碼請只改 DEMO_PASSWORD，並執行 tests/test_auth_dashboard.py
"""

import base64
import hashlib
import hmac
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import streamlit as st
from dotenv import load_dotenv

from app.access_controller.rbac import Role

load_dotenv()
load_dotenv(".env.local", override=True)


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


# ── Demo／內建帳號（單一來源，勿在其他檔案硬編碼）────────────────────────────
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "Aegis@2026"


def demo_credentials_hint() -> str:
    """登入頁 Demo 提示文字（僅公開 Demo 帳號，不含 .env 本機管理員）。"""
    return f"Demo · {DEMO_USERNAME} / {DEMO_PASSWORD}"


def _load_local_admin_accounts_from_env() -> dict[str, dict]:
    """
    從環境變數 DASHBOARD_LOCAL_ADMINS 載入本機管理員。

    格式（勿寫入程式碼／前端／Git）：
      帳號:密碼
      帳號:密碼:顯示名稱
    多組以逗號分隔。僅能設定於本機 .env。
    """
    raw = os.environ.get("DASHBOARD_LOCAL_ADMINS", "").strip()
    if not raw:
        return {}

    accounts: dict[str, dict] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry or entry.startswith("#"):
            continue
        parts = entry.split(":", 2)
        if len(parts) < 2:
            continue
        username = parts[0].strip().lower()
        password = parts[1]
        display_name = parts[2].strip() if len(parts) > 2 and parts[2].strip() else username
        if not username or not password:
            continue
        accounts[username] = {
            "password_hash": _hash_password(password),
            "display_name": display_name,
            "role": Role.SYSTEM_ADMIN,
            "avatar_emoji": "⬡",
            "source": "local_env",
        }
    return accounts


def _build_default_user_db() -> dict[str, dict]:
    """建立含內建管理員與 .env 本機管理員的預設使用者庫。"""
    db = {
        DEMO_USERNAME: {
            "password_hash": _hash_password(DEMO_PASSWORD),
            "display_name": "系統管理員",
            "role": Role.SYSTEM_ADMIN,
            "avatar_emoji": "⬡",
            "source": "demo",
        },
    }
    db.update(_load_local_admin_accounts_from_env())
    return db


def _sync_builtin_admin(db: dict[str, dict]) -> None:
    """內建 admin 密碼雜湊與 DEMO_PASSWORD 常數保持同步（更新常數後無需清 session）。"""
    expected_hash = _hash_password(DEMO_PASSWORD)
    if DEMO_USERNAME not in db:
        db[DEMO_USERNAME] = _build_default_user_db()[DEMO_USERNAME]
        db[DEMO_USERNAME]["source"] = "demo"
        return
    if db[DEMO_USERNAME].get("password_hash") != expected_hash:
        db[DEMO_USERNAME]["password_hash"] = expected_hash


def _sync_local_admins(db: dict[str, dict]) -> None:
    """本機 .env 管理員與 DASHBOARD_LOCAL_ADMINS 保持同步。"""
    env_accounts = _load_local_admin_accounts_from_env()
    env_usernames = set(env_accounts.keys())

    for username in list(db.keys()):
        if db[username].get("source") == "local_env" and username not in env_usernames:
            del db[username]

    for username, data in env_accounts.items():
        db[username] = data


# ── 使用者資料庫（in-memory，存在 session_state 確保跨 rerun 持久）────────────
def _get_user_db() -> dict[str, dict]:
    """取得使用者資料庫（首次存取時初始化預設帳號）"""
    if "_user_db" not in st.session_state:
        st.session_state["_user_db"] = _build_default_user_db()
    else:
        _sync_builtin_admin(st.session_state["_user_db"])
        _sync_local_admins(st.session_state["_user_db"])
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
    """將使用者資訊寫入 session_state，並標記需寫入瀏覽器 cookie。"""
    st.session_state["authenticated"] = True
    st.session_state["user"] = user
    st.session_state["login_time"] = datetime.now()
    st.session_state["_pending_auth_cookie"] = user.username
    st.session_state["_auth_session_live"] = True
    # 登入當輪為 Streamlit rerun，勿被 refresh guard 誤判為重新輸入網址
    st.session_state["_skip_browser_refresh_logout"] = True
    st.session_state.pop("_block_cookie_restore", None)
    st.session_state.pop("_clear_auth_cookie", None)


def logout() -> None:
    """清除登入狀態與瀏覽器 cookie。"""
    st.session_state["authenticated"] = False
    st.session_state.pop("user", None)
    st.session_state.pop("login_time", None)
    st.session_state.pop("_pending_auth_cookie", None)
    st.session_state.pop("_auth_cookie_ok", None)
    st.session_state.pop("_skip_browser_refresh_logout", None)
    st.session_state.pop("_auth_session_live", None)
    st.session_state["_clear_auth_cookie"] = True
    st.session_state["_block_cookie_restore"] = True


def is_authenticated() -> bool:
    """檢查是否已登入"""
    return bool(st.session_state.get("authenticated", False))


# ── 登入 cookie + 站內導覽 token（嚴格閘門）────────────────────────────────
# cookie：僅在「帶有效 _nav」的站內連結整頁導向時還原登入
# 直接輸入網址／F5／無 _nav → 一律登入頁（禁止靠 cookie 偷渡）
_AUTH_COOKIE_NAME = "scamdna_auth"
_FORCE_LOGOUT_COOKIE = "scamdna_force_logout"
_AUTH_MAX_AGE_SEC = 60 * 60 * 12  # 12 小時
_REFRESH_LOGOUT_PARAM = "_refresh_logout"
_NAV_PARAM = "_nav"
_NAV_MAX_AGE_SEC = 5 * 60  # 站內導覽 token 5 分鐘


def _auth_secret() -> str:
    return os.environ.get("DASHBOARD_AUTH_SECRET") or DEMO_PASSWORD


def _make_auth_token(username: str) -> str:
    ts = str(int(time.time()))
    msg = f"{username.strip().lower()}:{ts}"
    sig = hmac.new(
        _auth_secret().encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return base64.urlsafe_b64encode(f"{msg}:{sig}".encode("utf-8")).decode("ascii")


def _parse_auth_token(token: str) -> Optional[str]:
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        username, ts, sig = raw.rsplit(":", 2)
        msg = f"{username}:{ts}"
        expected = hmac.new(
            _auth_secret().encode("utf-8"),
            msg.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(time.time()) - int(ts) > _AUTH_MAX_AGE_SEC:
            return None
        return username
    except Exception:
        return None


def _make_nav_token(username: str) -> str:
    """短效站內導覽憑證：僅允許帶此參數的連結還原登入。"""
    ts = str(int(time.time()))
    msg = f"nav:{username.strip().lower()}:{ts}"
    sig = hmac.new(
        _auth_secret().encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]
    return base64.urlsafe_b64encode(f"{msg}:{sig}".encode("utf-8")).decode("ascii")


def _parse_nav_token(token: str) -> Optional[str]:
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        prefix, username, ts, sig = raw.rsplit(":", 3)
        if prefix != "nav":
            return None
        msg = f"nav:{username}:{ts}"
        expected = hmac.new(
            _auth_secret().encode("utf-8"),
            msg.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()[:32]
        if not hmac.compare_digest(sig, expected):
            return None
        if int(time.time()) - int(ts) > _NAV_MAX_AGE_SEC:
            return None
        return username
    except Exception:
        return None


def build_page_href(page_key: str) -> str:
    """產生帶 _nav 憑證的站內連結（無登入者則僅 page 參數）。"""
    user = get_current_user()
    if user is None:
        return f"?page={page_key}"
    token = _make_nav_token(user.username)
    return f"?page={page_key}&{_NAV_PARAM}={token}"


def _strip_nav_param_from_url() -> None:
    """還原登入後立刻移除 _nav，避免 F5 重放憑證。"""
    if _NAV_PARAM not in st.query_params:
        return
    retained = {k: v for k, v in st.query_params.items() if k != _NAV_PARAM}
    st.query_params.clear()
    for key, value in retained.items():
        st.query_params[key] = value


def _profile_from_username(username: str) -> Optional[UserProfile]:
    db = _get_user_db()
    user_data = db.get(username.strip().lower())
    if user_data is None:
        return None
    return UserProfile(
        username=username.strip().lower(),
        display_name=user_data["display_name"],
        role=user_data["role"],
        avatar_emoji=user_data["avatar_emoji"],
        last_login=datetime.now(),
    )


def _inject_cookie_script(*, clear: bool = False, username: str | None = None) -> None:
    """透過 JS 寫入／清除頂層文件 cookie（導覽 <a href> 整頁載入後仍可讀取）。"""
    import streamlit.components.v1 as components

    if clear:
        script = f"""
        <script>
        (function () {{
          const names = ["{_AUTH_COOKIE_NAME}", "{_FORCE_LOGOUT_COOKIE}"];
          names.forEach(function (name) {{
            const cleared = name + "=; path=/; max-age=0; SameSite=Lax";
            try {{ window.top.document.cookie = cleared; }} catch (e) {{ document.cookie = cleared; }}
          }});
        }})();
        </script>
        """
    else:
        token = _make_auth_token(username or "")
        script = f"""
        <script>
        (function () {{
          const name = "{_AUTH_COOKIE_NAME}";
          const value = encodeURIComponent("{token}");
          const maxAge = {_AUTH_MAX_AGE_SEC};
          const cookie = name + "=" + value + "; path=/; max-age=" + maxAge + "; SameSite=Lax";
          try {{ window.top.document.cookie = cookie; }} catch (e) {{ document.cookie = cookie; }}
        }})();
        </script>
        """
    components.html(script, height=0, width=0)


def sync_auth_cookies() -> None:
    """處理登入後寫入／登出後清除 cookie。"""
    if st.session_state.pop("_clear_auth_cookie", False):
        _inject_cookie_script(clear=True)
        return
    pending = st.session_state.pop("_pending_auth_cookie", None)
    if pending:
        _inject_cookie_script(username=pending)
        return
    # 已登入時定期延長 cookie，避免導覽後遺失
    if is_authenticated():
        user = get_current_user()
        if user is not None and not st.session_state.get("_auth_cookie_ok"):
            _inject_cookie_script(username=user.username)
            st.session_state["_auth_cookie_ok"] = True


def try_restore_session_from_cookie() -> bool:
    """
    從瀏覽器 cookie 還原登入。

    僅應在站內連結帶有效 _nav 時呼叫；禁止在直接輸入網址時呼叫。
    """
    if is_authenticated():
        return True
    if st.session_state.get("_block_cookie_restore"):
        return False
    try:
        token = st.context.cookies.get(_AUTH_COOKIE_NAME)
    except Exception:
        token = None
    if not token:
        return False
    username = _parse_auth_token(token)
    if not username:
        return False
    user = _profile_from_username(username)
    if user is None:
        return False
    st.session_state["authenticated"] = True
    st.session_state["user"] = user
    st.session_state["login_time"] = datetime.now()
    st.session_state["_auth_cookie_ok"] = True
    st.session_state["_auth_session_live"] = True
    return True


def _consume_force_logout_cookie() -> bool:
    """若瀏覽器帶有 force-logout cookie，清除並回傳 True。"""
    try:
        flag = st.context.cookies.get(_FORCE_LOGOUT_COOKIE)
    except Exception:
        flag = None
    if flag != "1":
        return False
    # 請前端清掉（隨 sync / logout 一併清）
    st.session_state["_clear_auth_cookie"] = True
    return True


def handle_browser_refresh_logout() -> bool:
    """
    處理 F5 / Ctrl+Shift+R 帶入的 _refresh_logout=1。

    Returns:
        True 表示本次應強制登出並顯示登入頁（不再 rerun，避免 cookie 競態還原）。
    """
    if st.query_params.get(_REFRESH_LOGOUT_PARAM) == "1":
        logout()
        st.query_params.clear()
        return True
    return False


def enforce_login_gate() -> bool:
    """
    嚴格登入閘門（單一入口）。

    Returns:
        True  → 呼叫端應顯示登入頁並 st.stop()
        False → 已通過認證，可繼續渲染 Dashboard
    """
    if handle_browser_refresh_logout():
        return True

    if st.query_params.get("logout") == "1":
        logout()
        st.query_params.clear()
        return True

    if _consume_force_logout_cookie():
        logout()
        return True

    # 登出後殘留旗標：禁止任何還原
    if st.session_state.get("_block_cookie_restore") and not is_authenticated():
        return True

    nav_raw = st.query_params.get(_NAV_PARAM)
    nav_user = _parse_nav_token(nav_raw) if nav_raw else None

    if nav_user:
        # 站內 ?page=&_nav= 導覽：允許 cookie 還原
        if not is_authenticated():
            try_restore_session_from_cookie()
        user = get_current_user()
        if user is not None and user.username == nav_user:
            st.session_state["_auth_session_live"] = True
            st.session_state.pop("_block_cookie_restore", None)
            # 本輪為站內導覽落地，禁止 refresh guard 立刻再登出
            st.session_state["_skip_browser_refresh_logout"] = True
            _strip_nav_param_from_url()
            return False
        logout()
        return True

    # 無有效 _nav：禁止靠 cookie 還原
    if is_authenticated() and st.session_state.get("_auth_session_live"):
        # 同一 Streamlit session 內的 widget rerun（登入後操作）→ 放行
        # F5 若重用 session，交由 refresh guard（force-logout cookie / meta refresh）處理
        return False

    # 直接輸入網址／新分頁／新 session：一律登入頁，並清掉殘留 cookie
    if is_authenticated():
        logout()
    else:
        st.session_state["_clear_auth_cookie"] = True
        st.session_state["_block_cookie_restore"] = True
    return True


def install_browser_refresh_guard() -> None:
    """
    注入 JS：F5 / Ctrl+Shift+R / 重新輸入網址 → 寫 force-logout cookie，
    並以父頁 meta refresh／連結點擊導向 _refresh_logout=1。

    站內 ?page=&_nav= 連結不觸發。
    components.html 在沙箱 iframe 內，top.location 可能被擋，故改操父文件。
    """
    import streamlit.components.v1 as components

    param = _REFRESH_LOGOUT_PARAM
    auth_cookie = _AUTH_COOKIE_NAME
    force_cookie = _FORCE_LOGOUT_COOKIE
    intent_key = "scamdna_inapp_nav"
    handled_key = "scamdna_guard_handled"
    skip_logout = "true" if st.session_state.pop("_skip_browser_refresh_logout", False) else "false"

    components.html(
        f"""
        <script>
        (function () {{
            function topWin() {{
                try {{ return window.top; }} catch (e) {{
                    try {{ return window.parent; }} catch (e2) {{ return null; }}
                }}
            }}
            const top = topWin();
            if (!top) return;

            function setCookie(name, value, maxAge) {{
                const c = name + "=" + value + "; path=/; max-age=" + maxAge + "; SameSite=Lax";
                try {{ top.document.cookie = c; }} catch (e) {{
                    try {{ document.cookie = c; }} catch (e2) {{}}
                }}
            }}

            function hookInAppNavClicks() {{
                try {{
                    if (top.__scamdnaNavHooked) return;
                    top.__scamdnaNavHooked = true;
                    top.document.addEventListener("click", function (ev) {{
                        const el = ev.target;
                        if (!el || !el.closest) return;
                        const a = el.closest("a[href]");
                        if (!a) return;
                        const href = a.getAttribute("href") || "";
                        if (href.indexOf("logout=") !== -1) return;
                        if (href.indexOf("page=") === -1) return;
                        try {{ top.sessionStorage.setItem("{intent_key}", "1"); }} catch (e) {{}}
                    }}, true);
                }} catch (e) {{}}
            }}

            function navEntry() {{
                try {{
                    return top.performance.getEntriesByType("navigation")[0] || null;
                }} catch (e) {{
                    return null;
                }}
            }}

            function loadId() {{
                const nav = navEntry();
                if (nav) return String(nav.type) + "@" + String(Math.floor(nav.startTime || 0));
                try {{
                    if (top.performance.navigation) {{
                        return "legacy@" + String(top.performance.navigation.type);
                    }}
                }} catch (e) {{}}
                return "unknown";
            }}

            function isReload() {{
                try {{
                    const nav = navEntry();
                    if (nav && nav.type === "reload") return true;
                }} catch (e) {{}}
                try {{
                    if (top.performance.navigation && top.performance.navigation.type === 1) {{
                        return true;
                    }}
                }} catch (e) {{}}
                return false;
            }}

            function consumeInAppIntent() {{
                try {{
                    if (top.sessionStorage.getItem("{intent_key}") === "1") {{
                        top.sessionStorage.removeItem("{intent_key}");
                        return true;
                    }}
                }} catch (e) {{}}
                return false;
            }}

            function forceParentLogoutRedirect() {{
                let loc;
                try {{ loc = top.location; }} catch (e) {{ return; }}
                if (!loc) return;
                const url = new URL(loc.href);
                if (url.searchParams.get("{param}") === "1") return;
                url.searchParams.set("{param}", "1");
                url.searchParams.delete("page");
                url.searchParams.delete("{_NAV_PARAM}");
                const target = url.toString();

                // 1) 父文件 meta refresh（不受 iframe sandbox top-navigation 限制）
                try {{
                    const meta = top.document.createElement("meta");
                    meta.httpEquiv = "refresh";
                    meta.content = "0;url=" + target;
                    top.document.head.appendChild(meta);
                }} catch (e) {{}}

                // 2) 父文件隱藏連結 click
                try {{
                    const a = top.document.createElement("a");
                    a.href = target;
                    a.style.display = "none";
                    top.document.body.appendChild(a);
                    a.click();
                }} catch (e) {{}}

                // 3) 直接改 location（部分環境仍可用）
                try {{ loc.replace(target); }} catch (e) {{}}
            }}

            hookInAppNavClicks();

            const id = loadId();
            try {{
                if (top.sessionStorage.getItem("{handled_key}") === id) {{
                    return;
                }}
            }} catch (e) {{}}

            const skipLogout = {skip_logout};
            const inApp = consumeInAppIntent();
            const mustLogout = (!skipLogout) && (isReload() || !inApp);

            try {{ top.sessionStorage.setItem("{handled_key}", id); }} catch (e) {{}}

            if (!mustLogout) return;

            setCookie("{force_cookie}", "1", 60);
            setCookie("{auth_cookie}", "", 0);
            forceParentLogoutRedirect();
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def get_current_user() -> Optional[UserProfile]:
    """取得目前登入的使用者"""
    if not is_authenticated():
        return None
    return st.session_state.get("user")


# ── 登入/註冊頁面（Forest Gate）───────────────────────────────────────────────
def render_login_page() -> bool:
    """
    渲染登入/註冊頁面（Forest Narrative：左 6 敘事牆／右 4 表單）

    Returns:
        True 如果使用者已成功登入
        False 如果尚未登入
    """
    if is_authenticated():
        return True

    # 左牆＋關鍵 layout 寫入父頁，避免被捲進 Streamlit 右欄造成重疊異狀
    _inject_login_shell()
    st.html(_LOGIN_CSS)
    st.html(_LOGIN_PANEL_HEAD_HTML)

    tab_login, tab_register = st.tabs(["登入", "註冊"])

    with tab_login:
        _render_login_form()

    with tab_register:
        _render_register_form()

    return False


# 父頁注入：完整左牆 HTML + layout／框線 CSS（繞過 st.html DOMPurify）
_LOGIN_PARENT_CSS = """
.stApp {
  --ink: #15261c;
  --muted: #5b6b61;
  --forest: #166534;
  --forest-deep: #124a2b;
  --paper: #f6f7f4;
  --split-left: 60%;
  --split-right: 40%;
  background: #eef1ec !important;
  overflow-x: hidden !important;
}
header, [data-testid="stHeader"], .stAppHeader,
[data-testid="stToolbar"], .stAppToolbar, [data-testid="stDecoration"],
#MainMenu, footer, [data-testid="stSidebar"], [data-testid="collapsedControl"] {
  display: none !important;
  height: 0 !important;
  min-height: 0 !important;
}
.main .block-container,
div[data-testid="stMainBlockContainer"] {
  position: relative !important;
  z-index: 5 !important;
  margin-left: 60% !important;
  width: 40% !important;
  max-width: 40% !important;
  min-height: 100vh !important;
  height: 100vh !important;
  padding: 1.5rem 1.25rem !important;
  box-sizing: border-box !important;
  background: #eef1ec !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  align-items: center !important;
  overflow: auto !important;
}
.main .block-container > div,
div[data-testid="stMainBlockContainer"] > div {
  width: 100% !important;
  max-width: 340px !important;
  margin: 0 auto !important;
  flex: 0 0 auto !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: stretch !important;
}
section[data-testid="stMain"] div[data-testid="stVerticalBlock"]:has(.scamdna-panel-head),
section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.scamdna-panel-head) {
  background: #ffffff !important;
  border: 1.5px solid #166534 !important;
  border-radius: 14px !important;
  padding: 1.1rem 1.2rem 1.15rem !important;
  box-sizing: border-box !important;
  box-shadow: 0 10px 28px rgba(22,101,52,0.10) !important;
  max-width: 320px !important;
  width: 100% !important;
  margin: 0 auto !important;
  text-align: left !important;
  gap: 0.2rem !important;
  animation: scamdnaEmbedIn 0.55s ease-out both !important;
}
/* 卡片內、標題上方的空 iframe／style 殼層壓扁 */
section[data-testid="stMain"] div[data-testid="stVerticalBlock"]:has(.scamdna-panel-head) > div:not(:has(.scamdna-panel-head)):not(:has(.stTabs)):not(:has(.stForm)):not(:has([data-testid="stForm"])) {
  height: 0 !important;
  min-height: 0 !important;
  max-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  border: none !important;
}
.scamdna-panel-head {
  margin: 0 0 0.1rem !important;
  padding: 0 !important;
}
.stTabs {
  margin-top: 0.15rem !important;
  width: 100% !important;
}
.stTabs [data-baseweb="tab-list"] {
  justify-content: flex-start !important;
  padding-left: 0 !important;
  margin-left: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  padding: 8px 14px 8px 0 !important;
}
.stTabs [data-baseweb="tab-panel"] {
  padding-top: 0.35rem !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
}
.stTabs, .stForm, .stForm label, .stForm .stTextInput {
  text-align: left !important;
  width: 100% !important;
  margin-left: 0 !important;
  padding-left: 0 !important;
}
div[data-testid="stForm"], .stForm {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  box-shadow: none !important;
  width: 100% !important;
  max-width: 100% !important;
  margin: 0 !important;
}
/* 隱藏 Press Enter to submit form 浮層 */
[data-testid="InputInstructions"],
.stForm [data-testid="InputInstructions"],
div[data-testid="stTextInput"] [data-testid="InputInstructions"] {
  display: none !important;
  visibility: hidden !important;
  width: 0 !important;
  height: 0 !important;
  overflow: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
}
.stForm .stTextInput,
.stForm [data-testid="stWidgetLabel"],
.stForm [data-testid="stFormSubmitButton"],
.stForm [data-testid="stFormSubmitButton"] > button,
.stForm [data-testid="stElementContainer"],
.stForm [data-testid="element-container"] {
  width: 100% !important;
  max-width: 100% !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
}
.stForm .stTextInput > div:last-child,
.stForm .stTextInput [data-baseweb="input"],
.stForm .stTextInput [data-baseweb="base-input"] {
  width: 100% !important;
  margin-left: 0 !important;
  background: #ffffff !important;
  border: 1.5px solid #9CA3AF !important;
  border-radius: 8px !important;
  box-shadow: inset 0 0 0 1px #9CA3AF !important;
  min-height: 40px !important;
  box-sizing: border-box !important;
}
.stForm .stTextInput > div:last-child:focus-within,
.stForm .stTextInput [data-baseweb="input"]:focus-within,
.stForm .stTextInput [data-baseweb="base-input"]:focus-within {
  border-color: #166534 !important;
  box-shadow: inset 0 0 0 1px #166534, 0 0 0 3px rgba(22,101,52,0.12) !important;
}
.stForm .stTextInput input {
  border: none !important;
  box-shadow: none !important;
  background: #ffffff !important;
  color: #15261c !important;
  text-align: left !important;
  width: 100% !important;
}
.stForm .stTextInput button {
  display: none !important;
}
.stForm [data-testid="stFormSubmitButton"] > button {
  background: #166534 !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 8px !important;
  width: 100% !important;
  margin-left: 0 !important;
}
#scamdna-login-left.scamdna-split-left,
.scamdna-split-left {
  position: fixed !important;
  left: 0 !important;
  top: 0 !important;
  width: 60% !important;
  height: 100vh !important;
  z-index: 2 !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  padding: clamp(2.2rem, 5.5vh, 4rem) clamp(2rem, 4.8vw, 4.25rem) !important;
  box-sizing: border-box !important;
  overflow: hidden !important;
  background:
    radial-gradient(ellipse 65% 50% at 12% 18%, rgba(187,247,208,0.20), transparent 55%),
    radial-gradient(ellipse 50% 42% at 92% 82%, rgba(15,47,31,0.55), transparent 58%),
    linear-gradient(155deg, #1c5537 0%, #14532d 46%, #0d281c 100%) !important;
  color: #f0fdf4 !important;
  line-height: normal !important;
  animation: scamdnaEmbedIn 0.55s ease-out both !important;
}
.scamdna-split-left .content {
  position: relative !important;
  z-index: 1 !important;
  max-width: 440px !important;
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  text-align: left !important;
}
.scamdna-eyebrow {
  margin: 0 0 0.85rem !important;
  color: rgba(187,247,208,0.78) !important;
  font-family: Manrope, "Noto Sans TC", sans-serif !important;
  font-size: 0.72rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.18em !important;
  text-transform: uppercase !important;
}
.scamdna-brand {
  margin: 0 !important;
  color: #f7fef9 !important;
  font-family: Manrope, "Noto Sans TC", sans-serif !important;
  font-size: clamp(2.55rem, 4.6vw, 3.55rem) !important;
  font-weight: 800 !important;
  letter-spacing: 0.04em !important;
  line-height: 1.02 !important;
}
.scamdna-rule {
  width: 48px !important;
  height: 2px !important;
  margin: 1.1rem 0 0 !important;
  background: #86efac !important;
  border-radius: 1px !important;
}
.scamdna-tagline {
  margin: 1rem 0 0 !important;
  color: rgba(220,252,231,0.72) !important;
  font-size: 0.9rem !important;
  font-weight: 500 !important;
  line-height: 1.7 !important;
  max-width: 26em !important;
  text-align: left !important;
}
.scamdna-points {
  display: flex !important;
  flex-direction: column !important;
  gap: 0.75rem !important;
  width: 100% !important;
  max-width: 26em !important;
  margin: 1.75rem 0 0 0 !important;
  padding: 0 !important;
}
.scamdna-points .scamdna-point {
  display: block !important;
  width: 100% !important;
  box-sizing: border-box !important;
  margin: 0 !important;
  padding: 0.75rem 0.95rem !important;
  border: 1px solid rgba(187,247,208,0.14) !important;
  border-radius: 10px !important;
  background: rgba(255,255,255,0.04) !important;
  text-align: left !important;
}
.scamdna-points .label {
  display: block !important;
  color: #ecfdf5 !important;
  font-size: 0.92rem !important;
  font-weight: 600 !important;
}
.scamdna-points .desc {
  display: block !important;
  margin-top: 0.28rem !important;
  color: rgba(220,252,231,0.62) !important;
  font-size: 0.78rem !important;
}
.scamdna-split-left .grain,
.scamdna-split-left .canopy,
.scamdna-split-left .mist,
.scamdna-split-left .orbit {
  pointer-events: none !important;
  position: absolute !important;
}
.scamdna-split-left .grain {
  inset: 0 !important;
  opacity: 0.32 !important;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/%3E%3C/svg%3E") !important;
  background-size: 160px 160px !important;
  mix-blend-mode: soft-light !important;
}
.scamdna-split-left .canopy {
  inset: -12% -8% auto -8% !important;
  height: 52% !important;
  background:
    radial-gradient(ellipse 42% 70% at 12% 100%, rgba(34,197,94,0.16), transparent 70%),
    radial-gradient(ellipse 36% 65% at 48% 110%, rgba(134,239,172,0.12), transparent 72%),
    radial-gradient(ellipse 40% 70% at 86% 100%, rgba(22,101,52,0.20), transparent 70%) !important;
}
.scamdna-split-left .mist {
  left: -8% !important;
  bottom: -18% !important;
  width: 70% !important;
  height: 55% !important;
  background: radial-gradient(ellipse at 40% 40%, rgba(236,253,245,0.09), transparent 68%) !important;
}
.scamdna-split-left .orbit {
  right: -18% !important;
  top: 50% !important;
  width: min(58vw, 520px) !important;
  aspect-ratio: 1 !important;
  transform: translateY(-50%) !important;
  border-radius: 50% !important;
  border: 1px solid rgba(187,247,208,0.14) !important;
  box-shadow: inset 0 0 0 56px rgba(187,247,208,0.03), inset 0 0 0 112px rgba(187,247,208,0.025) !important;
}
@keyframes scamdnaEmbedIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@media (max-width: 900px) {
  #scamdna-login-left.scamdna-split-left,
  .scamdna-split-left {
    position: relative !important;
    width: 100% !important;
    height: auto !important;
    min-height: 280px !important;
  }
  .main .block-container,
  div[data-testid="stMainBlockContainer"] {
    margin-left: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    height: auto !important;
    min-height: auto !important;
  }
}
"""

_LOGIN_LEFT_HTML = """
<aside id="scamdna-login-left" class="scamdna-split-left" translate="no" lang="zh-Hant">
  <div class="grain" aria-hidden="true"></div>
  <div class="canopy" aria-hidden="true"></div>
  <div class="mist" aria-hidden="true"></div>
  <div class="orbit" aria-hidden="true"></div>
  <div class="content">
    <div class="scamdna-eyebrow">AI Prediction System</div>
    <div class="scamdna-brand">ScamDNA</div>
    <div class="scamdna-rule" aria-hidden="true"></div>
    <p class="scamdna-tagline">AI 詐騙話術進化預警系統，在新型詐騙大規模爆發前，提前看見風險。</p>
    <div class="scamdna-points">
      <div class="scamdna-point">
        <span class="label">話術裂變生成</span>
        <span class="desc">以 LLM 逆向模擬詐騙變種話術</span>
      </div>
      <div class="scamdna-point">
        <span class="label">XAI 可解釋分析</span>
        <span class="desc">標示心理操控片段，判斷有依據</span>
      </div>
      <div class="scamdna-point">
        <span class="label">異常偵測預警</span>
        <span class="desc">每日追蹤新興趨勢與風險訊號</span>
      </div>
    </div>
  </div>
</aside>
"""


def _inject_login_shell() -> None:
    """把左牆與關鍵 CSS 寫進父頁 body/head（完全脫離 Streamlit 排版樹）。"""
    import streamlit.components.v1 as components

    css = _LOGIN_PARENT_CSS.replace("\\", "\\\\").replace("`", "\\`")
    html = (
        _LOGIN_LEFT_HTML.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("</", "<\\/")
    )
    components.html(
        f"""
        <script>
        (function () {{
          let doc;
          try {{ doc = window.top.document; }} catch (e) {{
            try {{ doc = window.parent.document; }} catch (e2) {{ return; }}
          }}
          if (!doc || !doc.head || !doc.body) return;

          const cssId = "scamdna-login-parent-css";
          let style = doc.getElementById(cssId);
          if (!style) {{
            style = doc.createElement("style");
            style.id = cssId;
            doc.head.appendChild(style);
          }}
          style.textContent = `{css}`;

          const old = doc.getElementById("scamdna-login-left");
          if (old) old.remove();
          const wrap = doc.createElement("div");
          wrap.innerHTML = `{html}`;
          const panel = wrap.firstElementChild;
          if (panel) doc.body.appendChild(panel);

          function collapseCardTopGap() {{
            const head = doc.querySelector(".scamdna-panel-head");
            if (!head) return;
            let node = head;
            while (node && node.parentElement) {{
              const parent = node.parentElement;
              const kids = Array.from(parent.children || []);
              const idx = kids.indexOf(node);
              for (let i = 0; i < idx; i++) {{
                const prev = kids[i];
                if (!prev) continue;
                const text = (prev.innerText || "").trim();
                const hasUseful = prev.querySelector && (
                  prev.querySelector(".stTabs") ||
                  prev.querySelector(".stForm") ||
                  prev.querySelector('[data-testid="stForm"]') ||
                  prev.querySelector(".scamdna-panel-head")
                );
                if (!hasUseful && (!text || prev.querySelector("iframe, style"))) {{
                  prev.style.setProperty("height", "0", "important");
                  prev.style.setProperty("min-height", "0", "important");
                  prev.style.setProperty("max-height", "0", "important");
                  prev.style.setProperty("margin", "0", "important");
                  prev.style.setProperty("padding", "0", "important");
                  prev.style.setProperty("overflow", "hidden", "important");
                  prev.style.setProperty("border", "none", "important");
                }}
              }}
              const tid = parent.getAttribute && parent.getAttribute("data-testid");
              if (tid === "stVerticalBlock" || tid === "stVerticalBlockBorderWrapper") break;
              node = parent;
            }}
            doc.querySelectorAll('[data-testid="InputInstructions"]').forEach(function (el) {{
              el.style.setProperty("display", "none", "important");
              el.style.setProperty("visibility", "hidden", "important");
            }});
          }}
          collapseCardTopGap();
          setTimeout(collapseCardTopGap, 50);
          setTimeout(collapseCardTopGap, 200);
          setTimeout(collapseCardTopGap, 500);
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def clear_login_shell() -> None:
    """登入成功後移除父頁左牆與登入專用 CSS，並恢復頁面可捲動。"""
    import streamlit.components.v1 as components

    components.html(
        """
        <script>
        (function () {
          let doc;
          try { doc = window.top.document; } catch (e) {
            try { doc = window.parent.document; } catch (e2) { return; }
          }
          if (!doc) return;
          const panel = doc.getElementById("scamdna-login-left");
          if (panel) panel.remove();
          const style = doc.getElementById("scamdna-login-parent-css");
          if (style) style.remove();

          // 登入頁曾鎖住 overflow / 100vh，這裡強制恢復 Dashboard 可下拉
          const unlock = doc.getElementById("scamdna-scroll-unlock-css");
          const cssText = `
            html, body, .stApp {
              overflow: visible !important;
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
              overflow: visible !important;
              overflow-y: visible !important;
              height: auto !important;
              max-height: none !important;
              min-height: 0 !important;
            }
            .stApp, [data-testid="stAppViewContainer"] {
              min-height: 100vh !important;
            }
          `;
          let el = unlock;
          if (!el) {
            el = doc.createElement("style");
            el.id = "scamdna-scroll-unlock-css";
            doc.head.appendChild(el);
          }
          el.textContent = cssText;

          [doc.documentElement, doc.body].forEach(function (n) {
            if (!n || !n.style) return;
            n.style.removeProperty("overflow");
            n.style.removeProperty("overflow-x");
            n.style.removeProperty("overflow-y");
            n.style.removeProperty("height");
            n.style.removeProperty("max-height");
            n.style.setProperty("overflow-y", "auto", "important");
            n.style.setProperty("height", "auto", "important");
          });

          // 清掉登入頁對主容器的 60%/100vh 佈局殘留
          doc.querySelectorAll(
            '.main .block-container, div[data-testid="stMainBlockContainer"], .stMainBlockContainer'
          ).forEach(function (m) {
            if (!m || !m.style) return;
            ["height", "min-height", "max-height", "overflow", "margin-left",
             "width", "max-width", "display", "justify-content", "align-items"].forEach(function (p) {
              m.style.removeProperty(p);
            });
            m.style.setProperty("height", "auto", "important");
            m.style.setProperty("max-height", "none", "important");
            m.style.setProperty("overflow-x", "hidden", "important");
            m.style.setProperty("overflow-y", "visible", "important");
            m.style.setProperty("margin-left", "auto", "important");
            m.style.setProperty("margin-right", "auto", "important");
            m.style.setProperty("width", "100%", "important");
            m.style.setProperty("max-width", "1400px", "important");
            m.style.setProperty("padding-left", "32px", "important");
            m.style.setProperty("padding-right", "32px", "important");
            m.style.setProperty("box-sizing", "border-box", "important");
          });
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def _render_login_form() -> None:
    """渲染登入表單"""
    with st.form("login_form", clear_on_submit=False, border=False):
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
                else:
                    login(user)
                    st.rerun()


def _render_register_form() -> None:
    """渲染註冊表單"""
    with st.form("register_form", clear_on_submit=False, border=False):
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
def _labels_redundant(name: str, role_label: str) -> bool:
    """顯示名稱與角色標籤是否實質重複（避免頂欄出現兩個近義身分）。"""
    a = (name or "").strip()
    b = (role_label or "").strip()
    if not a or a == b:
        return True
    # 近義／錯字：系統管理師 ↔ 系統管理員
    if a.replace("師", "員") == b or b.replace("師", "員") == a:
        return True
    if a in b or b in a:
        return True
    return False


def render_user_bar() -> str:
    """生成頂部使用者資訊 HTML（身分標籤只顯示一個，不顯示空洞頭像符號）。"""
    user = get_current_user()
    if user is None:
        return ""

    role_badge_cls = {
        Role.SYSTEM_ADMIN: "role-admin",
        Role.SCAM_ANALYST: "role-analyst",
        Role.GENERAL_OPERATOR: "role-viewer",
        Role.EXTERNAL_CLIENT: "role-viewer",
    }.get(user.role, "role-viewer")

    name_label = (user.display_name or user.username).strip()
    role_label = user.role.value.strip()

    parts = ['<div class="user-bar" translate="no">']
    if _labels_redundant(name_label, role_label):
        parts.append(f'<span class="user-role {role_badge_cls}">{role_label}</span>')
    else:
        parts.append(f'<span class="user-name">{name_label}</span>')
        parts.append(f'<span class="user-role {role_badge_cls}">{role_label}</span>')
    parts.append("</div>")
    return "".join(parts)


# ── 登入頁面 CSS — Forest Narrative（左 6／右 4）─────────────────────────────
_LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Noto+Sans+TC:wght@400;500;600;700&display=swap');

.stApp {
    --ink: #15261c;
    --muted: #5b6b61;
    --forest: #166534;
    --forest-deep: #124a2b;
    --paper: #f6f7f4;
    --panel: #ffffff;
    --line: #d5ddd6;
    --split-left: 60%;
    --split-right: 40%;
    background: #eef1ec !important;
    font-family: 'Noto Sans TC', 'Manrope', sans-serif !important;
    color: var(--ink) !important;
    margin-top: 0 !important;
    padding-top: 0 !important;
}
header, .stAppHeader, #MainMenu, footer {
    display: none !important;
    height: 0 !important;
}
[data-testid="stSidebar"] { display: none !important; }

/* 右欄置中（詳細 layout 以父頁 CSS 為準） */
.main .block-container {
    position: relative !important;
    z-index: 5 !important;
    margin-left: 60% !important;
    width: 40% !important;
    max-width: 40% !important;
    min-height: 100vh !important;
    padding: 1.5rem 1.25rem !important;
    box-sizing: border-box !important;
    background: #eef1ec !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
}
.main .block-container > div {
    width: 100% !important;
    max-width: 340px !important;
    margin: 0 auto !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
}

/* 登入卡片 */
.scamdna-panel-head {
    position: relative;
    z-index: 1;
    margin: 0 0 0.1rem !important;
    padding: 0 !important;
    text-align: center;
}
.scamdna-panel-title {
    margin: 0;
    color: var(--ink);
    font-family: 'Manrope', 'Noto Sans TC', sans-serif;
    font-size: 1.28rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    line-height: 1.25;
}
.scamdna-panel-sub {
    margin: 0.35rem 0 0;
    color: var(--muted);
    font-size: 0.84rem;
    font-weight: 500;
    line-height: 1.45;
}

/* Tabs：左對齊，與表單同緣 */
.stTabs { margin-top: 0.15rem !important; width: 100% !important; }
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 0.35rem !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--line) !important;
    gap: 0 !important;
    justify-content: flex-start !important;
    padding-left: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    padding: 8px 14px 8px 0 !important;
    background: transparent !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
}
.stTabs [aria-selected="false"],
.stTabs [aria-selected="false"] * {
    color: var(--muted) !important;
    -webkit-text-fill-color: var(--muted) !important;
}
.stTabs [aria-selected="true"],
.stTabs [aria-selected="true"] * {
    color: var(--forest) !important;
    -webkit-text-fill-color: var(--forest) !important;
    font-weight: 700 !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background: var(--forest) !important;
    height: 2px !important;
}
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* 表單：全寬左對齊 */
.stForm {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    box-shadow: none !important;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
}
/* 隱藏 Press Enter to submit form */
[data-testid="InputInstructions"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
    overflow: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}
/* ── 登入輸入契約：帳密欄必須永遠可輸入（修改樣式時勿移除此區塊）────────── */
.stForm .stTextInput,
.stForm label {
    width: 100% !important;
    text-align: left !important;
    pointer-events: auto !important;
    margin-left: 0 !important;
    padding-left: 0 !important;
}
.stForm .stTextInput input {
    pointer-events: auto !important;
    opacity: 1 !important;
    cursor: text !important;
    text-align: left !important;
    width: 100% !important;
    border: none !important;
    background: #ffffff !important;
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
    caret-color: var(--forest) !important;
    font-size: 0.92rem !important;
}
.stForm .stTextInput > div:last-child {
    width: 100% !important;
    margin-left: 0 !important;
    background: #ffffff !important;
    border: 1.5px solid #9CA3AF !important;
    border-radius: 8px !important;
    box-shadow: inset 0 0 0 1px #9CA3AF !important;
    min-height: 40px !important;
    box-sizing: border-box !important;
}
.stForm .stTextInput > div:last-child:focus-within {
    border-color: var(--forest) !important;
    box-shadow: inset 0 0 0 1px var(--forest), 0 0 0 3px rgba(22,101,52,0.12) !important;
}
.stForm .stTextInput input::placeholder {
    color: #8a968c !important;
    -webkit-text-fill-color: #8a968c !important;
    opacity: 1 !important;
}
.stForm .stTextInput button { display: none !important; }

.stForm button[kind="primary"],
.stForm [data-testid="stFormSubmitButton"] button {
    background: var(--forest) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    margin-top: 10px !important;
    margin-left: 0 !important;
    width: 100% !important;
}
.stForm button[kind="primary"]:hover,
.stForm [data-testid="stFormSubmitButton"] button:hover {
    background: var(--forest-deep) !important;
}
.stForm button[kind="primary"] *,
.stForm [data-testid="stFormSubmitButton"] button * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
.stForm label {
    color: #3d4f44 !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
}

@keyframes scamdnaEmbedIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@media (max-width: 900px) {
    .main .block-container {
        margin-left: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
        min-height: auto !important;
        height: auto !important;
        padding: 1.25rem 1.1rem 2rem !important;
        justify-content: flex-start !important;
    }
}
</style>
"""

_LOGIN_STAGE_HTML = ""  # 左牆改由 _inject_login_shell 掛到父頁 body

_LOGIN_PANEL_HEAD_HTML = """
<div class="scamdna-auth-card scamdna-panel-head" translate="no" lang="zh-Hant">
  <div class="scamdna-panel-title">歡迎回來</div>
  <div class="scamdna-panel-sub">登入後即可進入預警儀表板</div>
</div>
"""

_LOGIN_HTML = _LOGIN_LEFT_HTML

# ── 使用者列 CSS（嵌入主頁面 header）──────────────────────────────────────────
USER_BAR_CSS = """
.user-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
    height: 28px;
}
.user-name {
    color: #ffffff;
    font-size: 0.75rem;
    font-weight: 600;
    white-space: nowrap;
    max-width: 88px;
    overflow: hidden;
    text-overflow: ellipsis;
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
"""
