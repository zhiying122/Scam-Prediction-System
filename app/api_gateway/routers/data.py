"""
資料匯入路由

提供 POST /v1/data/import 端點，供管理員匯入真實報案資料。
支援 CSV 與 JSON 格式，匯入前自動執行 PII 去識別化。

需求：7.1、7.3
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from app.data_import.importer import DataImporter, ImportError as DataImportError
from app.data_import.pii_remover import PiiRemover

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["資料匯入"])

# 模組層級的匯入器與去識別化處理器（可透過依賴注入替換）
_importer = DataImporter()
_pii_remover = PiiRemover()

# ── In-Memory 儲存（模擬 PostgreSQL）─────────────────────────────────────────
# ⚠️ 此 in-memory 儲存僅供 development/testing 環境使用。
# production 環境應切換至 PostgreSQL 以確保匯入資料持久化。
_imported_records_store: list[dict] = []
"""PII 去識別化後的匯入資料儲存列表"""


def get_imported_records_store() -> list[dict]:
    """取得 in-memory 匯入資料儲存列表（供其他模組存取或測試注入使用）"""
    return _imported_records_store


class DataImportResponse(BaseModel):
    """資料匯入回應模型"""

    batch_id: str = Field(..., description="匯入批次識別碼")
    status: str = Field(..., description="匯入狀態")
    message: str = Field(..., description="狀態說明")
    record_count: int = Field(..., description="成功匯入的資料筆數")
    created_at: str = Field(..., description="批次建立時間（ISO 8601）")


@router.post(
    "/import",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DataImportResponse,
    summary="匯入真實報案資料",
    response_description="匯入批次識別碼與狀態",
)
async def import_case_data(
    request: Request,
    file: UploadFile = File(..., description="報案資料檔案（CSV 或 JSON 格式）"),
) -> DataImportResponse:
    """
    匯入真實報案資料

    接受 CSV 或 JSON 格式的報案資料檔案，
    自動執行 PII 去識別化後觸發模型增量微調。

    需求：7.1、7.3
    """
    # 判斷格式
    content_type = file.content_type or ""
    filename = file.filename or ""

    if content_type == "text/csv" or filename.endswith(".csv"):
        fmt = "csv"
    elif content_type == "application/json" or filename.endswith(".json"):
        fmt = "json"
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "INVALID_FORMAT",
                "description": "僅支援 CSV（text/csv）或 JSON（application/json）格式",
            },
        )

    # 讀取檔案內容
    content = await file.read()

    # 執行匯入解析
    try:
        result = _importer.import_auto(content, fmt)
    except DataImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": exc.error_code,
                "description": "資料格式驗證失敗",
                "details": exc.details,
            },
        ) from exc

    # 執行 PII 去識別化
    cleaned_records = _pii_remover.remove_from_batch(result.records)

    # 儲存清理後的資料至 in-memory store（模擬 PostgreSQL 持久化）
    _imported_records_store.extend(cleaned_records)

    logger.info(
        "資料匯入完成：批次 %s，共 %d 筆，PII 去識別化完成，已儲存至 store（累計 %d 筆）",
        result.batch_id,
        len(cleaned_records),
        len(_imported_records_store),
    )

    return DataImportResponse(
        batch_id=result.batch_id,
        status="accepted",
        message="報案資料匯入任務已接受，PII 去識別化完成，等待模型微調排程",
        record_count=len(cleaned_records),
        created_at=result.created_at.isoformat(),
    )
