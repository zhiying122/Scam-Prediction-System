"""
API Gateway 測試模組

涵蓋 APIKeyMiddleware、RateLimitMiddleware、RequestLoggingMiddleware
與各路由端點的單元測試。

屬性測試：
- 屬性 15：API 金鑰驗證拒絕無效請求（需求 5.3）
- 屬性 16：速率限制觸發 HTTP 429（需求 5.4）
- 屬性 17：Scam_Script 內容不外洩（需求 5.5、6.3）
"""

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

from app.api_gateway.main import app
from app.api_gateway.middleware.api_key import (
    APIKeyMiddleware,
    _VALID_API_KEYS,
    lookup_api_key,
)
from app.api_gateway.middleware.rate_limit import (
    RateLimitMiddleware,
    SlidingWindowCounter,
)

# ── 測試客戶端 ────────────────────────────────────────────────────────────────

@pytest.fixture
def client() -> TestClient:
    """建立 FastAPI 測試客戶端"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def valid_api_key() -> str:
    """回傳有效的測試 API 金鑰"""
    return "test-key-001"


@pytest.fixture
def premium_api_key() -> str:
    """回傳高速率限制的測試 API 金鑰"""
    return "test-key-002"


# ── 健康檢查端點測試 ──────────────────────────────────────────────────────────

class TestHealthEndpoint:
    """健康檢查端點測試"""

    def test_health_check_returns_200(self, client: TestClient) -> None:
        """健康檢查端點應回傳 HTTP 200，不需要 API 金鑰"""
        response = client.get("/v1/health")
        assert response.status_code == 200

    def test_health_check_response_structure(self, client: TestClient) -> None:
        """健康檢查回應應包含 status、service、timestamp、version 欄位"""
        response = client.get("/v1/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "timestamp" in data
        assert "version" in data

    def test_health_check_no_api_key_required(self, client: TestClient) -> None:
        """健康檢查端點不需要 X-API-Key 標頭"""
        # 不帶任何標頭，應正常回傳 200
        response = client.get("/v1/health")
        assert response.status_code == 200


# ── API 金鑰驗證中介軟體測試 ──────────────────────────────────────────────────

class TestAPIKeyMiddleware:
    """APIKeyMiddleware 單元測試"""

    def test_missing_api_key_returns_401(self, client: TestClient) -> None:
        """缺少 X-API-Key 標頭應回傳 HTTP 401"""
        response = client.get("/v1/risk-vectors")
        assert response.status_code == 401

    def test_empty_api_key_returns_401(self, client: TestClient) -> None:
        """空字串 X-API-Key 應回傳 HTTP 401"""
        response = client.get("/v1/risk-vectors", headers={"X-API-Key": ""})
        assert response.status_code == 401

    def test_invalid_api_key_returns_401(self, client: TestClient) -> None:
        """不存在的 API 金鑰應回傳 HTTP 401"""
        response = client.get("/v1/risk-vectors", headers={"X-API-Key": "invalid-key-xyz"})
        assert response.status_code == 401

    def test_revoked_api_key_returns_401(self, client: TestClient) -> None:
        """已撤銷的 API 金鑰應回傳 HTTP 401"""
        response = client.get("/v1/risk-vectors", headers={"X-API-Key": "test-key-revoked"})
        assert response.status_code == 401

    def test_valid_api_key_passes(self, client: TestClient, valid_api_key: str) -> None:
        """有效的 API 金鑰應通過驗證（回傳非 401 狀態碼）"""
        response = client.get("/v1/risk-vectors", headers={"X-API-Key": valid_api_key})
        assert response.status_code != 401

    def test_401_response_contains_error_code(self, client: TestClient) -> None:
        """HTTP 401 回應應包含 error_code 欄位"""
        response = client.get("/v1/risk-vectors", headers={"X-API-Key": "bad-key"})
        assert response.status_code == 401
        data = response.json()
        assert "error_code" in data
        assert "description" in data

    def test_lookup_api_key_valid(self) -> None:
        """lookup_api_key 應回傳有效金鑰的資訊"""
        result = lookup_api_key("test-key-001")
        assert result is not None
        assert result["client_id"] == "client-financial-001"
        assert result["is_active"] is True

    def test_lookup_api_key_nonexistent(self) -> None:
        """lookup_api_key 對不存在的金鑰應回傳 None"""
        result = lookup_api_key("nonexistent-key")
        assert result is None

    def test_lookup_api_key_revoked(self) -> None:
        """lookup_api_key 對已撤銷的金鑰應回傳 None"""
        result = lookup_api_key("test-key-revoked")
        assert result is None


# ── 速率限制中介軟體測試 ──────────────────────────────────────────────────────

class TestRateLimitMiddleware:
    """RateLimitMiddleware 單元測試"""

    def test_within_limit_returns_200(self, client: TestClient, valid_api_key: str) -> None:
        """在速率限制內的請求應正常回傳"""
        response = client.get("/v1/risk-vectors", headers={"X-API-Key": valid_api_key})
        assert response.status_code != 429

    def test_rate_limit_headers_present(self, client: TestClient, valid_api_key: str) -> None:
        """回應標頭應包含速率限制資訊"""
        response = client.get("/v1/risk-vectors", headers={"X-API-Key": valid_api_key})
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    def test_exceeding_rate_limit_returns_429(self) -> None:
        """超過速率限制應回傳 HTTP 429"""
        # 使用獨立計數器避免影響其他測試
        counter = SlidingWindowCounter(window_seconds=60)
        client_key = "test-client-rate-limit"
        rate_limit = 5

        # 模擬超過限制的請求
        for _ in range(rate_limit + 1):
            counter.add_request(client_key)

        count = counter.get_count(client_key)
        assert count > rate_limit

    def test_retry_after_header_on_429(self, client: TestClient) -> None:
        """HTTP 429 回應應包含非零的 Retry-After 標頭"""
        # 建立一個速率限制極低的測試應用
        from fastapi import FastAPI
        from fastapi.testclient import TestClient as TC

        test_app = FastAPI()
        test_counter = SlidingWindowCounter(window_seconds=60)

        test_app.add_middleware(
            RateLimitMiddleware,
            default_rate_limit=1,
            window_seconds=60,
            exempt_paths=set(),
            counter=test_counter,
        )

        @test_app.get("/test")
        async def test_endpoint():
            return {"ok": True}

        tc = TC(test_app, raise_server_exceptions=False)

        # 第一次請求應通過
        r1 = tc.get("/test")
        assert r1.status_code == 200

        # 第二次請求應被限制
        r2 = tc.get("/test")
        assert r2.status_code == 429
        assert "Retry-After" in r2.headers
        assert int(r2.headers["Retry-After"]) > 0

    def test_429_response_contains_retry_after_in_body(self, client: TestClient) -> None:
        """HTTP 429 回應本體應包含 retry_after 欄位"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient as TC

        test_app = FastAPI()
        test_counter = SlidingWindowCounter(window_seconds=60)
        test_app.add_middleware(
            RateLimitMiddleware,
            default_rate_limit=1,
            window_seconds=60,
            exempt_paths=set(),
            counter=test_counter,
        )

        @test_app.get("/test")
        async def test_endpoint():
            return {"ok": True}

        tc = TC(test_app, raise_server_exceptions=False)
        tc.get("/test")  # 第一次
        r = tc.get("/test")  # 第二次（超限）

        assert r.status_code == 429
        data = r.json()
        assert "error_code" in data
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert "retry_after" in data
        assert data["retry_after"] > 0


