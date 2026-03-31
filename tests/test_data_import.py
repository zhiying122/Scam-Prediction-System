"""
資料匯入模組測試

測試 DataImporter、PiiRemover 與 ModelManager 的核心邏輯。
包含單元測試與屬性測試（hypothesis），使用 in-memory 資料結構，
不依賴實際資料庫。

屬性測試：
- 屬性 22：PII 去識別化（需求 7.3）
- 屬性 23：模型版本回滾（需求 7.4）
- 屬性 24：微調摘要報告完整性（需求 7.5）
"""

import uuid
from datetime import datetime, timezone

import pytest
from hypothesis import given, settings, strategies as st

from app.data_import.importer import DataImporter, ImportError as DataImportError
from app.data_import.pii_remover import PiiRemover
from app.prediction_layer.model_manager import ModelManager, ModelVersionRepository


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def importer() -> DataImporter:
    return DataImporter()


@pytest.fixture
def pii_remover() -> PiiRemover:
    return PiiRemover()


@pytest.fixture
def model_manager() -> ModelManager:
    return ModelManager()


@pytest.fixture
def sample_csv_content() -> str:
    return (
        "source,scam_type,description,reported_at\n"
        "警政署,投資詐騙,受害者被誘導投入資金至假投資平台,2024-01-15T10:30:00\n"
        "民間防詐組織,假冒客服,自稱銀行客服要求提供驗證碼,2024-01-16T09:00:00\n"
    )


@pytest.fixture
def sample_json_content() -> str:
    import json
    return json.dumps([
        {
            "source": "警政署",
            "scam_type": "投資詐騙",
            "description": "受害者被誘導投入資金至假投資平台",
            "reported_at": "2024-01-15T10:30:00",
        },
        {
            "source": "民間防詐組織",
            "scam_type": "假冒客服",
            "description": "自稱銀行客服要求提供驗證碼",
            "reported_at": "2024-01-16T09:00:00",
        },
    ], ensure_ascii=False)


@pytest.fixture
def sample_records() -> list[dict]:
    batch_id = str(uuid.uuid4())
    return [
        {
            "id": str(uuid.uuid4()),
            "source": "警政署",
            "scam_type": "投資詐騙",
            "description": "受害者被誘導投入資金至假投資平台",
            "reported_at": "2024-01-15T10:30:00",
            "import_batch_id": batch_id,
            "pii_removed": False,
        }
        for _ in range(5)
    ]


# ── 9.1 DataImporter 單元測試 ─────────────────────────────────────────────────

class TestDataImporterCsv:
    """CSV 格式匯入測試"""

    def test_import_valid_csv(self, importer: DataImporter, sample_csv_content: str) -> None:
        """正常 CSV 匯入應回傳正確筆數"""
        result = importer.import_csv(sample_csv_content)
        assert result.success_count == 2
        assert result.batch_id != ""
        assert len(result.records) == 2

    def test_import_csv_bytes(self, importer: DataImporter, sample_csv_content: str) -> None:
        """支援 bytes 格式輸入"""
        result = importer.import_csv(sample_csv_content.encode("utf-8"))
        assert result.success_count == 2

    def test_import_csv_record_fields(self, importer: DataImporter, sample_csv_content: str) -> None:
        """匯入記錄應包含所有必要欄位"""
        result = importer.import_csv(sample_csv_content)
        record = result.records[0]
        assert "id" in record
        assert "source" in record
        assert "scam_type" in record
        assert "description" in record
        assert "reported_at" in record
        assert "import_batch_id" in record
        assert record["pii_removed"] is False  # 尚未去識別化

    def test_import_csv_missing_required_column(self, importer: DataImporter) -> None:
        """缺少必要欄位應拋出 ImportError"""
        csv_content = "source,scam_type\n警政署,投資詐騙\n"
        with pytest.raises(DataImportError) as exc_info:
            importer.import_csv(csv_content)
        assert exc_info.value.error_code == "INVALID_FORMAT"

    def test_import_csv_empty_file(self, importer: DataImporter) -> None:
        """空 CSV 應拋出 ImportError"""
        with pytest.raises(DataImportError):
            importer.import_csv("")

    def test_import_csv_all_records_same_batch_id(
        self, importer: DataImporter, sample_csv_content: str
    ) -> None:
        """同批次所有記錄應有相同的 batch_id"""
        result = importer.import_csv(sample_csv_content)
        batch_ids = {r["import_batch_id"] for r in result.records}
        assert len(batch_ids) == 1
        assert result.batch_id in batch_ids

    def test_import_csv_bom_encoding(self, importer: DataImporter) -> None:
        """支援 UTF-8 BOM 編碼"""
        csv_content = (
            "source,scam_type,description,reported_at\n"
            "警政署,投資詐騙,測試描述,2024-01-15T10:30:00\n"
        )
        result = importer.import_csv(csv_content.encode("utf-8-sig"))
        assert result.success_count == 1


