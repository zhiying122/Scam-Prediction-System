"""
Access_Controller 存取管制模組測試

涵蓋 RBAC 角色驗證、存取日誌雜湊鏈、批量匯出 TOTP 二次驗證的單元測試。
對應需求：6.1、6.2、6.4、6.5
"""

import uuid
from datetime import datetime, timezone

import pyotp
import pytest

from app.access_controller.audit_log import (
    GENESIS_HASH,
    append_log,
    clear_logs,
    get_all_logs,
    verify_chain,
    _compute_hash,
)
from app.access_controller.mfa import (
    BULK_EXPORT_THRESHOLD,
    BulkExportRequires2FA,
    InvalidTOTPError,
    generate_totp_secret,
    require_2fa_for_bulk_export,
    verify_totp,
)
from app.access_controller.rbac import (
    Action,
    Role,
    check_permission,
)


# ── 測試輔助函數 ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_log_chain():
    """每個測試前後清空日誌鏈，確保測試隔離"""
    clear_logs()
    yield
    clear_logs()


def _make_resource_id() -> str:
    """產生測試用資源 UUID"""
    return str(uuid.uuid4())


# ══════════════════════════════════════════════════════════════════════════════
# 2.1 RBAC 角色驗證核心邏輯測試（需求 6.1）
# ══════════════════════════════════════════════════════════════════════════════

class TestCheckPermission:
    """check_permission 函數的單元測試"""

    # ── 系統管理員權限測試 ────────────────────────────────────────────────────

    def test_admin_can_read(self):
        """系統管理員可以讀取 Scam_Script"""
        assert check_permission("admin-001", Role.SYSTEM_ADMIN, Action.READ) is True

    def test_admin_can_export(self):
        """系統管理員可以匯出 Scam_Script"""
        assert check_permission("admin-001", Role.SYSTEM_ADMIN, Action.EXPORT) is True

    def test_admin_can_bulk_export(self):
        """系統管理員可以批量匯出（超過 100 份需 2FA，由 mfa.py 處理）"""
        assert check_permission("admin-001", Role.SYSTEM_ADMIN, Action.BULK_EXPORT) is True

    # ── 詐騙分析師權限測試 ────────────────────────────────────────────────────

    def test_analyst_can_read(self):
        """詐騙分析師可以讀取 Scam_Script"""
        assert check_permission("analyst-001", Role.SCAM_ANALYST, Action.READ) is True

    def test_analyst_can_export(self):
        """詐騙分析師可以匯出 Scam_Script"""
        assert check_permission("analyst-001", Role.SCAM_ANALYST, Action.EXPORT) is True

    def test_analyst_can_bulk_export(self):
        """詐騙分析師可以批量匯出（超過 100 份需 2FA）"""
        assert check_permission("analyst-001", Role.SCAM_ANALYST, Action.BULK_EXPORT) is True

    # ── 一般操作員權限測試 ────────────────────────────────────────────────────

    def test_general_operator_cannot_read(self):
        """一般操作員不可讀取 Scam_Script"""
        assert check_permission("op-001", Role.GENERAL_OPERATOR, Action.READ) is False

    def test_general_operator_cannot_export(self):
        """一般操作員不可匯出 Scam_Script"""
        assert check_permission("op-001", Role.GENERAL_OPERATOR, Action.EXPORT) is False

    def test_general_operator_cannot_bulk_export(self):
        """一般操作員不可批量匯出"""
        assert check_permission("op-001", Role.GENERAL_OPERATOR, Action.BULK_EXPORT) is False

    # ── External_Client 權限測試 ──────────────────────────────────────────────

    def test_external_client_cannot_read(self):
        """External_Client 不可讀取 Scam_Script"""
        assert check_permission("client-001", Role.EXTERNAL_CLIENT, Action.READ) is False

    def test_external_client_cannot_export(self):
        """External_Client 不可匯出"""
        assert check_permission("client-001", Role.EXTERNAL_CLIENT, Action.EXPORT) is False

    def test_external_client_cannot_bulk_export(self):
        """External_Client 不可批量匯出"""
        assert check_permission("client-001", Role.EXTERNAL_CLIENT, Action.BULK_EXPORT) is False

    # ── 字串輸入支援測試 ──────────────────────────────────────────────────────

    def test_accepts_string_role(self):
        """check_permission 應接受字串形式的角色"""
        assert check_permission("admin-001", "系統管理員", "read") is True

    def test_accepts_string_action(self):
        """check_permission 應接受字串形式的操作類型"""
        assert check_permission("analyst-001", Role.SCAM_ANALYST, "export") is True

    def test_invalid_role_raises_value_error(self):
        """不合法的角色應拋出 ValueError"""
        with pytest.raises(ValueError, match="不合法的角色"):
            check_permission("op-001", "超級管理員", Action.READ)

    def test_invalid_action_raises_value_error(self):
        """不合法的操作類型應拋出 ValueError"""
        with pytest.raises(ValueError, match="不合法的操作類型"):
            check_permission("op-001", Role.SYSTEM_ADMIN, "delete")


