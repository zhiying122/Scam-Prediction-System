"""
報案資料格式驗證模組

驗證匯入的真實報案資料批次是否符合系統規範。
格式不符時拒絕整批資料，回傳包含具體錯誤說明的回應。
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# 必要欄位定義：欄位名稱 -> 期望型別
REQUIRED_FIELDS: dict[str, type] = {
    "source": str,
    "scam_type": str,
    "description": str,
    "reported_at": (str, datetime),  # type: ignore[assignment]
    "import_batch_id": str,
    "pii_removed": bool,
}

# 非空字串欄位（不允許空字串）
NON_EMPTY_STRING_FIELDS = {"source", "scam_type", "description", "import_batch_id"}


def validate_single_record(record: Any, index: int) -> list[str]:
    """
    驗證單筆報案資料

    Args:
        record: 要驗證的資料記錄
        index: 記錄在批次中的索引（用於錯誤訊息）

    Returns:
        錯誤訊息列表（空列表表示驗證通過）
    """
    errors: list[str] = []

    if not isinstance(record, dict):
        return [f"第 {index} 筆：資料必須為字典格式，實際型別：{type(record).__name__}"]

    # 檢查必要欄位是否存在
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"第 {index} 筆：缺少必要欄位 '{field}'")

    if errors:
        return errors

    # 檢查資料型別
    for field, expected_type in REQUIRED_FIELDS.items():
        value = record.get(field)
        if value is None:
            errors.append(f"第 {index} 筆：欄位 '{field}' 不可為 None")
            continue

        # reported_at 允許 str 或 datetime
        if field == "reported_at":
            if not isinstance(value, (str, datetime)):
                errors.append(
                    f"第 {index} 筆：欄位 'reported_at' 型別錯誤，"
                    f"期望 str 或 datetime，實際：{type(value).__name__}"
                )
            elif isinstance(value, str):
                # 嘗試解析日期字串
                try:
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    errors.append(
                        f"第 {index} 筆：欄位 'reported_at' 日期格式無效，"
                        f"期望 ISO 8601 格式，實際值：'{value}'"
                    )
        elif field == "pii_removed":
            if not isinstance(value, bool):
                errors.append(
                    f"第 {index} 筆：欄位 'pii_removed' 型別錯誤，"
                    f"期望 bool，實際：{type(value).__name__}"
                )
        else:
            if not isinstance(value, str):
                errors.append(
                    f"第 {index} 筆：欄位 '{field}' 型別錯誤，"
                    f"期望 str，實際：{type(value).__name__}"
                )

    # 檢查非空字串欄位
    for field in NON_EMPTY_STRING_FIELDS:
        value = record.get(field)
        if isinstance(value, str) and not value.strip():
            errors.append(f"第 {index} 筆：欄位 '{field}' 不可為空字串")

    return errors


def validate_case_report_batch(data: Any) -> dict[str, Any]:
    """
    驗證報案資料批次格式

    驗證必要欄位與資料型別，格式不符時拒絕整批資料。

    Args:
        data: 要驗證的資料批次（應為字典列表）

    Returns:
        驗證結果字典，包含：
        - valid (bool): 是否通過驗證
        - error_code (str | None): 錯誤代碼（通過時為 None）
        - details (list[str]): 具體錯誤說明列表
        - accepted_count (int): 接受的記錄數（通過時為批次大小，失敗時為 0）
        - rejected_count (int): 拒絕的記錄數（通過時為 0，失敗時為批次大小）
    """
    # 檢查頂層資料型別
    if not isinstance(data, list):
        return {
            "valid": False,
            "error_code": "INVALID_FORMAT",
            "details": [
                f"批次資料必須為列表格式，實際型別：{type(data).__name__}"
            ],
            "accepted_count": 0,
            "rejected_count": 1,
        }

    if len(data) == 0:
        return {
            "valid": False,
            "error_code": "EMPTY_BATCH",
            "details": ["批次資料不可為空列表"],
            "accepted_count": 0,
            "rejected_count": 0,
        }

    # 逐筆驗證
    all_errors: list[str] = []
    for i, record in enumerate(data):
        record_errors = validate_single_record(record, i + 1)
        all_errors.extend(record_errors)

    if all_errors:
        logger.warning(
            "報案資料批次驗證失敗：%d 筆資料，%d 個錯誤",
            len(data),
            len(all_errors),
        )
        return {
            "valid": False,
            "error_code": "INVALID_FORMAT",
            "details": all_errors,
            "accepted_count": 0,
            "rejected_count": len(data),
        }

    logger.info("報案資料批次驗證通過：%d 筆資料", len(data))
    return {
        "valid": True,
        "error_code": None,
        "details": [],
        "accepted_count": len(data),
        "rejected_count": 0,
    }