class TestDataImporterJson:
    """JSON 格式匯入測試"""

    def test_import_valid_json_array(
        self, importer: DataImporter, sample_json_content: str
    ) -> None:
        """正常 JSON 陣列匯入應回傳正確筆數"""
        result = importer.import_json(sample_json_content)
        assert result.success_count == 2

    def test_import_json_with_records_key(self, importer: DataImporter) -> None:
        """支援包含 'records' 鍵的 JSON 物件"""
        import json
        data = {
            "records": [
                {
                    "source": "警政署",
                    "scam_type": "投資詐騙",
                    "description": "測試描述",
                    "reported_at": "2024-01-15T10:30:00",
                }
            ]
        }
        result = importer.import_json(json.dumps(data))
        assert result.success_count == 1

    def test_import_json_with_data_key(self, importer: DataImporter) -> None:
        """支援包含 'data' 鍵的 JSON 物件"""
        import json
        data = {
            "data": [
                {
                    "source": "警政署",
                    "scam_type": "投資詐騙",
                    "description": "測試描述",
                    "reported_at": "2024-01-15T10:30:00",
                }
            ]
        }
        result = importer.import_json(json.dumps(data))
        assert result.success_count == 1

    def test_import_json_invalid_format(self, importer: DataImporter) -> None:
        """無效 JSON 應拋出 ImportError"""
        with pytest.raises(DataImportError) as exc_info:
            importer.import_json("not valid json {{{")
        assert exc_info.value.error_code == "INVALID_FORMAT"

    def test_import_json_empty_array(self, importer: DataImporter) -> None:
        """空 JSON 陣列應拋出 ImportError"""
        with pytest.raises(DataImportError):
            importer.import_json("[]")

    def test_import_auto_csv(self, importer: DataImporter, sample_csv_content: str) -> None:
        """import_auto 應正確路由至 CSV 解析"""
        result = importer.import_auto(sample_csv_content, "csv")
        assert result.success_count == 2

    def test_import_auto_json(
        self, importer: DataImporter, sample_json_content: str
    ) -> None:
        """import_auto 應正確路由至 JSON 解析"""
        result = importer.import_auto(sample_json_content, "json")
        assert result.success_count == 2

    def test_import_auto_unsupported_format(self, importer: DataImporter) -> None:
        """不支援的格式應拋出 ImportError"""
        with pytest.raises(DataImportError) as exc_info:
            importer.import_auto("content", "xml")
        assert exc_info.value.error_code == "UNSUPPORTED_FORMAT"


# ── 9.2 PiiRemover 單元測試 ───────────────────────────────────────────────────