# ══════════════════════════════════════════════════════════════════════════════
# 2.3 存取日誌防竄改雜湊鏈測試（需求 6.2、6.5）
# ══════════════════════════════════════════════════════════════════════════════

class TestAppendLog:
    """append_log 函數的單元測試"""

    def test_first_log_uses_genesis_hash(self):
        """第一筆日誌的 prev_hash 應為創世雜湊"""
        log = append_log("op-001", "read", _make_resource_id(), "scam_script")
        assert log.prev_hash == GENESIS_HASH

    def test_second_log_links_to_first(self):
        """第二筆日誌的 prev_hash 應等於第一筆的 current_hash"""
        log1 = append_log("op-001", "read", _make_resource_id(), "scam_script")
        log2 = append_log("op-002", "export", _make_resource_id(), "scam_script")
        assert log2.prev_hash == log1.current_hash

    def test_log_contains_required_fields(self):
        """日誌記錄應包含操作人員識別碼、存取時間與操作類型（需求 6.2）"""
        resource_id = _make_resource_id()
        log = append_log("op-001", "read", resource_id, "scam_script")

        assert log.operator_id == "op-001"
        assert log.action == "read"
        assert log.resource_id == resource_id
        assert log.resource_type == "scam_script"
        assert log.timestamp is not None
        assert log.id is not None

    def test_current_hash_is_sha256(self):
        """current_hash 應為 64 字元的十六進位字串（SHA-256）"""
        log = append_log("op-001", "read", _make_resource_id(), "scam_script")
        assert len(log.current_hash) == 64
        assert all(c in "0123456789abcdef" for c in log.current_hash)

    def test_log_stored_in_chain(self):
        """新增的日誌應儲存在日誌鏈中"""
        append_log("op-001", "read", _make_resource_id(), "scam_script")
        append_log("op-002", "export", _make_resource_id(), "scam_script")
        logs = get_all_logs()
        assert len(logs) == 2

    def test_custom_timestamp(self):
        """應支援自訂時間戳記"""
        custom_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        log = append_log("op-001", "read", _make_resource_id(), "scam_script", timestamp=custom_time)
        assert log.timestamp == custom_time

    def test_empty_operator_id_raises(self):
        """空的 operator_id 應拋出 ValueError"""
        with pytest.raises(ValueError, match="operator_id 不可為空字串"):
            append_log("", "read", _make_resource_id(), "scam_script")

    def test_invalid_action_raises(self):
        """不合法的操作類型應拋出 ValueError"""
        with pytest.raises(ValueError, match="不合法的操作類型"):
            append_log("op-001", "delete", _make_resource_id(), "scam_script")

    def test_empty_resource_id_raises(self):
        """空的 resource_id 應拋出 ValueError"""
        with pytest.raises(ValueError, match="resource_id 不可為空字串"):
            append_log("op-001", "read", "", "scam_script")

    def test_all_valid_actions_accepted(self):
        """所有合法操作類型（read/export/bulk_export）應被接受"""
        for action in ["read", "export", "bulk_export"]:
            log = append_log("op-001", action, _make_resource_id(), "scam_script")
            assert log.action == action


