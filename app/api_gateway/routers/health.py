"""
健康檢查路由

提供 GET /v1/health 端點，供負載平衡器與監控系統確認服務狀態。

需求：5.1
"""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["健康檢查"])


@router.get("/health", summary="健康檢查", response_description="服務狀態資訊")
async def health_check() -> dict:
    """
    健康檢查端點

    回傳服務當前狀態與時間戳，不需要 API 金鑰驗證。
    供負載平衡器、Kubernetes liveness probe 或監控系統使用。

    Returns:
        包含服務狀態與時間戳的字典
    """
    return {
        "status": "healthy",
        "service": "AI 詐騙進化預測系統 API Gateway",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }
