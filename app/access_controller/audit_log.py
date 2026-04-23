"""
存取日誌防竄改雜湊鏈模組

實作 append-only 存取日誌，使用 SHA-256 雜湊鏈確保日誌記錄不可被竄改。
每筆日誌包含前一筆的雜湊值，形成不可偽造的鏈式結構。

需求：6.2、6.5
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.models.access_log import AccessLog, VALID_ACTIONS


# ── 創世雜湊常數 ──────────────────────────────────────────────────────────────

GENESIS_HASH = "0" * 64
"""創世雜湊：第一筆日誌的 prev_hash 使用此值（64 個零）"""


# ── In-Memory 日誌儲存（模擬 PostgreSQL append-only 資料表）────────────────────
# ⚠️ 此 in-memory 日誌鏈僅供 development/testing 環境使用。
# production 環境應切換至 PostgreSQL append-only 資料表，以確保日誌持久化與防竄改。

_log_chain: list[AccessLog] = []
"""
In-memory 日誌鏈（僅供 development/testing 使用）

模擬 PostgreSQL append-only 資料表，
正式環境應替換為資料庫寫入操作。
"""

# ── 環境檢查：production 環境警告 ─────────────────────────────────────────────
try:
    from app.config import get_settings as _get_settings
    if _get_settings().app_env == "production":
        import logging as _logging
        _logging.getLogger(__name__).warning(
            "⚠️ [audit_log.py] _log_chain 使用 in-memory 儲存，"
            "production 環境應切換至 PostgreSQL append-only 資料表以確保日誌持久化。"
        )
except Exception:
    pass  # 設定載入失敗時不影響模組初始化


# ── 雜湊計算函數 ──────────────────────────────────────────────────────────────

def _compute_hash(
    operator_id: str,
    action: str,
    resource_id: str,
    resource_type: str,
    timestamp: datetime,
    prev_hash: str,
) -> str:
    """
    計算日誌記錄的 SHA-256 雜湊值。

    將日誌欄位序列化為 JSON 字串後計算雜湊，
    確保雜湊計算的確定性（欄位順序固定）。

    Args:
        operator_id: 操作人員識別碼
        action: 操作類型
        resource_id: 資源 UUID
        resource_type: 資源類型
        timestamp: 操作時間戳記
        prev_hash: 前一筆日誌的雜湊值

    Returns:
        64 字元的十六進位 SHA-256 雜湊字串
    """
    # 使用固定欄位順序確保雜湊計算的確定性
    payload = json.dumps(
        {
            "operator_id": operator_id,
            "action": action,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "timestamp": timestamp.isoformat(),
            "prev_hash": prev_hash,
        },
        ensure_ascii=False,
        sort_keys=True,  # 確保 JSON 鍵值排序一致
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ── 核心日誌操作函數 ──────────────────────────────────────────────────────────

def append_log(
    operator_id: str,
    action: str,
    resource_id: str,
    resource_type: str,
    timestamp: Optional[datetime] = None,
) -> AccessLog:
    """
    新增一筆存取日誌記錄至雜湊鏈。

    自動計算 prev_hash（取前一筆的 current_hash）與 current_hash（SHA-256），
    確保日誌鏈的完整性。

    Args:
        operator_id: 操作人員識別碼（非空字串）
        action: 操作類型（必須為 read / export / bulk_export 之一）
        resource_id: 存取的資源 UUID
        resource_type: 資源類型（例如：scam_script）
        timestamp: 操作時間戳記（預設為當前 UTC 時間）

    Returns:
        新建立的 AccessLog 物件

    Raises:
        ValueError: 若 operator_id 為空、action 不合法，或 resource_id 為空
    """
    # 輸入驗證
    if not operator_id or not operator_id.strip():
        raise ValueError("operator_id 不可為空字串")

    if action not in VALID_ACTIONS:
        raise ValueError(f"不合法的操作類型：{action}，合法操作為 {VALID_ACTIONS}")

    if not resource_id or not resource_id.strip():
        raise ValueError("resource_id 不可為空字串")

    if not resource_type or not resource_type.strip():
        raise ValueError("resource_type 不可為空字串")

    # 使用當前 UTC 時間（若未提供）
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    # 取得前一筆日誌的雜湊值（若無則使用創世雜湊）
    if _log_chain:
        prev_hash = _log_chain[-1].current_hash
    else:
        prev_hash = GENESIS_HASH

    # 計算本筆日誌的雜湊值
    current_hash = _compute_hash(
        operator_id=operator_id,
        action=action,
        resource_id=resource_id,
        resource_type=resource_type,
        timestamp=timestamp,
        prev_hash=prev_hash,
    )

    # 建立日誌記錄
    log_entry = AccessLog(
        id=str(uuid.uuid4()),
        operator_id=operator_id,
        action=action,
        resource_id=resource_id,
        resource_type=resource_type,
        timestamp=timestamp,
        prev_hash=prev_hash,
        current_hash=current_hash,
    )

    # 附加至日誌鏈（append-only，不可修改已有記錄）
    _log_chain.append(log_entry)

    return log_entry


def verify_chain() -> bool:
    """
    驗證整條日誌鏈的雜湊完整性。

    逐筆重新計算每筆日誌的 current_hash，
    並驗證與儲存值是否一致，同時確認 prev_hash 鏈接正確。

    Returns:
        True 表示日誌鏈完整未被竄改，False 表示偵測到竄改

    Note:
        空日誌鏈視為完整（回傳 True）。
    """
    if not _log_chain:
        return True

    for i, log in enumerate(_log_chain):
        # 驗證 prev_hash 鏈接
        expected_prev_hash = GENESIS_HASH if i == 0 else _log_chain[i - 1].current_hash
        if log.prev_hash != expected_prev_hash:
            return False

        # 重新計算 current_hash 並比對
        expected_hash = _compute_hash(
            operator_id=log.operator_id,
            action=log.action,
            resource_id=log.resource_id,
            resource_type=log.resource_type,
            timestamp=log.timestamp,
            prev_hash=log.prev_hash,
        )
        if log.current_hash != expected_hash:
            return False

    return True


def get_all_logs() -> list[AccessLog]:
    """
    取得所有日誌記錄（唯讀）。

    Returns:
        日誌記錄列表的副本（避免外部修改）
    """
    return list(_log_chain)


def clear_logs() -> None:
    """
    清空所有日誌記錄（僅供測試使用）。

    Warning:
        此函數僅供測試環境使用，正式環境不應呼叫此函數。
    """
    _log_chain.clear()
