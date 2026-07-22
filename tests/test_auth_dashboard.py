"""Dashboard 登入認證規範測試 — 確保帳密單一來源與輸入可用性契約。"""

import re

import pytest

from app.dashboard import auth
from app.dashboard.auth import (
    DEMO_PASSWORD,
    DEMO_USERNAME,
    _build_default_user_db,
    _hash_password,
    _load_local_admin_accounts_from_env,
    _sync_builtin_admin,
    demo_credentials_hint,
)
from app.access_controller.rbac import Role


class TestDemoCredentialSingleSource:
    """帳密只能從 auth.DEMO_* 讀取，更新常數後應自動同步。"""

    def test_demo_hint_matches_constants(self) -> None:
        hint = demo_credentials_hint()
        assert DEMO_USERNAME in hint
        assert DEMO_PASSWORD in hint

    def test_default_db_uses_demo_constants(self) -> None:
        db = _build_default_user_db()
        assert DEMO_USERNAME in db
        assert db[DEMO_USERNAME]["password_hash"] == _hash_password(DEMO_PASSWORD)

    def test_sync_updates_stale_admin_hash(self) -> None:
        db = _build_default_user_db()
        db[DEMO_USERNAME]["password_hash"] = _hash_password("old-password")
        _sync_builtin_admin(db)
        assert db[DEMO_USERNAME]["password_hash"] == _hash_password(DEMO_PASSWORD)

    def test_streamlit_app_has_login_gate_without_auto_login(self) -> None:
        """streamlit_app 須有登入閘門，且不得硬編碼密碼或自動登入。"""
        from pathlib import Path

        source = Path("app/dashboard/streamlit_app.py").read_text(encoding="utf-8")
        assert "Aegis@2026" not in source
        assert "render_login_page()" in source
        assert "st.stop()" in source
        assert "authenticate(DEMO_USERNAME" not in source
        assert "handle_browser_refresh_logout()" in source
        assert "install_browser_refresh_guard()" in source

    def test_auth_has_refresh_logout_helpers(self) -> None:
        assert hasattr(auth, "handle_browser_refresh_logout")
        assert hasattr(auth, "install_browser_refresh_guard")
        assert auth._REFRESH_LOGOUT_PARAM == "_refresh_logout"

    def test_demo_hint_never_shows_local_env_accounts(self, monkeypatch) -> None:
        monkeypatch.setenv("DASHBOARD_LOCAL_ADMINS", "hiddenuser:hiddenpass:Hidden Admin")
        hint = demo_credentials_hint()
        assert "hiddenuser" not in hint
        assert "hiddenpass" not in hint
        assert "Hidden Admin" not in hint

    def test_local_admin_loaded_only_from_env(self, monkeypatch) -> None:
        monkeypatch.setenv("DASHBOARD_LOCAL_ADMINS", "localadmin:localpass:Local Admin")
        accounts = _load_local_admin_accounts_from_env()
        assert "localadmin" in accounts
        assert accounts["localadmin"]["password_hash"] == _hash_password("localpass")
        assert accounts["localadmin"]["role"] == Role.SYSTEM_ADMIN
        assert accounts["localadmin"]["source"] == "local_env"

    def test_no_private_credentials_in_committed_auth_source(self) -> None:
        from pathlib import Path

        for rel in ("app/dashboard/auth.py", "app/dashboard/streamlit_app.py"):
            text = Path(rel).read_text(encoding="utf-8").lower()
            assert "chien" not in text
            assert "123456" not in text


class TestAuthenticateLogic:
    """純邏輯認證（不依賴 Streamlit session）。"""

    def test_valid_demo_credentials(self) -> None:
        db = _build_default_user_db()
        user_data = db.get(DEMO_USERNAME.strip().lower())
        assert user_data is not None
        assert user_data["password_hash"] == _hash_password(DEMO_PASSWORD)

    def test_wrong_password_fails(self) -> None:
        db = _build_default_user_db()
        user_data = db.get("nick")
        assert user_data is None


class TestLoginCssContract:
    """登入頁 CSS 必須保留輸入可用性規則。"""

    def test_login_css_has_input_contract(self) -> None:
        css = auth._LOGIN_CSS
        assert "登入輸入契約" in css
        assert "pointer-events: auto" in css
        assert re.search(r"\.stTextInput input[^}]*opacity:\s*1", css)

    def test_login_css_does_not_disable_inputs(self) -> None:
        css = auth._LOGIN_CSS
        # input 本身不可設 opacity:0（密碼顯示鈕區塊除外）
        input_blocks = re.findall(
            r"\.stTextInput input[^{]*\{[^}]+\}", css, flags=re.DOTALL
        )
        for block in input_blocks:
            assert "opacity: 0" not in block.replace("opacity: 0.", "")

    def test_login_forms_keep_values_on_submit(self) -> None:
        source = open("app/dashboard/auth.py", encoding="utf-8").read()
        assert 'st.form("login_form", clear_on_submit=False)' in source
        assert 'st.form("register_form", clear_on_submit=False)' in source