class TestPiiRemover:
    """PII 去識別化測試"""

    def test_remove_email(self, pii_remover: PiiRemover) -> None:
        """應移除電子郵件"""
        text = "請聯絡 victim@example.com 取得更多資訊"
        result, detected = pii_remover.remove_from_text(text)
        assert "victim@example.com" not in result
        assert "[EMAIL]" in result
        assert detected is True

    def test_remove_mobile_phone(self, pii_remover: PiiRemover) -> None:
        """應移除台灣手機號碼"""
        text = "受害者電話：0912345678"
        result, detected = pii_remover.remove_from_text(text)
        assert "0912345678" not in result
        assert detected is True

    def test_remove_mobile_phone_with_dash(self, pii_remover: PiiRemover) -> None:
        """應移除含連字號的手機號碼"""
        text = "聯絡電話 0912-345-678"
        result, detected = pii_remover.remove_from_text(text)
        assert "0912-345-678" not in result
        assert detected is True

    def test_remove_tw_id(self, pii_remover: PiiRemover) -> None:
        """應移除台灣身分證字號"""
        text = "身分證字號 A123456789 已驗證"
        result, detected = pii_remover.remove_from_text(text)
        assert "A123456789" not in result
        assert "[ID_NUMBER]" in result
        assert detected is True

    def test_remove_address(self, pii_remover: PiiRemover) -> None:
        """應移除台灣地址"""
        text = "受害者住址：台北市信義區信義路五段7號"
        result, detected = pii_remover.remove_from_text(text)
        assert "信義路五段7號" not in result
        assert detected is True

    def test_no_pii_text_unchanged(self, pii_remover: PiiRemover) -> None:
        """不含 PII 的文字應保持不變"""
        text = "受害者被誘導投入資金至假投資平台，損失慘重"
        result, detected = pii_remover.remove_from_text(text)
        assert result == text
        assert detected is False

    def test_remove_from_record_sets_pii_removed_true(
        self, pii_remover: PiiRemover
    ) -> None:
        """去識別化後 pii_removed 應設為 True"""
        record = {
            "id": str(uuid.uuid4()),
            "source": "警政署",
            "scam_type": "投資詐騙",
            "description": "受害者電話 0912345678 被詐騙",
            "reported_at": "2024-01-15T10:30:00",
            "import_batch_id": str(uuid.uuid4()),
            "pii_removed": False,
        }
        result = pii_remover.remove_from_record(record)
        assert result["pii_removed"] is True

    def test_remove_from_record_cleans_description(
        self, pii_remover: PiiRemover
    ) -> None:
        """去識別化應清除 description 中的 PII"""
        record = {
            "source": "警政署",
            "scam_type": "投資詐騙",
            "description": "受害者 email: test@mail.com 被詐騙",
            "reported_at": "2024-01-15",
            "import_batch_id": str(uuid.uuid4()),
            "pii_removed": False,
        }
        result = pii_remover.remove_from_record(record)
        assert "test@mail.com" not in result["description"]

    def test_remove_from_batch_all_pii_removed_true(
        self, pii_remover: PiiRemover, sample_records: list[dict]
    ) -> None:
        """批次去識別化後所有記錄的 pii_removed 應為 True"""
        results = pii_remover.remove_from_batch(sample_records)
        assert all(r["pii_removed"] is True for r in results)

    def test_remove_from_batch_preserves_count(
        self, pii_remover: PiiRemover, sample_records: list[dict]
    ) -> None:
        """批次去識別化不應改變記錄數量"""
        results = pii_remover.remove_from_batch(sample_records)
        assert len(results) == len(sample_records)

    def test_contains_pii_detects_email(self, pii_remover: PiiRemover) -> None:
        """contains_pii 應偵測到電子郵件"""
        assert pii_remover.contains_pii("聯絡 user@example.com") is True

    def test_contains_pii_no_pii(self, pii_remover: PiiRemover) -> None:
        """contains_pii 對無 PII 文字應回傳 False"""
        assert pii_remover.contains_pii("一般詐騙描述文字") is False

    def test_empty_text_no_pii(self, pii_remover: PiiRemover) -> None:
        """空字串不應觸發 PII 偵測"""
        result, detected = pii_remover.remove_from_text("")
        assert detected is False


# ── 9.4 ModelManager 單元測試 ─────────────────────────────────────────────────

