"""
預測預警路由

提供 GET /v1/predictions/alerts 端點，查詢 Prediction_Layer 生成的預警事件列表。

需求：3.2、5.1
"""

from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from app.prediction_layer.alerting import AlertingService

router = APIRouter(prefix="/predictions", tags=["預測預警"])

# 全域共用的 AlertingService 實例（in-memory 儲存）
_alerting_service = AlertingService()


def get_alerting_service() -> AlertingService:
    """取得全域 AlertingService 實例"""
    return _alerting_service


class AlertEventResponse(BaseModel):
    """預警事件回應模型"""

    id: str = Field(..., description="預警事件識別碼")
    risk_level: str = Field(..., description="風險等級（高/中/低）")
    trigger_features: list[str] = Field(..., description="觸發預警的特徵描述列表")
    risk_vector_id: str = Field(..., description="關聯風險向量識別碼")
    notified_at: str = Field(..., description="通知時間（ISO 8601）")
    created_at: str = Field(..., description="建立時間（ISO 8601）")


@router.get(
    "/alerts",
    response_model=list[AlertEventResponse],
    summary="查詢預警事件列表",
    response_description="預警事件列表",
)
async def list_alerts(
    request: Request,
    risk_level: Optional[str] = Query(None, description="風險等級篩選（高/中/低）"),
    limit: int = Query(default=20, ge=1, le=100, description="回傳筆數上限"),
) -> list[AlertEventResponse]:
    """
    查詢 Prediction_Layer 生成的預警事件列表

    支援依風險等級篩選，回傳最新的預警事件。
    回應內容不包含 Scam_Script 的 content 欄位。

    需求：3.2、5.1
    """
    service = get_alerting_service()
    alerts = service.get_alerts(limit=limit * 10)  # 多取一些供篩選後再限制

    # 套用風險等級篩選
    if risk_level:
        alerts = [a for a in alerts if a.risk_level == risk_level]

    # 套用筆數上限
    alerts = alerts[:limit]

    return [
        AlertEventResponse(
            id=a.id,
            risk_level=a.risk_level,
            trigger_features=a.trigger_features,
            risk_vector_id=a.risk_vector_id,
            notified_at=a.notified_at.isoformat(),
            created_at=a.created_at.isoformat(),
        )
        for a in alerts
    ]
