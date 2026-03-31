"""
風險向量查詢路由

提供 GET /v1/risk-vectors 與 GET /v1/risk-vectors/{id} 端點，
供外部客戶端查詢指定時間範圍內的 Risk_Vector。

回應內容僅包含 RiskVector 欄位，不得暴露 Scam_Script 內容。

需求：5.1、5.2、5.5
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.prediction_layer.risk_vector import RiskVectorRepository

router = APIRouter(prefix="/risk-vectors", tags=["風險向量"])

# 全域共用的 in-memory 儲存庫（模擬 PostgreSQL）
_repository = RiskVectorRepository()


def get_repository() -> RiskVectorRepository:
    """取得全域 RiskVectorRepository 實例"""
    return _repository


class RiskVectorResponse(BaseModel):
    """風險向量回應模型（不含 Scam_Script 內容）"""

    id: str = Field(..., description="風險向量識別碼")
    high_risk_features: list[str] = Field(..., description="高風險語意特徵列表")
    scam_cluster_label: str = Field(..., description="詐騙類群標籤")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="風險分數（0.0 ~ 1.0）")
    risk_level: str = Field(..., description="風險等級（高/中/低）")
    time_range_start: str = Field(..., description="分析時間範圍起始（ISO 8601）")
    time_range_end: str = Field(..., description="分析時間範圍結束（ISO 8601）")
    version: str = Field(..., description="模型版本號")
    created_at: str = Field(..., description="建立時間（ISO 8601）")


def _parse_iso_datetime(dt_str: str) -> datetime:
    """解析 ISO 8601 時間字串，回傳帶時區的 datetime"""
    try:
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError as exc:
        raise ValueError(f"無效的時間格式：{dt_str}，請使用 ISO 8601 格式") from exc


@router.get(
    "",
    response_model=list[RiskVectorResponse],
    summary="查詢風險向量列表",
    response_description="指定時間範圍內的風險向量列表",
)
async def list_risk_vectors(
    request: Request,
    start_time: Optional[str] = Query(None, description="查詢起始時間（ISO 8601）"),
    end_time: Optional[str] = Query(None, description="查詢結束時間（ISO 8601）"),
    risk_level: Optional[str] = Query(None, description="風險等級篩選（高/中/低）"),
    limit: int = Query(default=20, ge=1, le=100, description="回傳筆數上限"),
) -> list[RiskVectorResponse]:
    """
    查詢指定時間範圍內的 Risk_Vector 列表

    支援依時間範圍與風險等級篩選，目標回應時間 < 500ms（使用 Redis 快取）。
    回應內容僅包含 RiskVector 欄位，不暴露 Scam_Script 完整對話內容。

    需求：5.1、5.2、5.5
    """
    repo = get_repository()
    vectors = repo.get_all()

    # 解析時間範圍篩選條件
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None

    if start_time:
        try:
            start_dt = _parse_iso_datetime(start_time)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error_code": "INVALID_PARAM", "description": str(exc)},
            ) from exc

    if end_time:
        try:
            end_dt = _parse_iso_datetime(end_time)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error_code": "INVALID_PARAM", "description": str(exc)},
            ) from exc

    # 套用篩選條件
    results = []
    for v in vectors:
        # 時間範圍篩選（依 created_at）
        created = v.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        if start_dt and created < start_dt:
            continue
        if end_dt and created > end_dt:
            continue

        # 風險等級篩選
        if risk_level and v.risk_level != risk_level:
            continue

        results.append(v)

    # 套用筆數上限
    results = results[:limit]

    return [
        RiskVectorResponse(
            id=v.id,
            high_risk_features=v.high_risk_features,
            scam_cluster_label=v.scam_cluster_label,
            risk_score=v.risk_score,
            risk_level=v.risk_level,
            time_range_start=v.time_range_start.isoformat(),
            time_range_end=v.time_range_end.isoformat(),
            version=v.version,
            created_at=v.created_at.isoformat(),
        )
        for v in results
    ]


@router.get(
    "/{vector_id}",
    response_model=RiskVectorResponse,
    summary="查詢單一風險向量",
    response_description="指定 ID 的風險向量詳細資訊",
)
async def get_risk_vector(
    vector_id: str,
    request: Request,
) -> RiskVectorResponse:
    """
    查詢單一 Risk_Vector 詳細資訊

    需求：5.1、5.5
    """
    repo = get_repository()
    vector = repo.get_by_id(vector_id)

    if vector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "description": f"找不到 ID 為 {vector_id} 的風險向量"},
        )

    return RiskVectorResponse(
        id=vector.id,
        high_risk_features=vector.high_risk_features,
        scam_cluster_label=vector.scam_cluster_label,
        risk_score=vector.risk_score,
        risk_level=vector.risk_level,
        time_range_start=vector.time_range_start.isoformat(),
        time_range_end=vector.time_range_end.isoformat(),
        version=vector.version,
        created_at=vector.created_at.isoformat(),
    )
