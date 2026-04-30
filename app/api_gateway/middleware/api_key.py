"""
API 金鑰驗證中介軟體

負責驗證所有進入 API Gateway 的請求是否攜帶有效的 API 金鑰。
無效或缺失的金鑰將立即回傳 HTTP 401，不執行任何業務邏輯。

需求：5.3
"""

import json
import logging
import os
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# ── 硬編碼的開發/測試用 API 金鑰（僅作為 fallback）─────────────────────────────
# ⚠️ 此硬編碼金鑰僅供 development/testing 環境使用。
# 實際生產環境應透過環境變數 API_KEYS 或 PostgreSQL 資料庫載入金鑰。
_HARDCODED_DEV_KEYS: dict[str, dict] = {
    "test-key-001": {
        "client_id": "client-financial-001",
        "plan": "standard",
        "rate_limit": 100,  # 每 60 秒最多 100 次請求
        "is_active": True,
    },
    "test-key-002": {
        "client_id": "client-gov-001",
        "plan": "premium",
        "rate_limit": 500,  # 每 60 秒最多 500 次請求
        "is_active": True,
    },
    "test-key-revoked": {
        "client_id": "client-revoked-001",
        "plan": "standard",
        "rate_limit": 100,
        "is_active": False,  # 已撤銷的金鑰
    },
}


def _load_api_keys_from_env() -> dict[str, dict]:
    """
    從環境變數載入 API 金鑰配置

    優先從環境變數 API_KEYS 載入 JSON 格式的金鑰配置。
    若環境變數未設定，在 development/testing 環境 fallback 到硬編碼金鑰；
    在 production 環境中使用硬編碼金鑰時記錄警告日誌。

    環境變數格式範例：
        API_KEYS='{"key1": {"client_id": "...", "plan": "...", "rate_limit": 100, "is_active": true}}'

    Returns:
        API 金鑰字典
    """
    api_keys_json = os.environ.get("API_KEYS")

    if api_keys_json:
        try:
            keys = json.loads(api_keys_json)
            logger.info("已從環境變數 API_KEYS 載入 %d 組 API 金鑰", len(keys))
            return keys
        except (json.JSONDecodeError, TypeError) as e:
            logger.error("環境變數 API_KEYS 格式無效，無法解析 JSON: %s", e)

    # 環境變數未設定或解析失敗，檢查執行環境
    app_env = os.environ.get("APP_ENV", "development").lower()

    if app_env in ("development", "testing"):
        logger.debug(
            "環境變數 API_KEYS 未設定，%s 環境使用硬編碼 fallback 金鑰",
            app_env,
        )
        return _HARDCODED_DEV_KEYS.copy()

    # production 環境未設定 API_KEYS：拒絕啟動，不使用硬編碼金鑰
    if app_env == "production":
        raise RuntimeError(
            "⛔ 生產環境必須設定環境變數 API_KEYS，不允許使用硬編碼測試金鑰。"
            "請設定 API_KEYS 環境變數或連接資料庫載入金鑰。"
        )

    # development/testing 環境：使用硬編碼金鑰作為 fallback
    logger.warning(
        "⚠️ 生產環境未設定環境變數 API_KEYS，使用硬編碼 fallback 金鑰。"
        "請儘速設定 API_KEYS 環境變數或連接資料庫。"
    )
    return _HARDCODED_DEV_KEYS.copy()


# 格式：{api_key: {"client_id": str, "plan": str, "rate_limit": int, "is_active": bool}}
# ⚠️ _VALID_API_KEYS 的 in-memory 字典僅供 development/testing 環境使用。
# production 環境應從 PostgreSQL 或外部金鑰管理服務載入。
_VALID_API_KEYS: dict[str, dict] = _load_api_keys_from_env()

# ── 環境檢查：production 環境警告 ─────────────────────────────────────────────
try:
    from app.config import get_settings as _get_settings
    if _get_settings().app_env == "production":
        logger.warning(
            "⚠️ [api_key.py] _VALID_API_KEYS 使用 in-memory 字典儲存，"
            "production 環境應切換至 PostgreSQL 或外部金鑰管理服務。"
        )
except Exception:
    pass  # 設定載入失敗時不影響模組初始化

# 不需要 API 金鑰驗證的路徑白名單
_EXEMPT_PATHS: set[str] = {
    "/v1/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}


def lookup_api_key(api_key: str) -> dict | None:
    """
    查詢 API 金鑰有效性

    模擬從 PostgreSQL 查詢 API 金鑰資料。
    回傳金鑰資訊字典，若金鑰不存在或已撤銷則回傳 None。

    Args:
        api_key: 待驗證的 API 金鑰字串

    Returns:
        金鑰資訊字典（含 client_id、plan、rate_limit），或 None（無效金鑰）
    """
    key_info = _VALID_API_KEYS.get(api_key)
    if key_info is None:
        return None
    # 已撤銷的金鑰視為無效
    if not key_info.get("is_active", False):
        return None
    return key_info


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    API 金鑰驗證中介軟體

    攔截所有 HTTP 請求，驗證 X-API-Key 標頭的有效性。
    驗證通過後將金鑰資訊注入 request.state，供後續中介軟體使用。

    無效情況（回傳 HTTP 401）：
    - 缺少 X-API-Key 標頭
    - 金鑰格式為空字串
    - 金鑰不存在於資料庫
    - 金鑰已被撤銷（is_active = False）
    """

    def __init__(self, app: ASGIApp, exempt_paths: set[str] | None = None) -> None:
        """
        初始化 API 金鑰驗證中介軟體

        Args:
            app: ASGI 應用程式實例
            exempt_paths: 不需要驗證的路徑集合（預設使用全域白名單）
        """
        super().__init__(app)
        self.exempt_paths = exempt_paths if exempt_paths is not None else _EXEMPT_PATHS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        處理請求的核心邏輯

        Args:
            request: FastAPI 請求物件
            call_next: 下一個中介軟體或路由處理函數

        Returns:
            HTTP 回應物件
        """
        # 白名單路徑直接放行，不需要 API 金鑰
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # 取得 X-API-Key 標頭
        api_key = request.headers.get("X-API-Key", "").strip()

        # 空值或缺失標頭：回傳 401
        if not api_key:
            logger.warning(
                "API 金鑰缺失 | 來源 IP: %s | 路徑: %s",
                request.client.host if request.client else "unknown",
                request.url.path,
            )
            return JSONResponse(
                status_code=401,
                content={
                    "error_code": "MISSING_API_KEY",
                    "description": "請求缺少 X-API-Key 標頭，請提供有效的 API 金鑰",
                },
            )

        # 查詢金鑰有效性（模擬 PostgreSQL 查詢）
        key_info = lookup_api_key(api_key)

        if key_info is None:
            logger.warning(
                "無效 API 金鑰 | 金鑰前綴: %s... | 來源 IP: %s | 路徑: %s",
                api_key[:8] if len(api_key) >= 8 else api_key,
                request.client.host if request.client else "unknown",
                request.url.path,
            )
            return JSONResponse(
                status_code=401,
                content={
                    "error_code": "UNAUTHORIZED",
                    "description": "提供的 API 金鑰無效或已被撤銷，請聯繫系統管理員",
                },
            )

        # 驗證通過：將金鑰資訊注入 request.state 供後續使用
        request.state.api_key = api_key
        request.state.client_id = key_info["client_id"]
        request.state.rate_limit = key_info["rate_limit"]
        request.state.plan = key_info["plan"]

        logger.debug(
            "API 金鑰驗證通過 | 客戶端: %s | 路徑: %s",
            key_info["client_id"],
            request.url.path,
        )

        return await call_next(request)
