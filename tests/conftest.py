"""
測試共用 Fixtures

提供所有測試模組共用的測試資料庫連線、mock LLM 客戶端、
測試資料工廠等基礎設施。
"""

import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.config import Settings


# ── 測試用設定覆寫 ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    測試環境設定

    覆寫預設設定，使用測試專用的資料庫與服務連線。
    """
    return Settings(
        app_env="testing",
        debug=True,
        postgres_host="localhost",
        postgres_port=5432,
        postgres_db="scam_prediction_test",
        postgres_user="postgres",
        postgres_password="postgres",
        redis_host="localhost",
        redis_port=6379,
        redis_db=1,  # 使用獨立的 Redis DB 避免污染開發資料
        qdrant_host="localhost",
        qdrant_port=6333,
        qdrant_collection_name="semantic_vectors_test",
        openai_api_key="test-api-key-not-real",
    )


# ── Mock LLM 客戶端 ────────────────────────────────────────────────────────────

@pytest.fixture
def mock_llm_response() -> dict:
    """
    模擬 LLM 回傳的詐騙話術生成結果

    回傳包含 10 個詐騙對話樣本的結構化 JSON，
    每個樣本包含話術文本、心理操控類別標籤與目標受眾描述。
    """
    return {
        "samples": [
            {
                "content": f"測試詐騙話術樣本 {i}：您的帳戶異常，請立即點擊連結驗證身份。",
                "psychological_tags": ["緊迫感製造", "權威偽裝"],
                "target_audience": "中老年族群",
            }
            for i in range(1, 11)  # 生成 10 個樣本（符合需求 1.1 最少 10 個）
        ]
    }


@pytest.fixture
def mock_llm_client(mock_llm_response: dict) -> Generator[MagicMock, None, None]:
    """
    Mock LangChain LLM 客戶端

    攔截所有 LLM API 呼叫，回傳預設的測試回應，
    避免測試過程中產生實際 API 費用。
    """
    with patch("langchain_openai.ChatOpenAI") as mock_class:
        mock_instance = MagicMock()
        mock_instance.invoke = MagicMock(
            return_value=MagicMock(content=str(mock_llm_response))
        )
        mock_instance.ainvoke = AsyncMock(
            return_value=MagicMock(content=str(mock_llm_response))
        )
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_llm_timeout() -> Generator[MagicMock, None, None]:
    """
    模擬 LLM API 逾時情境

    用於測試逾時錯誤處理邏輯（需求 1.3）。
    """
    import asyncio

    with patch("langchain_openai.ChatOpenAI") as mock_class:
        mock_instance = MagicMock()
        mock_instance.ainvoke = AsyncMock(side_effect=asyncio.TimeoutError("LLM 回應逾時"))
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_llm_api_error() -> Generator[MagicMock, None, None]:
    """
    模擬 LLM API 錯誤情境

    用於測試 API 錯誤處理邏輯（需求 1.3）。
    """
    from openai import APIError

    with patch("langchain_openai.ChatOpenAI") as mock_class:
        mock_instance = MagicMock()
        mock_instance.ainvoke = AsyncMock(
            side_effect=APIError("API 服務錯誤", request=MagicMock(), body=None)
        )
        mock_class.return_value = mock_instance
        yield mock_instance


# ── 測試資料工廠 ───────────────────────────────────────────────────────────────

@pytest.fixture
def sample_scam_script_data() -> dict:
    """
    建立測試用 ScamScript 資料字典

    提供符合資料模型規格的測試資料，
    is_regulated 恆為 True（需求 1.5）。
    """
    return {
        "id": str(uuid.uuid4()),
        "task_id": str(uuid.uuid4()),
        "content": "您好，我是銀行客服，您的帳戶發現異常交易，請立即提供驗證碼。",
        "scenario": "假冒銀行客服",
        "target_audience": "中老年族群",
        "psychological_tags": ["權威偽裝", "緊迫感製造"],
        "language": "zh-TW",
        "is_regulated": True,  # 恆為 True
        "created_at": datetime.now(timezone.utc),
        "created_by": "operator-001",
    }


@pytest.fixture
def sample_risk_vector_data() -> dict:
    """
    建立測試用 RiskVector 資料字典

    風險分數在 [0.0, 1.0] 範圍內，風險等級為高/中/低之一。
    """
    now = datetime.now(timezone.utc)
    return {
        "id": str(uuid.uuid4()),
        "high_risk_features": ["緊迫感製造", "假冒官方機構", "要求提供驗證碼"],
        "scam_cluster_label": "假冒客服詐騙",
        "risk_score": 0.85,
        "risk_level": "高",
        "time_range_start": now.replace(hour=0, minute=0, second=0),
        "time_range_end": now,
        "version": "1.0.0",
        "created_at": now,
    }


@pytest.fixture
def sample_alert_event_data(sample_risk_vector_data: dict) -> dict:
    """
    建立測試用 AlertEvent 資料字典

    風險等級為高/中/低之一，觸發特徵至少一個非空項目。
    """
    now = datetime.now(timezone.utc)
    return {
        "id": str(uuid.uuid4()),
        "risk_level": "高",
        "trigger_features": ["新型假冒客服話術出現頻率異常上升"],
        "risk_vector_id": sample_risk_vector_data["id"],
        "notified_operators": ["operator-001", "operator-002"],
        "notified_at": now,
        "created_at": now,
    }


@pytest.fixture
def sample_access_log_data() -> dict:
    """
    建立測試用 AccessLog 資料字典

    包含操作人員識別碼、操作類型與雜湊鏈欄位。
    """
    return {
        "id": str(uuid.uuid4()),
        "operator_id": "operator-001",
        "action": "read",
        "resource_id": str(uuid.uuid4()),
        "resource_type": "scam_script",
        "timestamp": datetime.now(timezone.utc),
        "prev_hash": "0" * 64,  # 創世雜湊（第一筆記錄）
        "current_hash": "a" * 64,  # 模擬 SHA-256 雜湊值
    }


@pytest.fixture
def sample_case_report_data() -> dict:
    """
    建立測試用 CaseReport 資料字典

    pii_removed 標記是否已完成去識別化（需求 7.3）。
    """
    return {
        "id": str(uuid.uuid4()),
        "source": "警政署",
        "scam_type": "投資詐騙",
        "description": "受害者接到自稱投資顧問的電話，被誘導投入大量資金至假投資平台。",
        "reported_at": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        "import_batch_id": str(uuid.uuid4()),
        "pii_removed": True,
    }


@pytest.fixture
def sample_model_version_data() -> dict:
    """
    建立測試用 ModelVersion 資料字典

    準確率在 [0.0, 1.0] 範圍內，is_active 標記當前版本。
    """
    return {
        "id": str(uuid.uuid4()),
        "version": "1.0.0",
        "accuracy_before": 0.75,
        "accuracy_after": 0.82,
        "training_data_count": 500,
        "new_cluster_count": 3,
        "created_at": datetime.now(timezone.utc),
        "created_by": "admin-001",
        "is_active": True,
    }


# ── Mock 資料庫連線 ────────────────────────────────────────────────────────────

@pytest.fixture
def mock_redis_client() -> Generator[MagicMock, None, None]:
    """
    Mock Redis 客戶端

    攔截所有 Redis 操作，避免測試依賴實際 Redis 服務。
    """
    with patch("redis.asyncio.from_url") as mock_redis:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=None)
        mock_client.set = AsyncMock(return_value=True)
        mock_client.incr = AsyncMock(return_value=1)
        mock_client.expire = AsyncMock(return_value=True)
        mock_client.ttl = AsyncMock(return_value=60)
        mock_client.delete = AsyncMock(return_value=1)
        mock_redis.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_qdrant_client() -> Generator[MagicMock, None, None]:
    """
    Mock Qdrant 向量資料庫客戶端

    攔截所有向量資料庫操作，避免測試依賴實際 Qdrant 服務。
    """
    with patch("qdrant_client.QdrantClient") as mock_class:
        mock_instance = MagicMock()
        mock_instance.upsert = MagicMock(return_value=MagicMock(status="completed"))
        mock_instance.search = MagicMock(return_value=[])
        mock_instance.get_collection = MagicMock(return_value=MagicMock())
        mock_class.return_value = mock_instance
        yield mock_instance