class TestModelManager:
    """模型版本管理測試"""

    def test_fine_tune_creates_version(
        self, model_manager: ModelManager, sample_records: list[dict]
    ) -> None:
        """微調應建立新版本記錄"""
        summary = model_manager.fine_tune("batch-001", sample_records)
        assert summary.version != ""
        assert summary.training_data_count == len(sample_records)

    def test_fine_tune_records_accuracy(
        self, model_manager: ModelManager, sample_records: list[dict]
    ) -> None:
        """微調摘要應包含準確率資訊"""
        summary = model_manager.fine_tune("batch-001", sample_records)
        assert 0.0 <= summary.accuracy_before <= 1.0
        assert 0.0 <= summary.accuracy_after <= 1.0

    def test_fine_tune_new_version_is_active(
        self, model_manager: ModelManager, sample_records: list[dict]
    ) -> None:
        """微調後新版本應為 is_active=True"""
        model_manager.fine_tune("batch-001", sample_records)
        active = model_manager.get_active_version()
        assert active is not None
        assert active.is_active is True

    def test_fine_tune_only_one_active_version(
        self, model_manager: ModelManager, sample_records: list[dict]
    ) -> None:
        """任何時刻只能有一個 is_active=True 的版本"""
        model_manager.fine_tune("batch-001", sample_records)
        model_manager.fine_tune("batch-002", sample_records)
        all_versions = model_manager.get_all_versions()
        active_count = sum(1 for v in all_versions if v.is_active)
        assert active_count == 1

    def test_fine_tune_empty_records_raises(self, model_manager: ModelManager) -> None:
        """空資料應拋出 ValueError"""
        with pytest.raises(ValueError):
            model_manager.fine_tune("batch-001", [])

    def test_rollback_restores_version(
        self, model_manager: ModelManager, sample_records: list[dict]
    ) -> None:
        """回滾應將指定版本設為 is_active=True"""
        summary_v1 = model_manager.fine_tune("batch-001", sample_records)
        summary_v2 = model_manager.fine_tune("batch-002", sample_records)

        # 確認 v2 為當前版本
        active = model_manager.get_active_version()
        assert active is not None
        assert active.id == summary_v2.version_id

        # 回滾至 v1
        rolled_back = model_manager.rollback(summary_v1.version_id)
        assert rolled_back.is_active is True
        assert rolled_back.id == summary_v1.version_id

    def test_rollback_deactivates_other_versions(
        self, model_manager: ModelManager, sample_records: list[dict]
    ) -> None:
        """回滾後其他版本應為 is_active=False"""
        summary_v1 = model_manager.fine_tune("batch-001", sample_records)
        model_manager.fine_tune("batch-002", sample_records)
        model_manager.rollback(summary_v1.version_id)

        all_versions = model_manager.get_all_versions()
        active_count = sum(1 for v in all_versions if v.is_active)
        assert active_count == 1

    def test_rollback_nonexistent_version_raises(
        self, model_manager: ModelManager
    ) -> None:
        """回滾不存在的版本應拋出 ValueError"""
        with pytest.raises(ValueError):
            model_manager.rollback("nonexistent-id")

    def test_fine_tune_summary_has_all_fields(
        self, model_manager: ModelManager, sample_records: list[dict]
    ) -> None:
        """微調摘要應包含所有必要欄位"""
        summary = model_manager.fine_tune("batch-001", sample_records)
        summary_dict = summary.to_dict()
        assert "training_data_count" in summary_dict
        assert "accuracy_before" in summary_dict
        assert "accuracy_after" in summary_dict
        assert "new_cluster_count" in summary_dict
        assert summary_dict["training_data_count"] is not None
        assert summary_dict["accuracy_before"] is not None
        assert summary_dict["accuracy_after"] is not None
        assert summary_dict["new_cluster_count"] is not None

    def test_operator_notification_called(self, sample_records: list[dict]) -> None:
        """微調完成後應通知已訂閱的 Operator"""
        notifications: list[dict] = []
        manager = ModelManager(operator_notifier=notifications.append)
        manager.subscribe_operator("operator-001")
        manager.fine_tune("batch-001", sample_records)
        assert len(notifications) == 1
        assert notifications[0]["training_data_count"] == len(sample_records)


# ── 屬性測試 ──────────────────────────────────────────────────────────────────

# 屬性 22：PII 去識別化
# Validates: Requirements 7.3

