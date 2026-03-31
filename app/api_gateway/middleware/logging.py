"""
請求日誌中介軟體

記錄所有 API 請求的時間戳、來源 IP、端點路徑與回應狀態碼。
提供完整的請求追蹤能力，便於監控與除錯。

需求：5.1、5.2
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    請求日誌中介軟體

    攔截所有 HTTP 請求，在請求完成後記錄以下資訊：
    - 時間戳（ISO 8601 格式）
    - 來源 IP 位址
    - HTTP 方法與端點路徑
    - 回應狀態碼
    - 請求處理耗時（毫秒）
    - 客戶端識別碼（若已通過 API 金鑰驗證）
    """

    def __init__(self, app: ASGIApp) -> None:
        """
        初始化請求日誌中介軟體

        Args:
            app: ASGI 應用程式實例
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        處理請求並記錄日誌

        Args:
            request: FastAPI 請求物件
            call_next: 下一個中介軟體或路由處理函數

        Returns:
            HTTP 回應物件
        """
        # 記錄請求開始時間
        start_time = time.time()

        # 取得來源 IP
        client_ip = request.client.host if request.client else "unknown"

        # 取得客戶端識別碼（由 APIKeyMiddleware 注入，若存在）
        client_id = getattr(request.state, "client_id", None)

        # 執行後續中介軟體與路由處理
        response = await call_next(request)

        # 計算處理耗時（毫秒）
        elapsed_ms = (time.time() - start_time) * 1000

        # 記錄請求日誌
        log_parts = [
            f"方法: {request.method}",
            f"路徑: {request.url.path}",
            f"來源 IP: {client_ip}",
            f"狀態碼: {response.status_code}",
            f"耗時: {elapsed_ms:.2f}ms",
        ]
        if client_id:
            log_parts.append(f"客戶端: {client_id}")

        log_message = " | ".join(log_parts)

        # 根據狀態碼選擇日誌等級
        if response.status_code >= 500:
            logger.error(log_message)
        elif response.status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        # 在回應標頭附上處理耗時（便於客戶端監控）
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"

        return response