class TestVerifyChain:
    """verify_chain 函數的單元測試"""

    def test_empty_chain_is_valid(self):
        """空日誌鏈應視為完整（回傳 True）"""
        assert verify_chain() is True

    def test_single_log_is_valid(self):
        """單筆日誌鏈應通過驗證"""
        append_log("op-001", "read", _make_resource_id(), "scam_script")
        assert verify_chain() is True

    def test_multiple_logs_are_valid(self):
        """多筆日誌鏈應通過驗證"""
        for i in range(5):
            append_log(f"op-{i:03d}", "read", _make_resource_id(), "scam_script")
        assert verify_chain() is True

    def test_tampered_current_hash_detected(self):
        """竄改 current_hash 應被偵測到"""
        from app.access_controller import audit_log as al

        append_log("op-001", "read", _make_resource_id(), "scam_script")
        append_log("op-002", "export", _make_resource_id(), "scam_script")

        # 直接竄改第一筆日誌的 current_hash
        al._log_chain[0].current_hash = "f" * 64

        assert verify_chain() is False

    def test_tampered_prev_hash_detected(self):
        """竄改 prev_hash 應被偵測到"""
        from app.access_controller import audit_log as al

        append_log("op-001", "read", _make_resource_id(), "scam_script")
        append_log("op-002", "export", _make_resource_id(), "scam_script")

        # 直接竄改第二筆日誌的 prev_hash
        al._log_chain[1].prev_hash = "e" * 64

        assert verify_chain() is False

    def test_tampered_operator_id_detected(self):
        """竄改 operator_id 應被偵測到（雜湊不符）"""
        from app.access_controller import audit_log as al

        append_log("op-001", "read", _make_resource_id(), "scam_script")

        # 竄改 operator_id（但 current_hash 未更新）
        al._log_chain[0].operator_id = "attacker-999"

        assert verify_chain() is False

    def test_chain_integrity_after_multiple_appends(self):
        """多次新增後日誌鏈應保持完整"""
        resource_ids = [_make_resource_id() for _ in range(10)]
        for i, rid in enumerate(resource_ids):
            append_log(f"op-{i:03d}", "read", rid, "scam_script")

        assert verify_chain() is True
        assert len(get_all_logs()) == 10

    def test_tamper_middle_entry_breaks_chain(self):
        """竄改中間某筆記錄應導致從該筆開始的驗證失敗"""
        from app.access_controller import audit_log as al

        for i in range(5):
            append_log(f"op-{i:03d}", "read", _make_resource_id(), "scam_script")

        # 竄改第 3 筆（index=2）的 operator_id
        al._log_chain[2].operator_id = "tampered"

        # 整條鏈應驗證失敗
        assert verify_chain() is False


# ══════════════════════════════════════════════════════════════════════════════
# 2.6 批量匯出二次驗證（TOTP）測試（需求 6.4）
# ══════════════════════════════════════════════════════════════════════════════

