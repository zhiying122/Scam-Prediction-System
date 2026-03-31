"""
API Gateway 主應用程式

建立 FastAPI 應用程式，掛載所有中介軟體與路由。
提供統一入口，負責 API 金鑰驗證、速率限制、請求日誌與路由分發。

需求：5.1、5.2、5.3、5.4
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api_gateway.middleware.api_key import APIKeyMiddleware
from app.api_gateway.middleware.logging import RequestLoggingMiddleware
from app.api_gateway.middleware.rate_limit import RateLimitMiddleware
from app.api_gateway.routers import data, health, predictions, risk_vectors, scam
from app.config import get_settings

# ── 日誌設定 ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

settings = get_settings()


# ── 應用程式生命週期事件 ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """應用程式生命週期管理（啟動與關閉）"""
    logger.info("API Gateway 啟動中 | 環境: %s | 版本: 1.0.0", settings.app_env)
    yield
    logger.info("API Gateway 正在關閉...")


# ── 建立 FastAPI 應用程式 ──────────────────────────────────────────────────────
app = FastAPI(
    lifespan=lifespan,
    title="AI 詐騙進化預測系統 API Gateway",
    description=(
        "主動式防詐情報平台 API，提供風險向量查詢、詐騙話術生成觸發、"
        "報案資料匯入與預警事件查詢等功能。"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── 掛載中介軟體（注意：Starlette 中介軟體以 LIFO 順序執行）────────────────────
# 執行順序（由外到內）：
# 1. RequestLoggingMiddleware（最外層，記錄完整請求週期）
# 2. RateLimitMiddleware（速率限制）
# 3. APIKeyMiddleware（API 金鑰驗證）
# 4. CORSMiddleware（跨域資源共享）
# 5. 路由處理函數（最內層）

# CORS 中介軟體（最先加入 = 最後執行）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境應限制為允許的來源網域
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# API 金鑰驗證中介軟體
app.add_middleware(APIKeyMiddleware)

# 速率限制中介軟體
app.add_middleware(
    RateLimitMiddleware,
    default_rate_limit=settings.api_rate_limit_default,
    window_seconds=settings.api_rate_limit_window_seconds,
)

# 請求日誌中介軟體（最後加入 = 最先執行，確保記錄完整請求週期）
app.add_middleware(RequestLoggingMiddleware)

# ── 掛載路由 ──────────────────────────────────────────────────────────────────
API_PREFIX = "/v1"

# 健康檢查（不需要 API 金鑰）
app.include_router(health.router, prefix=API_PREFIX)

# 業務路由（需要 API 金鑰驗證）
app.include_router(scam.router, prefix=API_PREFIX)
app.include_router(risk_vectors.router, prefix=API_PREFIX)
app.include_router(data.router, prefix=API_PREFIX)
app.include_router(predictions.router, prefix=API_PREFIX)
