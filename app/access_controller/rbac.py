"""
RBAC 角色型存取控制模組

定義系統角色枚舉、權限矩陣，並提供 FastAPI 依賴注入裝飾器，
確保只有具備合法角色的操作人員才能存取受管制資源。

需求：6.1
"""

from enum import Enum
from typing import Callable

from fastapi import Depends, HTTPException, Header, status


# ── 角色枚舉定義 ──────────────────────────────────────────────────────────────

class Role(str, Enum):
    """
    系統角色枚舉

    定義系統中所有合法的操作人員角色。
    """
    SYSTEM_ADMIN = "系統管理員"
    """系統管理員：最高權限，可存取 Scam_Script 並執行批量匯出"""

    SCAM_ANALYST = "詐騙分析師"
    """詐騙分析師：可存取 Scam_Script 並執行批量匯出"""

    GENERAL_OPERATOR = "一般操作員"
    """一般操作員：不可存取 Scam_Script，不可匯出"""

    EXTERNAL_CLIENT = "External_Client"
    """外部客戶端：不可存取 Scam_Script，不可匯出"""


# ── 操作類型定義 ──────────────────────────────────────────────────────────────

class Action(str, Enum):
    """
    操作類型枚舉

    定義系統中所有合法的操作類型。
    """
    READ = "read"
    """讀取操作：存取 Scam_Script 內容"""

    EXPORT = "export"
    """匯出操作：匯出單筆或少量 Scam_Script"""

    BULK_EXPORT = "bulk_export"
    """批量匯出操作：匯出超過 100 份 Scam_Script（需 2FA）"""


# ── 權限矩陣定義 ──────────────────────────────────────────────────────────────

# 格式：{角色: {操作: 是否允許}}
PERMISSION_MATRIX: dict[Role, dict[Action, bool]] = {
    Role.SYSTEM_ADMIN: {
        Action.READ: True,
        Action.EXPORT: True,
        Action.BULK_EXPORT: True,  # 超過 100 份需 2FA，由 mfa.py 處理
    },
    Role.SCAM_ANALYST: {
        Action.READ: True,
        Action.EXPORT: True,
        Action.BULK_EXPORT: True,  # 超過 100 份需 2FA，由 mfa.py 處理
    },
    Role.GENERAL_OPERATOR: {
        Action.READ: False,
        Action.EXPORT: False,
        Action.BULK_EXPORT: False,
    },
    Role.EXTERNAL_CLIENT: {
        Action.READ: False,
        Action.EXPORT: False,
        Action.BULK_EXPORT: False,
    },
}


# ── 核心權限驗證函數 ──────────────────────────────────────────────────────────

def _resolve_role(role: str) -> Role:
    """將角色字串解析為 Role 枚舉（支援中文值與枚舉名稱如 SCAM_ANALYST）。"""
    try:
        return Role(role)
    except ValueError:
        try:
            return Role[role]
        except KeyError:
            valid = [f"{r.name} / {r.value}" for r in Role]
            raise ValueError(f"不合法的角色：{role}，合法角色為 {valid}") from None


def check_permission(operator_id: str, role: Role | str, action: Action | str) -> bool:
    """
    驗證操作人員是否具備指定操作的權限。

    Args:
        operator_id: 操作人員識別碼（用於日誌記錄）
        role: 操作人員角色（Role 枚舉或字串）
        action: 欲執行的操作類型（Action 枚舉或字串）

    Returns:
        True 表示允許，False 表示拒絕

    Raises:
        ValueError: 若角色或操作類型不在合法範圍內
    """
    # 將字串轉換為枚舉（支援字串輸入）
    if isinstance(role, str):
        role = _resolve_role(role)

    if isinstance(action, str):
        try:
            action = Action(action)
        except ValueError:
            raise ValueError(f"不合法的操作類型：{action}，合法操作為 {[a.value for a in Action]}")

    # 查詢權限矩陣
    role_permissions = PERMISSION_MATRIX.get(role, {})
    return role_permissions.get(action, False)


# ── FastAPI 依賴注入裝飾器 ────────────────────────────────────────────────────

def require_role(roles: list[Role]) -> Callable:
    """
    FastAPI 依賴注入裝飾器工廠函數。

    建立一個依賴函數，驗證請求標頭中的角色是否在允許的角色列表中。
    若驗證失敗，回傳 HTTP 403 Forbidden。

    Args:
        roles: 允許存取的角色列表

    Returns:
        FastAPI 依賴函數

    Example:
        @router.get("/scam-scripts")
        async def get_scripts(
            operator=Depends(require_role([Role.SYSTEM_ADMIN, Role.SCAM_ANALYST]))
        ):
            ...
    """
    async def _check_role(
        x_operator_id: str = Header(..., description="操作人員識別碼"),
        x_operator_role: str = Header(..., description="操作人員角色"),
    ) -> dict:
        """
        驗證操作人員角色的依賴函數。

        從請求標頭讀取操作人員識別碼與角色，
        驗證角色是否在允許的角色列表中。
        """
        # 嘗試將字串轉換為 Role 枚舉
        try:
            operator_role = _resolve_role(x_operator_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"不合法的角色：{x_operator_role}",
            )

        # 驗證角色是否在允許列表中
        if operator_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"角色 {operator_role.value} 無權執行此操作，需要角色：{[r.value for r in roles]}",
            )

        return {
            "operator_id": x_operator_id,
            "role": operator_role,
        }

    return _check_role