class TestRequire2FAForBulkExport:
    """require_2fa_for_bulk_export 函數的單元測試"""

    def test_count_below_threshold_allowed(self):
        """匯出數量未超過閾值（100）應直接允許"""
        assert require_2fa_for_bulk_export(50) is True

    def test_count_at_threshold_allowed(self):
        """匯出數量等於閾值（100）應直接允許"""
        assert require_2fa_for_bulk_export(BULK_EXPORT_THRESHOLD) is True

    def test_count_above_threshold_without_totp_raises(self):
        """匯出數量超過閾值且未提供 TOTP 應拋出 BulkExportRequires2FA"""
        with pytest.raises(BulkExportRequires2FA) as exc_info:
            require_2fa_for_bulk_export(101)
        assert exc_info.value.count == 101

    def test_count_above_threshold_with_valid_totp_allowed(self):
        """匯出數量超過閾值且 TOTP 驗證通過應允許"""
        secret = generate_totp_secret()
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()

        result = require_2fa_for_bulk_export(150, totp_secret=secret, totp_token=valid_token)
        assert result is True

    def test_count_above_threshold_with_invalid_totp_raises(self):
        """匯出數量超過閾值且 TOTP 驗證失敗應拋出 InvalidTOTPError"""
        secret = generate_totp_secret()

        with pytest.raises(InvalidTOTPError):
            require_2fa_for_bulk_export(150, totp_secret=secret, totp_token="000000")

    def test_negative_count_raises_value_error(self):
        """負數匯出數量應拋出 ValueError"""
        with pytest.raises(ValueError, match="不可為負數"):
            require_2fa_for_bulk_export(-1)

    def test_zero_count_allowed(self):
        """匯出數量為 0 應直接允許"""
        assert require_2fa_for_bulk_export(0) is True

    def test_large_count_requires_totp(self):
        """大量匯出（如 10000 份）應要求 TOTP"""
        with pytest.raises(BulkExportRequires2FA):
            require_2fa_for_bulk_export(10000)

    def test_exactly_101_requires_totp(self):
        """剛好超過閾值（101 份）應要求 TOTP"""
        with pytest.raises(BulkExportRequires2FA) as exc_info:
            require_2fa_for_bulk_export(101)
        assert "101" in str(exc_info.value)


class TestVerifyTOTP:
    """verify_totp 函數的單元測試"""

    def test_valid_token_passes(self):
        """有效的 TOTP 碼應通過驗證"""
        secret = generate_totp_secret()
        totp = pyotp.TOTP(secret)
        assert verify_totp(secret, totp.now()) is True

    def test_invalid_token_fails(self):
        """無效的 TOTP 碼應驗證失敗"""
        secret = generate_totp_secret()
        assert verify_totp(secret, "000000") is False

    def test_empty_secret_fails(self):
        """空的 secret 應驗證失敗"""
        assert verify_totp("", "123456") is False

    def test_empty_token_fails(self):
        """空的 token 應驗證失敗"""
        secret = generate_totp_secret()
        assert verify_totp(secret, "") is False

    def test_wrong_secret_fails(self):
        """使用錯誤的 secret 驗證應失敗"""
        secret1 = generate_totp_secret()
        secret2 = generate_totp_secret()
        totp = pyotp.TOTP(secret1)
        # 用 secret1 產生的 token 不應通過 secret2 的驗證
        assert verify_totp(secret2, totp.now()) is False


class TestGenerateTOTPSecret:
    """generate_totp_secret 函數的單元測試"""

    def test_generates_valid_base32_secret(self):
        """產生的 TOTP 金鑰應為有效的 Base32 字串"""
        secret = generate_totp_secret()
        assert isinstance(secret, str)
        assert len(secret) > 0
        # Base32 字元集：A-Z 與 2-7
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
        assert all(c in valid_chars for c in secret)

    def test_each_secret_is_unique(self):
        """每次產生的 TOTP 金鑰應不同"""
        secrets = {generate_totp_secret() for _ in range(10)}
        assert len(secrets) == 10  # 10 個金鑰應全部不同


# ══════════════════════════════════════════════════════════════════════════════
# 屬性測試（Property-Based Testing）
# Feature: ai-scam-evolution-prediction
# ══════════════════════════════════════════════════════════════════════════════

from hypothesis import given, settings, assume
from hypothesis import strategies as st


# ── 策略定義 ──────────────────────────────────────────────────────────────────

# 合法角色策略
valid_roles = st.sampled_from(list(Role))

# 合法操作類型策略
valid_actions = st.sampled_from(list(Action))

# 合法操作類型字串策略（用於 audit_log）
valid_action_strings = st.sampled_from(["read", "export", "bulk_export"])

# 非空操作人員 ID 策略
operator_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"),
    min_size=1,
    max_size=50,
).filter(lambda s: s.strip() != "")

# 非空資源 ID 策略
resource_id_strategy = st.uuids().map(str)