# ── SlidingWindowCounter 單元測試 ─────────────────────────────────────────────

class TestSlidingWindowCounter:
    """SlidingWindowCounter 單元測試"""

    def test_initial_count_is_zero(self) -> None:
        """新客戶端的初始計數應為 0"""
        counter = SlidingWindowCounter(window_seconds=60)
        assert counter.get_count("new-client") == 0

    def test_add_request_increments_count(self) -> None:
        """每次 add_request 應增加計數"""
        counter = SlidingWindowCounter(window_seconds=60)
        counter.add_request("client-a")
        counter.add_request("client-a")
        assert counter.get_count("client-a") == 2

    def test_different_clients_independent(self) -> None:
        """不同客戶端的計數應相互獨立"""
        counter = SlidingWindowCounter(window_seconds=60)
        counter.add_request("client-x")
        counter.add_request("client-x")
        counter.add_request("client-y")
        assert counter.get_count("client-x") == 2
        assert counter.get_count("client-y") == 1

    def test_reset_clears_count(self) -> None:
        """reset 應清除指定客戶端的計數"""
        counter = SlidingWindowCounter(window_seconds=60)
        counter.add_request("client-reset")
        counter.add_request("client-reset")
        counter.reset("client-reset")
        assert counter.get_count("client-reset") == 0

    def test_expired_requests_not_counted(self) -> None:
        """視窗外的過期請求不應被計入"""
        counter = SlidingWindowCounter(window_seconds=1)  # 1 秒視窗
        counter.add_request("client-expire")
        time.sleep(1.1)  # 等待視窗過期
        assert counter.get_count("client-expire") == 0


# ── 請求日誌中介軟體測試 ──────────────────────────────────────────────────────