@settings(max_examples=20)
@given(
    st.one_of(
        # 電子郵件（限制為 ASCII 字母，確保符合 email 格式）
        st.builds(
            lambda u, d: f"聯絡 {u}@{d}.com",
            u=st.text(
                alphabet="abcdefghijklmnopqrstuvwxyz",
                min_size=3,
                max_size=10,
            ),
            d=st.text(
                alphabet="abcdefghijklmnopqrstuvwxyz",
                min_size=3,
                max_size=8,
            ),
        ),
        # 手機號碼
        st.builds(
            lambda n: f"電話：09{n:08d}",
            n=st.integers(min_value=0, max_value=99999999),
        ),
        # 身分證字號
        st.builds(
            lambda c, n: f"身分證 {c}{n:09d}",
            c=st.sampled_from(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")),
            n=st.integers(min_value=100000000, max_value=299999999),
        ),
    )
)
def test_pii_removal(pii_text: str) -> None:
    """
    屬性 22：PII 去識別化
    對於任意包含 PII 的文字，去識別化後不得包含原始 PII 值。

    Validates: Requirements 7.3
    """
    # Feature: ai-scam-evolution-prediction, Property 22: PII 去識別化
    remover = PiiRemover()
    result, detected = remover.remove_from_text(pii_text)
    # 去識別化後應偵測到 PII
    assert detected is True
    # 結果不應包含原始 PII 模式（電子郵件、手機、身分證）
    import re
    email_pattern = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
    mobile_pattern = re.compile(r"09\d{8}")
    id_pattern = re.compile(r"\b[A-Z][12]\d{8}\b")
    assert not email_pattern.search(result), f"結果仍含電子郵件：{result}"
    assert not mobile_pattern.search(result), f"結果仍含手機號碼：{result}"
    assert not id_pattern.search(result), f"結果仍含身分證字號：{result}"


# 屬性 23：模型版本回滾（Round-Trip）
# Validates: Requirements 7.4

@settings(max_examples=20)
@given(
    n_finetunes=st.integers(min_value=2, max_value=5),
    rollback_index=st.integers(min_value=0, max_value=4),
)
def test_model_version_rollback(n_finetunes: int, rollback_index: int) -> None:
    """
    屬性 23：模型版本回滾（Round-Trip）
    執行 N 次微調後，回滾至任意版本，is_active 應與目標版本一致。

    Validates: Requirements 7.4
    """
    # Feature: ai-scam-evolution-prediction, Property 23: 模型版本回滾（Round-Trip）
    manager = ModelManager()
    records = [
        {
            "id": str(uuid.uuid4()),
            "source": "警政署",
            "scam_type": "投資詐騙",
            "description": "測試描述",
            "reported_at": "2024-01-15T10:30:00",
            "import_batch_id": "batch-test",
            "pii_removed": True,
        }
    ]

    summaries = []
    for i in range(n_finetunes):
        summary = manager.fine_tune(f"batch-{i}", records)
        summaries.append(summary)

    # 選擇回滾目標（確保索引在範圍內）
    target_index = rollback_index % n_finetunes
    target_summary = summaries[target_index]

    # 執行回滾
    rolled_back = manager.rollback(target_summary.version_id)

    # 驗證：回滾後的版本應為 is_active=True
    assert rolled_back.is_active is True
    assert rolled_back.id == target_summary.version_id

    # 驗證：只有一個版本為 is_active=True
    all_versions = manager.get_all_versions()
    active_versions = [v for v in all_versions if v.is_active]
    assert len(active_versions) == 1
    assert active_versions[0].id == target_summary.version_id


# 屬性 24：微調摘要報告完整性
# Validates: Requirements 7.5

@settings(max_examples=20)
@given(
    record_count=st.integers(min_value=1, max_value=100),
)
def test_finetune_summary_completeness(record_count: int) -> None:
    """
    屬性 24：微調摘要報告完整性
    對於任意完成的微調操作，摘要應包含所有必要欄位且值非空。

    Validates: Requirements 7.5
    """
    # Feature: ai-scam-evolution-prediction, Property 24: 微調摘要報告完整性
    manager = ModelManager()
    records = [
        {
            "id": str(uuid.uuid4()),
            "source": "警政署",
            "scam_type": "投資詐騙",
            "description": f"測試描述 {i}",
            "reported_at": "2024-01-15T10:30:00",
            "import_batch_id": "batch-test",
            "pii_removed": True,
        }
        for i in range(record_count)
    ]

    summary = manager.fine_tune("batch-prop-test", records)
    summary_dict = summary.to_dict()

    # 驗證所有必要欄位存在且非 None
    required_fields = [
        "training_data_count",
        "accuracy_before",
        "accuracy_after",
        "new_cluster_count",
    ]
    for field in required_fields:
        assert field in summary_dict, f"摘要缺少欄位：{field}"
        assert summary_dict[field] is not None, f"欄位 {field} 不可為 None"

    # 驗證數值合法性
    assert summary_dict["training_data_count"] == record_count
    assert 0.0 <= summary_dict["accuracy_before"] <= 1.0
    assert 0.0 <= summary_dict["accuracy_after"] <= 1.0
    assert summary_dict["new_cluster_count"] >= 0