# 非空資源類型策略
resource_type_strategy = st.sampled_from(["scam_script", "risk_vector", "alert_event"])

# 匯出數量策略（0 ~ 閾值）
count_below_threshold = st.integers(min_value=0, max_value=BULK_EXPORT_THRESHOLD)

# 匯出數量策略（超過閾值）
count_above_threshold = st.integers(min_value=BULK_EXPORT_THRESHOLD + 1, max_value=10000)


# ── 屬性 18：角色存取控制 ─────────────────────────────────────────────────────
# Feature: ai-scam-evolution-prediction, Property 18: 角色存取控制

class TestProperty18RoleAccessControl:
    """
    屬性 18：角色存取控制
    驗證需求：6.1

    對任意合法角色與操作類型，check_permission 的回傳值必須與
    權限矩陣 PERMISSION_MATRIX 中定義的值完全一致。
    """

    @given(role=valid_roles, action=valid_actions)
    @settings(max_examples=100)
    def test_permission_matches_matrix(self, role: Role, action: Action):
        """
        # Feature: ai-scam-evolution-prediction, Property 18: 角色存取控制
        對任意合法角色與操作類型，check_permission 結果必須與權限矩陣一致。
        """
        from app.access_controller.rbac import PERMISSION_MATRIX
        expected = PERMISSION_MATRIX[role][action]
        result = check_permission("test-operator", role, action)
        assert result == expected, (
            f"角色 {role.value} 對操作 {action.value} 的權限應為 {expected}，但得到 {result}"
        )

    @given(role=valid_roles, action=valid_actions)
    @settings(max_examples=100)
    def test_permission_is_boolean(self, role: Role, action: Action):
        """
        # Feature: ai-scam-evolution-prediction, Property 18: 角色存取控制
        check_permission 的回傳值必須為布林值。
        """
        result = check_permission("test-operator", role, action)
        assert isinstance(result, bool), f"check_permission 應回傳 bool，但得到 {type(result)}"

    @given(
        operator_id=operator_id_strategy,
        role=valid_roles,
        action=valid_actions,
    )
    @settings(max_examples=100)
    def test_permission_independent_of_operator_id(
        self, operator_id: str, role: Role, action: Action
    ):
        """
        # Feature: ai-scam-evolution-prediction, Property 18: 角色存取控制
        權限結果只取決於角色與操作類型，與 operator_id 無關。
        """
        result1 = check_permission(operator_id, role, action)
        result2 = check_permission("another-operator-xyz", role, action)
        assert result1 == result2, (
            f"相同角色 {role.value} 對操作 {action.value} 的權限不應因 operator_id 不同而改變"
        )

    @given(action=valid_actions)
    @settings(max_examples=100)
    def test_restricted_roles_always_denied(self, action: Action):
        """
        # Feature: ai-scam-evolution-prediction, Property 18: 角色存取控制
        一般操作員與 External_Client 對任意操作類型均應被拒絕。
        """
        for restricted_role in [Role.GENERAL_OPERATOR, Role.EXTERNAL_CLIENT]:
            result = check_permission("test-op", restricted_role, action)
            assert result is False, (
                f"角色 {restricted_role.value} 對操作 {action.value} 應被拒絕，但得到 {result}"
            )

    @given(action=valid_actions)
    @settings(max_examples=100)
    def test_privileged_roles_always_allowed(self, action: Action):
        """
        # Feature: ai-scam-evolution-prediction, Property 18: 角色存取控制
        系統管理員與詐騙分析師對任意操作類型均應被允許。
        """
        for privileged_role in [Role.SYSTEM_ADMIN, Role.SCAM_ANALYST]:
            result = check_permission("test-op", privileged_role, action)
            assert result is True, (
                f"角色 {privileged_role.value} 對操作 {action.value} 應被允許，但得到 {result}"
            )


# ── 屬性 19：存取日誌記錄完整性（Round-Trip）────────────────────────────────
# Feature: ai-scam-evolution-prediction, Property 19: 存取日誌記錄完整性（Round-Trip）