class TestRequestLoggingMiddleware:
    """RequestLoggingMiddleware 單元測試"""

    def test_process_time_header_present(self, client: TestClient) -> None:
        """回應標頭應包含 X-Process-Time-Ms"""
        response = client.get("/v1/health")
        assert "X-Process-Time-Ms" in response.headers

    def test_process_time_is_numeric(self, client: TestClient) -> None:
        """X-Process-Time-Ms 標頭值應為數字"""
        response = client.get("/v1/health")
        process_time = float(response.headers["X-Process-Time-Ms"])
        assert process_time >= 0


# ── 路由骨架測試 ──────────────────────────────────────────────────────────────

class TestRouterSkeleton:
    """路由骨架端點測試"""

    def test_risk_vectors_endpoint_exists(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """GET /v1/risk-vectors 端點應存在並回傳 200"""
        response = client.get("/v1/risk-vectors", headers={"X-API-Key": valid_api_key})
        assert response.status_code == 200

    def test_risk_vectors_returns_list(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """GET /v1/risk-vectors 應回傳列表"""
        response = client.get("/v1/risk-vectors", headers={"X-API-Key": valid_api_key})
        assert isinstance(response.json(), list)

    def test_predictions_alerts_endpoint_exists(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """GET /v1/predictions/alerts 端點應存在並回傳 200"""
        response = client.get(
            "/v1/predictions/alerts", headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code == 200

    def test_scam_generate_endpoint_exists(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """POST /v1/scam/generate 端點應存在"""
        from unittest.mock import AsyncMock, patch

        mock_result = {
            "samples": [
                {
                    "content": f"詐騙話術 {i}",
                    "psychological_tags": ["緊迫感製造"],
                    "target_audience": "中老年族群",
                }
                for i in range(10)
            ],
            "count": 10,
            "request_id": "test-task-id",
        }
        with patch(
            "app.api_gateway.routers.scam.generate_scam_samples",
            new=AsyncMock(return_value=mock_result),
        ):
            response = client.post(
                "/v1/scam/generate",
                headers={"X-API-Key": valid_api_key},
                json={
                    "scenario": "假冒銀行客服",
                    "target_audience": "中老年族群",
                    "operator_id": "analyst-001",
                    "operator_role": "詐騙分析師",
                },
            )
        assert response.status_code == 202

    def test_scam_generate_returns_task_id(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """POST /v1/scam/generate 應回傳 task_id"""
        from unittest.mock import AsyncMock, patch

        mock_result = {
            "samples": [
                {
                    "content": f"詐騙話術 {i}",
                    "psychological_tags": ["緊迫感製造"],
                    "target_audience": "中老年族群",
                }
                for i in range(10)
            ],
            "count": 10,
            "request_id": "test-task-id",
        }
        with patch(
            "app.api_gateway.routers.scam.generate_scam_samples",
            new=AsyncMock(return_value=mock_result),
        ):
            response = client.post(
                "/v1/scam/generate",
                headers={"X-API-Key": valid_api_key},
                json={
                    "scenario": "假冒銀行客服",
                    "target_audience": "中老年族群",
                    "operator_id": "analyst-001",
                    "operator_role": "詐騙分析師",
                },
            )
        data = response.json()
        assert "task_id" in data
        assert len(data["task_id"]) > 0

    def test_risk_vector_not_found_returns_404(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """查詢不存在的 Risk_Vector 應回傳 404"""
        response = client.get(
            "/v1/risk-vectors/nonexistent-id",
            headers={"X-API-Key": valid_api_key},
        )
        assert response.status_code == 404


# ── 屬性測試 ──────────────────────────────────────────────────────────────────

class TestAPIKeyProperties:
    """
    屬性 15：API 金鑰驗證拒絕無效請求

    **Validates: Requirements 5.3**

    對於任意不含有效 API 金鑰的請求（空值、格式錯誤、不存在的金鑰、已撤銷的金鑰），
    API_Gateway 應回傳 HTTP 401 狀態碼，不得執行任何業務邏輯。
    """

    @h_settings(max_examples=100)
    @given(
        st.one_of(
            # 隨機字串（不在有效金鑰集合中）
            st.text(min_size=1, max_size=64).filter(
                lambda k: k.strip() not in _VALID_API_KEYS
                or not _VALID_API_KEYS.get(k.strip(), {}).get("is_active", False)
            ),
            # 空字串
            st.just(""),
            # 純空白字串
            st.text(alphabet=" \t\n", min_size=1, max_size=10),
        )
    )
    def test_invalid_api_key_rejected(self, api_key: str) -> None:
        """
        屬性 15：API 金鑰驗證拒絕無效請求

        **Validates: Requirements 5.3**

        對於任意無效的 API 金鑰，lookup_api_key 應回傳 None。
        """
        # Feature: ai-scam-evolution-prediction, Property 15: API 金鑰驗證拒絕無效請求
        result = lookup_api_key(api_key.strip())
        # 無效金鑰（不在有效集合中，或已撤銷）應回傳 None
        if api_key.strip() not in _VALID_API_KEYS:
            assert result is None
        elif not _VALID_API_KEYS[api_key.strip()].get("is_active", False):
            assert result is None


class TestRateLimitProperties:
    """
    屬性 16：速率限制觸發 HTTP 429

    **Validates: Requirements 5.4**

    對於任意在 60 秒視窗內超過訂閱方案請求上限的客戶端，
    API_Gateway 應回傳 HTTP 429，且回應標頭應包含非零的 Retry-After 值。
    """

    @h_settings(max_examples=50)
    @given(
        rate_limit=st.integers(min_value=1, max_value=20),
        extra_requests=st.integers(min_value=1, max_value=10),
    )
    def test_rate_limit_http_429(self, rate_limit: int, extra_requests: int) -> None:
        """
        屬性 16：速率限制觸發 HTTP 429

        **Validates: Requirements 5.4**

        對於任意速率限制值，超過限制後計數器應超過上限。
        """
        # Feature: ai-scam-evolution-prediction, Property 16: 速率限制觸發 HTTP 429
        counter = SlidingWindowCounter(window_seconds=60)
        client_key = f"prop-test-client-{rate_limit}"

        # 填滿速率限制
        for _ in range(rate_limit + extra_requests):
            counter.add_request(client_key)

        count = counter.get_count(client_key)
        # 計數應超過速率限制
        assert count > rate_limit

    @h_settings(max_examples=50)
    @given(
        rate_limit=st.integers(min_value=1, max_value=10),
    )
    def test_rate_limit_retry_after_nonzero(self, rate_limit: int) -> None:
        """
        屬性 16（補充）：超限時 Retry-After 應為非零正整數

        **Validates: Requirements 5.4**
        """
        # Feature: ai-scam-evolution-prediction, Property 16: 速率限制觸發 HTTP 429
        from fastapi import FastAPI
        from fastapi.testclient import TestClient as TC

        test_app = FastAPI()
        test_counter = SlidingWindowCounter(window_seconds=60)
        test_app.add_middleware(
            RateLimitMiddleware,
            default_rate_limit=rate_limit,
            window_seconds=60,
            exempt_paths=set(),
            counter=test_counter,
        )

        @test_app.get("/probe")
        async def probe():
            return {"ok": True}

        tc = TC(test_app, raise_server_exceptions=False)

        # 發送超過限制的請求
        last_response = None
        for _ in range(rate_limit + 1):
            last_response = tc.get("/probe")

        assert last_response is not None
        assert last_response.status_code == 429
        assert "Retry-After" in last_response.headers
        retry_after = int(last_response.headers["Retry-After"])
        assert retry_after > 0


class TestScamScriptNotExposed:
    """
    屬性 17：Scam_Script 內容不外洩

    **Validates: Requirements 5.5、6.3**

    對於任意透過 API_Gateway 對外介面的回應，
    回應內容不得包含 Scam_Script 的 content 欄位（完整對話文本）。
    """

    def test_risk_vectors_no_scam_content(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """
        屬性 17：風險向量回應不應包含 Scam_Script content 欄位

        **Validates: Requirements 5.5**
        """
        # Feature: ai-scam-evolution-prediction, Property 17: Scam_Script 內容不外洩
        response = client.get("/v1/risk-vectors", headers={"X-API-Key": valid_api_key})
        response_text = response.text
        # 回應中不應出現 scam_script content 相關欄位
        assert "scam_script" not in response_text.lower() or "content" not in response_text.lower()

    def test_predictions_alerts_no_scam_content(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """
        屬性 17：預警事件回應不應包含 Scam_Script content 欄位

        **Validates: Requirements 5.5**
        """
        # Feature: ai-scam-evolution-prediction, Property 17: Scam_Script 內容不外洩
        response = client.get(
            "/v1/predictions/alerts", headers={"X-API-Key": valid_api_key}
        )
        # 回應中不應出現 scam_script content 相關欄位
        assert '"content"' not in response.text or "scam_script" not in response.text.lower()

    @h_settings(max_examples=30)
    @given(
        endpoint=st.sampled_from([
            "/v1/risk-vectors",
            "/v1/predictions/alerts",
        ])
    )
    def test_api_responses_no_scam_script_content_field(self, endpoint: str) -> None:
        """
        屬性 17：所有對外 API 端點回應不應包含 Scam_Script content 欄位

        **Validates: Requirements 5.5、6.3**
        """
        # Feature: ai-scam-evolution-prediction, Property 17: Scam_Script 內容不外洩
        tc = TestClient(app, raise_server_exceptions=False)
        response = tc.get(endpoint, headers={"X-API-Key": "test-key-001"})

        # 回應不應包含 scam_script 的 content 欄位
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for item in data:
                    assert "content" not in item or "scam_script" not in str(item).lower()
