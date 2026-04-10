"""
速率限制中介軟體

使用 in-memory 滑動視窗計數器模擬 Redis 速率限制。
在 60 秒視窗內超過訂閱方案請求上限時，回傳 HTTP 429 並附上 Retry-After 標頭。

需求：5.4
"""

import logging
import time
from collections import deque
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# 不套用速率限制的路徑白名單
_EXEMPT_PATHS: set[str] = {
    "/v1/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# 預設速率限制（每 60 秒最多請求次數）
_DEFAULT_RATE_LIMIT = 100

# 滑動視窗大小（秒）
_WINDOW_SECONDS = 60


class SlidingWindowCounter:
    """
    滑動視窗計數器

    使用 deque 儲存請求時間戳，模擬 Redis 滑動視窗計數。
    自動清除視窗外的過期時間戳，確保計數準確。
    """

    def __init__(self, window_seconds: int = _WINDOW_SECONDS) -> None:
        """
        初始化滑動視窗計數器

        Args:
            window_seconds: 視窗大小（秒），預設 60 秒
        """
        self.window_seconds = window_seconds
        # 以客戶端識別碼為 key，儲存請求時間戳的 deque
        self._counters: dict[str, deque[float]] = {}

    def _cleanup_expired(self, client_key: str, now: float) -> None:
        """
        清除視窗外的過期時間戳

        Args:
            client_key: 客戶端識別碼
            now: 當前時間戳（Unix 時間）
        """
        if client_key not in self._counters:
            return
        window_start = now - self.window_seconds
        timestamps = self._counters[client_key]
        # 移除視窗起始時間之前的所有時間戳
        while timestamps and timestamps[0] <= window_start:
            timestamps.popleft()

    def add_request(self, client_key: str) -> tuple[int, float]:
        """
        記錄一次請求並回傳當前視窗內的請求數量

        Args:
            client_key: 客戶端識別碼（通常為 API 金鑰或 IP 位址）

        Returns:
            (當前視窗請求數, 最舊請求的時間戳)
        """
        now = time.time()

        if client_key not in self._counters:
            self._counters[client_key] = deque()

        # 清除過期時間戳
        self._cleanup_expired(client_key, now)

        # 記錄本次請求
        self._counters[client_key].append(now)

        timestamps = self._counters[client_key]
        oldest_timestamp = timestamps[0] if timestamps else now
        return len(timestamps), oldest_timestamp

    def get_count(self, client_key: str) -> int:
        """
        取得當前視窗內的請求數量（不記錄新請求）

        Args:
            client_key: 客戶端識別碼

        Returns:
            當前視窗內的請求數量
        """
        now = time.time()
        self._cleanup_expired(client_key, now)
        return len(self._counters.get(client_key, deque()))

    def reset(self, client_key: str) -> None:
        """
        重置指定客戶端的計數器（測試用）

        Args:
            client_key: 客戶端識別碼
        """
        if client_key in self._counters:
            del self._counters[client_key]


# 全域滑動視窗計數器實例（模擬 Redis 共享狀態）
_global_counter = SlidingWindowCounter(window_seconds=_WINDOW_SECONDS)


def get_rate_limit_counter() -> SlidingWindowCounter:
    """
    取得全域速率限制計數器

    Returns:
        全域 SlidingWindowCounter 實例
    """
    return _global_counter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中介軟體

    基於滑動視窗計數器實作速率限制，模擬 Redis 滑動視窗計數。
    超過訂閱方案上限時回傳 HTTP 429，並在回應標頭附上 Retry-After 值。

    客戶端識別優先順序：
    1. request.state.client_id（由 APIKeyMiddleware 注入）
    2. 來源 IP 位址（作為後備識別）
    """

    def __init__(
        self,
        app: ASGIApp,
        default_rate_limit: int = _DEFAULT_RATE_LIMIT,
        window_seconds: int = _WINDOW_SECONDS,
        exempt_paths: set[str] | None = None,
        counter: SlidingWindowCounter | None = None,
    ) -> None:
        """
        初始化速率限制中介軟體

        Args:
            app: ASGI 應用程式實例
            default_rate_limit: 預設每視窗最大請求次數
            window_seconds: 滑動視窗大小（秒）
            exempt_paths: 不套用速率限制的路徑集合
            counter: 自訂計數器實例（測試用，預設使用全域計數器）
        """
        super().__init__(app)
        self.default_rate_limit = default_rate_limit
        self.window_seconds = window_seconds
        self.exempt_paths = exempt_paths if exempt_paths is not None else _EXEMPT_PATHS
        self.counter = counter if counter is not None else _global_counter

    def _get_client_key(self, request: Request) -> str:
        """
        取得客戶端識別碼

        優先使用 APIKeyMiddleware 注入的 client_id，
        若不存在則使用來源 IP 位址。

        Args:
            request: FastAPI 請求物件

        Returns:
            客戶端識別碼字串
        """
        client_id = getattr(request.state, "client_id", None)
        if client_id:
            return f"client:{client_id}"
        # 後備：使用來源 IP
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"

    def _get_rate_limit(self, request: Request) -> int:
        """
        取得客戶端的速率限制值

        優先使用 APIKeyMiddleware 注入的 rate_limit，
        若不存在則使用預設值。

        Args:
            request: FastAPI 請求物件

        Returns:
            每視窗最大請求次數
        """
        return getattr(request.state, "rate_limit", self.default_rate_limit)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        處理請求的核心邏輯

        Args:
            request: FastAPI 請求物件
            call_next: 下一個中介軟體或路由處理函數

        Returns:
            HTTP 回應物件
        """
        # 白名單路徑直接放行
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        client_key = self._get_client_key(request)
        rate_limit = self._get_rate_limit(request)

        # 先檢查當前計數（不記錄本次請求），確保精確限制
        pre_count = self.counter.get_count(client_key)

        # 超過速率限制：回傳 HTTP 429（在記錄請求前檢查，避免多允許一次）
        if pre_count >= rate_limit:
            now = time.time()
            # 估算 Retry-After：取最舊請求的時間戳，計算視窗何時重置
            timestamps = self.counter._counters.get(client_key)
            if timestamps:
                oldest = timestamps[0]
                retry_after = max(1, int(oldest + self.window_seconds - now))
            else:
                retry_after = max(1, self.window_seconds)

            logger.warning(
                "速率限制超過 | 客戶端: %s | 當前計數: %d | 上限: %d | Retry-After: %d 秒",
                client_key,
                pre_count,
                rate_limit,
                retry_after,
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "description": (
                        f"在 {self.window_seconds} 秒視窗內的請求次數已超過訂閱方案上限 "
                        f"（{rate_limit} 次），請稍後再試"
                    ),
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + self.window_seconds)),
                },
            )

        # 記錄本次請求
        current_count, oldest_timestamp = self.counter.add_request(client_key)

        # 在回應標頭附上速率限制資訊
        response = await call_next(request)
        remaining = max(0, rate_limit - current_count)
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int(oldest_timestamp + self.window_seconds)
        )
        return response