class TestProperty19AuditLogRoundTrip:
    """
    屬性 19：存取日誌記錄完整性（Round-Trip）
    驗證需求：6.2

    對任意合法輸入，append_log 寫入後 get_all_logs 取回的記錄
    必須與原始輸入完全一致（Round-Trip 不變量）。
    """

    @pytest.fixture(autouse=True)
    def reset(self):
        clear_logs()
        yield
        clear_logs()

    @given(
        operator_id=operator_id_strategy,
        action=valid_action_strings,
        resource_id=resource_id_strategy,
        resource_type=resource_type_strategy,
    )
    @settings(max_examples=100)
    def test_log_fields_preserved_after_append(
        self, operator_id: str, action: str, resource_id: str, resource_type: str
    ):
        """
        # Feature: ai-scam-evolution-prediction, Property 19: 存取日誌記錄完整性（Round-Trip）
        append_log 後取回的記錄，所有欄位值必須與輸入完全一致。
        """
        clear_logs()
        log = append_log(operator_id, action, resource_id, resource_type)
        logs = get_all_logs()

        assert len(logs) == 1
        retrieved = logs[0]
        assert retrieved.operator_id == operator_id
        assert retrieved.action == action
        assert retrieved.resource_id == resource_id
        assert retrieved.resource_type == resource_type
        assert retrieved.id == log.id
        assert retrieved.current_hash == log.current_hash

    @given(
        entries=st.lists(
            st.tuples(
                operator_id_strategy,
                valid_action_strings,
                resource_id_strategy,
                resource_type_strategy,
            ),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=50)
    def test_log_count_matches_appends(self, entries):
        """
        # Feature: ai-scam-evolution-prediction, Property 19: 存取日誌記錄完整性（Round-Trip）
        append_log 呼叫 N 次後，get_all_logs 應回傳恰好 N 筆記錄。
        """
        clear_logs()
        for operator_id, action, resource_id, resource_type in entries:
            append_log(operator_id, action, resource_id, resource_type)

        logs = get_all_logs()
        assert len(logs) == len(entries)

    @given(
        operator_id=operator_id_strategy,
        action=valid_action_strings,
        resource_id=resource_id_strategy,
        resource_type=resource_type_strategy,
    )
    @settings(max_examples=100)
    def test_log_has_non_empty_hash_fields(
        self, operator_id: str, action: str, resource_id: str, resource_type: str
    ):
        """
        # Feature: ai-scam-evolution-prediction, Property 19: 存取日誌記錄完整性（Round-Trip）
        每筆日誌的 prev_hash 與 current_hash 必須為非空的 64 字元十六進位字串。
        """
        clear_logs()
        log = append_log(operator_id, action, resource_id, resource_type)

        assert len(log.prev_hash) == 64
        assert len(log.current_hash) == 64
        assert all(c in "0123456789abcdef" for c in log.prev_hash)
        assert all(c in "0123456789abcdef" for c in log.current_hash)

    @given(
        operator_id=operator_id_strategy,
        action=valid_action_strings,
        resource_id=resource_id_strategy,
        resource_type=resource_type_strategy,
    )
    @settings(max_examples=100)
    def test_log_timestamp_is_set(
        self, operator_id: str, action: str, resource_id: str, resource_type: str
    ):
        """
        # Feature: ai-scam-evolution-prediction, Property 19: 存取日誌記錄完整性（Round-Trip）
        每筆日誌的 timestamp 必須為非 None 的 datetime 物件。
        """
        clear_logs()
        log = append_log(operator_id, action, resource_id, resource_type)
        assert log.timestamp is not None
        assert isinstance(log.timestamp, datetime)


# ── 屬性 21：日誌防竄改雜湊鏈完整性 ─────────────────────────────────────────
# Feature: ai-scam-evolution-prediction, Property 21: 日誌防竄改雜湊鏈完整性

class TestProperty21HashChainIntegrity:
    """
    屬性 21：日誌防竄改雜湊鏈完整性
    驗證需求：6.5

    對任意合法日誌序列，verify_chain 在未竄改時必須回傳 True；
    對任意單一欄位的竄改，verify_chain 必須回傳 False。
    """

    @pytest.fixture(autouse=True)
    def reset(self):
        clear_logs()
        yield
        clear_logs()

    @given(
        entries=st.lists(
            st.tuples(
                operator_id_strategy,
                valid_action_strings,
                resource_id_strategy,
                resource_type_strategy,
            ),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=50)
    def test_intact_chain_always_valid(self, entries):
        """
        # Feature: ai-scam-evolution-prediction, Property 21: 日誌防竄改雜湊鏈完整性
        對任意合法日誌序列，未竄改的鏈必須通過 verify_chain 驗證。
        """
        clear_logs()
        for operator_id, action, resource_id, resource_type in entries:
            append_log(operator_id, action, resource_id, resource_type)

        assert verify_chain() is True

    @given(
        entries=st.lists(
            st.tuples(
                operator_id_strategy,
                valid_action_strings,
                resource_id_strategy,
                resource_type_strategy,
            ),
            min_size=2,
            max_size=8,
        ),
        tamper_index=st.integers(min_value=0, max_value=7),
        tampered_value=st.text(min_size=1, max_size=20).filter(lambda s: s.strip() != ""),
    )
    @settings(max_examples=50)
    def test_tampered_operator_id_detected(self, entries, tamper_index, tampered_value):
        """
        # Feature: ai-scam-evolution-prediction, Property 21: 日誌防竄改雜湊鏈完整性
        竄改任意一筆日誌的 operator_id 後，verify_chain 必須回傳 False。
        """
        from app.access_controller import audit_log as al

        clear_logs()
        for operator_id, action, resource_id, resource_type in entries:
            append_log(operator_id, action, resource_id, resource_type)

        idx = tamper_index % len(entries)
        original = al._log_chain[idx].operator_id
        assume(tampered_value != original)

        al._log_chain[idx].operator_id = tampered_value
        assert verify_chain() is False

    @given(
        entries=st.lists(
            st.tuples(
                operator_id_strategy,
                valid_action_strings,
                resource_id_strategy,
                resource_type_strategy,
            ),
            min_size=2,
            max_size=8,
        ),
        tamper_index=st.integers(min_value=0, max_value=7),
    )
    @settings(max_examples=50)
    def test_tampered_current_hash_detected(self, entries, tamper_index):
        """
        # Feature: ai-scam-evolution-prediction, Property 21: 日誌防竄改雜湊鏈完整性
        竄改任意一筆日誌的 current_hash 後，verify_chain 必須回傳 False。
        """
        from app.access_controller import audit_log as al

        clear_logs()
        for operator_id, action, resource_id, resource_type in entries:
            append_log(operator_id, action, resource_id, resource_type)

        idx = tamper_index % len(entries)
        al._log_chain[idx].current_hash = "f" * 64

        assert verify_chain() is False

    @given(
        entries=st.lists(
            st.tuples(
                operator_id_strategy,
                valid_action_strings,
                resource_id_strategy,
                resource_type_strategy,
            ),
            min_size=2,
            max_size=8,
        ),
        tamper_index=st.integers(min_value=1, max_value=7),
    )
    @settings(max_examples=50)
    def test_tampered_prev_hash_detected(self, entries, tamper_index):
        """
        # Feature: ai-scam-evolution-prediction, Property 21: 日誌防竄改雜湊鏈完整性
        竄改任意一筆日誌（非第一筆）的 prev_hash 後，verify_chain 必須回傳 False。
        """
        from app.access_controller import audit_log as al

        clear_logs()
        for operator_id, action, resource_id, resource_type in entries:
            append_log(operator_id, action, resource_id, resource_type)

        # 確保 tamper_index 在有效範圍內（至少第 2 筆，index >= 1）
        idx = max(1, tamper_index % len(entries))
        al._log_chain[idx].prev_hash = "e" * 64

        assert verify_chain() is False

    @given(
        n=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=30)
    def test_chain_length_preserved(self, n: int):
        """
        # Feature: ai-scam-evolution-prediction, Property 21: 日誌防竄改雜湊鏈完整性
        append_log N 次後，日誌鏈長度必須恰好為 N（append-only 不變量）。
        """
        clear_logs()
        for i in range(n):
            append_log(f"op-{i:03d}", "read", str(uuid.uuid4()), "scam_script")

        assert len(get_all_logs()) == n


# ── 屬性 20：批量匯出二次驗證閾值 ────────────────────────────────────────────
# Feature: ai-scam-evolution-prediction, Property 20: 批量匯出二次驗證閾值

class TestProperty20BulkExport2FAThreshold:
    """
    屬性 20：批量匯出二次驗證閾值
    驗證需求：6.4

    對任意數量 count：
    - count <= 100：require_2fa_for_bulk_export 必須回傳 True（不需 2FA）
    - count > 100 且未提供 TOTP：必須拋出 BulkExportRequires2FA
    - count > 100 且提供有效 TOTP：必須回傳 True
    """

    @given(count=count_below_threshold)
    @settings(max_examples=100)
    def test_count_at_or_below_threshold_never_requires_2fa(self, count: int):
        """
        # Feature: ai-scam-evolution-prediction, Property 20: 批量匯出二次驗證閾值
        count <= 100 時，require_2fa_for_bulk_export 必須回傳 True，不拋出例外。
        """
        result = require_2fa_for_bulk_export(count)
        assert result is True

    @given(count=count_above_threshold)
    @settings(max_examples=100)
    def test_count_above_threshold_always_requires_2fa(self, count: int):
        """
        # Feature: ai-scam-evolution-prediction, Property 20: 批量匯出二次驗證閾值
        count > 100 且未提供 TOTP 時，必須拋出 BulkExportRequires2FA。
        """
        with pytest.raises(BulkExportRequires2FA) as exc_info:
            require_2fa_for_bulk_export(count)
        assert exc_info.value.count == count

    @given(count=count_above_threshold)
    @settings(max_examples=50)
    def test_count_above_threshold_with_valid_totp_allowed(self, count: int):
        """
        # Feature: ai-scam-evolution-prediction, Property 20: 批量匯出二次驗證閾值
        count > 100 且提供有效 TOTP 時，必須回傳 True。
        """
        secret = generate_totp_secret()
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()

        result = require_2fa_for_bulk_export(count, totp_secret=secret, totp_token=valid_token)
        assert result is True

    @given(count=count_above_threshold)
    @settings(max_examples=50)
    def test_count_above_threshold_with_invalid_totp_raises(self, count: int):
        """
        # Feature: ai-scam-evolution-prediction, Property 20: 批量匯出二次驗證閾值
        count > 100 且提供無效 TOTP 時，必須拋出 InvalidTOTPError。
        """
        secret = generate_totp_secret()

        with pytest.raises(InvalidTOTPError):
            require_2fa_for_bulk_export(count, totp_secret=secret, totp_token="000000")

    @given(count=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=100)
    def test_threshold_boundary_is_exactly_100(self, count: int):
        """
        # Feature: ai-scam-evolution-prediction, Property 20: 批量匯出二次驗證閾值
        閾值邊界精確為 100：count <= 100 允許，count > 100 需要 2FA。
        """
        if count <= BULK_EXPORT_THRESHOLD:
            result = require_2fa_for_bulk_export(count)
            assert result is True
        else:
            with pytest.raises(BulkExportRequires2FA):
                require_2fa_for_bulk_export(count)

    @given(count=count_above_threshold)
    @settings(max_examples=50)
    def test_exception_contains_correct_count(self, count: int):
        """
        # Feature: ai-scam-evolution-prediction, Property 20: 批量匯出二次驗證閾值
        BulkExportRequires2FA 例外必須包含正確的 count 值。
        """
        with pytest.raises(BulkExportRequires2FA) as exc_info:
            require_2fa_for_bulk_export(count)
        assert exc_info.value.count == count
