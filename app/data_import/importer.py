"""
報案資料匯入模組

支援 CSV 與 JSON 格式的真實報案資料解析與匯入。
匯入後自動執行 PII 去識別化，並透過格式驗證確保資料品質。

需求：7.1
"""

import csv
import io
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# 支援的匯入格式
SUPPORTED_FORMATS = {"csv", "json"}

# CSV 必要欄位（對應 CaseReport 資料模型）
REQUIRED_CSV_COLUMNS = {"source", "scam_type", "description", "reported_at"}


class ImportError(Exception):
    """資料匯入錯誤"""

    def __init__(self, error_code: str, details: list[str]) -> None:
        self.error_code = error_code
        self.details = details
        super().__init__(f"{error_code}: {'; '.join(details)}")


class ImportResult:
    """
    匯入結果

    記錄本次匯入的批次 ID、成功筆數、失敗筆數與錯誤詳情。
    """

    def __init__(
        self,
        batch_id: str,
        records: list[dict[str, Any]],
        errors: list[str] | None = None,
    ) -> None:
        self.batch_id = batch_id
        """匯入批次識別碼"""

        self.records = records
        """成功解析的資料記錄列表"""

        self.errors = errors or []
        """解析過程中的錯誤訊息列表"""

        self.success_count = len(records)
        """成功解析的筆數"""

        self.created_at = datetime.now(timezone.utc)
        """批次建立時間"""


class DataImporter:
    """
    報案資料匯入器

    支援 CSV 與 JSON 格式的報案資料解析，
    解析後回傳標準化的資料記錄列表供後續處理。
    """

    def import_csv(self, content: str | bytes) -> ImportResult:
        """
        解析 CSV 格式報案資料

        Args:
            content: CSV 檔案內容（字串或位元組）

        Returns:
            ImportResult 包含解析後的資料記錄

        Raises:
            ImportError: 若 CSV 格式不符規範或缺少必要欄位
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8-sig")  # 支援 BOM 編碼

        batch_id = str(uuid.uuid4())
        records: list[dict[str, Any]] = []
        errors: list[str] = []

        try:
            reader = csv.DictReader(io.StringIO(content))
        except Exception as exc:
            raise ImportError("INVALID_FORMAT", [f"CSV 解析失敗：{exc}"]) from exc

        # 驗證必要欄位是否存在
        if reader.fieldnames is None:
            raise ImportError("INVALID_FORMAT", ["CSV 檔案為空或缺少標題列"])

        fieldnames_lower = {f.strip().lower() for f in reader.fieldnames if f}
        missing = REQUIRED_CSV_COLUMNS - fieldnames_lower
        if missing:
            raise ImportError(
                "INVALID_FORMAT",
                [f"CSV 缺少必要欄位：{', '.join(sorted(missing))}"],
            )

        for i, row in enumerate(reader, start=1):
            # 正規化欄位名稱（去除空白、轉小寫）
            normalized: dict[str, Any] = {
                k.strip().lower(): v.strip() if isinstance(v, str) else v
                for k, v in row.items()
                if k is not None
            }

            # 驗證非空欄位
            row_errors = self._validate_row(normalized, i)
            if row_errors:
                errors.extend(row_errors)
                continue

            record = self._normalize_record(normalized, batch_id)
            records.append(record)

        if errors and not records:
            raise ImportError("INVALID_FORMAT", errors)

        logger.info(
            "CSV 匯入完成：批次 %s，成功 %d 筆，錯誤 %d 筆",
            batch_id,
            len(records),
            len(errors),
        )
        return ImportResult(batch_id=batch_id, records=records, errors=errors)

    def import_json(self, content: str | bytes) -> ImportResult:
        """
        解析 JSON 格式報案資料

        Args:
            content: JSON 檔案內容（字串或位元組）

        Returns:
            ImportResult 包含解析後的資料記錄

        Raises:
            ImportError: 若 JSON 格式不符規範
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8")

        batch_id = str(uuid.uuid4())

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ImportError("INVALID_FORMAT", [f"JSON 解析失敗：{exc}"]) from exc

        # 支援頂層為列表或包含 records/data 鍵的字典
        if isinstance(data, dict):
            if "records" in data:
                data = data["records"]
            elif "data" in data:
                data = data["data"]
            else:
                data = [data]  # 單筆記錄包裝為列表

        if not isinstance(data, list):
            raise ImportError(
                "INVALID_FORMAT",
                ["JSON 資料必須為陣列格式或包含 'records'/'data' 鍵的物件"],
            )

        if len(data) == 0:
            raise ImportError("INVALID_FORMAT", ["JSON 資料陣列不可為空"])

        records: list[dict[str, Any]] = []
        errors: list[str] = []

        for i, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                errors.append(f"第 {i} 筆：資料必須為物件格式，實際型別：{type(item).__name__}")
                continue

            # 正規化欄位名稱
            normalized: dict[str, Any] = {
                k.strip().lower(): v for k, v in item.items()
            }

            row_errors = self._validate_row(normalized, i)
            if row_errors:
                errors.extend(row_errors)
                continue

            record = self._normalize_record(normalized, batch_id)
            records.append(record)

        if errors and not records:
            raise ImportError("INVALID_FORMAT", errors)

        logger.info(
            "JSON 匯入完成：批次 %s，成功 %d 筆，錯誤 %d 筆",
            batch_id,
            len(records),
            len(errors),
        )
        return ImportResult(batch_id=batch_id, records=records, errors=errors)

    def import_auto(self, content: str | bytes, fmt: str) -> ImportResult:
        """
        自動依格式匯入報案資料

        Args:
            content: 檔案內容
            fmt: 格式字串（'csv' 或 'json'）

        Returns:
            ImportResult

        Raises:
            ImportError: 若格式不支援
        """
        fmt = fmt.lower().strip()
        if fmt == "csv":
            return self.import_csv(content)
        elif fmt == "json":
            return self.import_json(content)
        else:
            raise ImportError(
                "UNSUPPORTED_FORMAT",
                [f"不支援的格式：'{fmt}'，僅支援 csv 或 json"],
            )

    # ── 私有輔助方法 ──────────────────────────────────────────────────────────

    def _validate_row(self, row: dict[str, Any], index: int) -> list[str]:
        """驗證單筆資料的必要欄位"""
        errors: list[str] = []
        for field in REQUIRED_CSV_COLUMNS:
            value = row.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"第 {index} 筆：欄位 '{field}' 不可為空")
        return errors

    def _normalize_record(
        self, row: dict[str, Any], batch_id: str
    ) -> dict[str, Any]:
        """將原始列資料正規化為標準記錄格式"""
        return {
            "id": str(uuid.uuid4()),
            "source": str(row.get("source", "")).strip(),
            "scam_type": str(row.get("scam_type", "")).strip(),
            "description": str(row.get("description", "")).strip(),
            "reported_at": str(row.get("reported_at", "")).strip(),
            "import_batch_id": batch_id,
            "pii_removed": False,  # 尚未執行去識別化
        }
