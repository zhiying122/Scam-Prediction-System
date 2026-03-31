"""
詐騙話術生成路由

提供 POST /v1/scam/generate 端點，觸發詐騙話術變種生成任務。
整合 Access_Controller 授權驗證，確保只有授權操作人員可觸發生成。
生成完成後將 Scam_Script 儲存至 in-memory 列表（模擬 PostgreSQL），
is_regulated 恆設為 True。

需求：1.1、1.4、1.5、5.1
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.access_controller.rbac import Action, Role, check_permission
from app.models.scam_script import ScamScript
from app.scam_engine.generator import generate_scam_samples

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scam", tags=["詐騙話術生成"])

# ── In-Memory 儲存（模擬 PostgreSQL）─────────────────────────────────────────
# 生產環境應替換為實際 PostgreSQL 連線
_scam_scripts_store: list[ScamScript] = []
"""In-memory 詐騙腳本儲存列表（模擬 PostgreSQL，is_regulated 恆為 True）"""


def get_scam_scripts_store() -> list[ScamScript]:
    """取得 in-memory 詐騙腳本儲存列表（供測試注入使用）"""
    return _scam_scripts_store


# ── 請求 / 回應模型 ───────────────────────────────────────────────────────────

class ScamGenerateRequest(BaseModel):
    """詐騙話術生成請求模型"""

    scenario: str = Field(..., min_length=1, description="基礎詐騙情境描述")
    target_audience: str = Field(..., min_length=1, description="目標受眾特徵描述")
    sample_count: int = Field(default=10, ge=10, le=50, description="生成樣本數量（最少 10 個）")
    operator_id: str = Field(..., min_length=1, description="操作人員識別碼")
    operator_role: str = Field(..., min_length=1, description="操作人員角色")


class ScamGenerateResponse(BaseModel):
    """詐騙話術生成回應模型"""

    task_id: str = Field(..., description="非同步任務識別碼")
    status: str = Field(..., description="任務狀態")
    message: str = Field(..., description="狀態說明")
    created_at: str = Field(..., description="任務建立時間（ISO 8601）")


# ── 端點實作 ──────────────────────────────────────────────────────────────────

@router.post(
    "/generate",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ScamGenerateResponse,
    summary="觸發詐騙話術生成任務",
    response_description="非同步任務識別碼與狀態",
)
async def generate_scam_scripts_endpoint(
    request: Request,
    body: ScamGenerateRequest,
) -> ScamGenerateResponse:
    """
    觸發詐騙話術變種生成任務

    1. 呼叫 Access_Controller 驗證操作人員授權（需求 1.4）
    2. 呼叫 Scam_Generation_Engine 生成至少 10 種詐騙對話樣本（需求 1.1）
    3. 將生成的 Scam_Script 儲存至 in-memory 列表，is_regulated 恆為 True（需求 1.5）
    4. 回傳 202 Accepted + task_id

    需求：1.1、1.4、1.5
    """
    task_id = str(uuid.uuid4())

    # ── 步驟 1：Access_Controller 授權驗證（需求 1.4）────────────────────────
    try:
        is_authorized = check_permission(
            operator_id=body.operator_id,
            role=body.operator_role,
            action=Action.READ,
        )
    except ValueError as exc:
        # 角色或操作類型不合法
        logger.warning(
            "授權驗證失敗（不合法角色）| operator_id=%s | role=%s | error=%s",
            body.operator_id, body.operator_role, str(exc)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"授權驗證失敗：{str(exc)}",
        )

    if not is_authorized:
        logger.warning(
            "未授權請求被拒絕 | operator_id=%s | role=%s",
            body.operator_id, body.operator_role
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"操作人員 {body.operator_id} 的角色 {body.operator_role} 無權執行詐騙話術生成",
        )

    logger.info(
        "授權驗證通過 | operator_id=%s | role=%s | task_id=%s",
        body.operator_id, body.operator_role, task_id
    )

    # ── 步驟 2：呼叫 Scam_Generation_Engine 生成樣本（需求 1.1、1.2）─────────
    result = await generate_scam_samples(
        scenario=body.scenario,
        target_audience=body.target_audience,
        min_samples=body.sample_count,
        request_id=task_id,
    )

    # 檢查是否發生錯誤（需求 1.3）
    if "error_code" in result:
        logger.error(
            "詐騙話術生成失敗 | task_id=%s | error_code=%s | description=%s",
            task_id, result["error_code"], result.get("description", "")
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result,
        )

    # ── 步驟 3：儲存 Scam_Script（is_regulated 恆為 True，需求 1.5）──────────
    samples: list[dict[str, Any]] = result.get("samples", [])
    now = datetime.now(timezone.utc)

    for sample in samples:
        script = ScamScript(
            id=str(uuid.uuid4()),
            task_id=task_id,
            content=sample["content"],
            scenario=body.scenario,
            target_audience=sample.get("target_audience", body.target_audience),
            psychological_tags=sample.get("psychological_tags", []),
            language="zh-TW",  # 預設語言（生成引擎使用繁體中文）
            is_regulated=True,  # 恆為 True（需求 1.5）
            created_at=now,
            created_by=body.operator_id,
        )
        _scam_scripts_store.append(script)

    logger.info(
        "Scam_Script 儲存完成 | task_id=%s | count=%d | is_regulated=True",
        task_id, len(samples)
    )

    return ScamGenerateResponse(
        task_id=task_id,
        status="accepted",
        message=f"詐騙話術生成任務已接受，共生成 {len(samples)} 個樣本",
        created_at=now.isoformat(),
    )
