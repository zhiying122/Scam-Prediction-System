"""
多因素驗證（MFA）模組

整合 pyotp 實作 TOTP（Time-based One-Time Password）驗證流程，
用於批量匯出 Scam_Script 時的二次身份驗證。

需求：6.4
"""

import pyotp

from app.config import get_settings


# ── 批量匯出閾值常數 ──────────────────────────────────────────────────────────

BULK_EXPORT_THRESHOLD = 100
"""觸發二次驗證的批量匯出閾值：超過此數量需要 TOTP 驗證"""


# ── TOTP 驗證核心函數 ─────────────────────────────────────────────────────────

def generate_totp_secret() -> str:
    """
    產生新的 TOTP 金鑰（Base32 編碼）。

    每位操作人員應有獨立的 TOTP 金鑰，
    正式環境應將金鑰安全儲存於資料庫並與操作人員帳號綁定。

    Returns:
        Base32 編碼的 TOTP 金鑰字串
    """
    return pyotp.random_base32()


def verify_totp(secret: str, token: str) -> bool:
    """
    驗證 TOTP 一次性密碼是否有效。

    使用 pyotp 驗證操作人員提供的 TOTP 碼，
    允許前後 1 個時間視窗的誤差（容忍時鐘偏差）。

    Args:
        secret: 操作人員的 TOTP 金鑰（Base32 編碼）
        token: 操作人員提供的 6 位數 TOTP 碼

    Returns:
        True 表示驗證通過，False 表示驗證失敗
    """
    if not secret or not token:
        return False

    totp = pyotp.TOTP(secret)
    # valid_window=1 允許前後 30 秒的時鐘偏差
    return totp.verify(token, valid_window=1)


def get_totp_uri(secret: str, operator_id: str) -> str:
    """
    產生 TOTP 設定 URI（用於 QR Code 掃描）。

    Args:
        secret: TOTP 金鑰（Base32 編碼）
        operator_id: 操作人員識別碼（作為帳號名稱）

    Returns:
        otpauth:// URI 字串，可用於產生 QR Code
    """
    settings = get_settings()
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=operator_id,
        issuer_name=settings.totp_issuer,
    )


# ── 批量匯出二次驗證函數 ──────────────────────────────────────────────────────

class BulkExportRequires2FA(Exception):
    """
    批量匯出需要二次驗證例外

    當匯出數量超過閾值且未提供 TOTP 驗證時拋出此例外。
    """

    def __init__(self, count: int):
        self.count = count
        super().__init__(
            f"匯出 {count} 份 Scam_Script 超過閾值 {BULK_EXPORT_THRESHOLD}，需要二次身份驗證（TOTP）"
        )


class InvalidTOTPError(Exception):
    """
    TOTP 驗證失敗例外

    當提供的 TOTP 碼無效時拋出此例外。
    """

    def __init__(self):
        super().__init__("TOTP 驗證失敗：提供的一次性密碼無效或已過期")


def require_2fa_for_bulk_export(
    count: int,
    totp_secret: str | None = None,
    totp_token: str | None = None,
) -> bool:
    """
    批量匯出二次驗證檢查函數。

    當匯出數量超過 100 份時，要求操作人員提供 TOTP 驗證碼。
    若未提供驗證碼，拋出 BulkExportRequires2FA 例外。
    若提供了驗證碼但驗證失敗，拋出 InvalidTOTPError 例外。

    Args:
        count: 欲匯出的 Scam_Script 數量
        totp_secret: 操作人員的 TOTP 金鑰（超過閾值時必須提供）
        totp_token: 操作人員提供的 TOTP 驗證碼（超過閾值時必須提供）

    Returns:
        True 表示允許匯出（數量未超過閾值，或 TOTP 驗證通過）

    Raises:
        BulkExportRequires2FA: 匯出數量超過閾值且未提供 TOTP 驗證碼
        InvalidTOTPError: 提供的 TOTP 驗證碼無效
        ValueError: count 為負數

    Example:
        # 數量未超過閾值，直接允許
        require_2fa_for_bulk_export(50)  # 回傳 True

        # 數量超過閾值，需提供 TOTP
        require_2fa_for_bulk_export(150, totp_secret="SECRET", totp_token="123456")
    """
    if count < 0:
        raise ValueError(f"匯出數量不可為負數：{count}")

    # 數量未超過閾值，直接允許
    if count <= BULK_EXPORT_THRESHOLD:
        return True

    # 數量超過閾值，需要 TOTP 驗證
    if totp_secret is None or totp_token is None:
        raise BulkExportRequires2FA(count)

    # 執行 TOTP 驗證
    if not verify_totp(totp_secret, totp_token):
        raise InvalidTOTPError()

    return True
