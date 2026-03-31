"""
Scam_Generation_Engine 單元測試

測試詐騙話術生成引擎的核心邏輯，包含：
- LLM 呼叫與 Prompt 模板（任務 4.1）
- 錯誤處理與結構化錯誤回應（任務 4.3）
- Access_Controller 授權驗證與 Scam_Script 受管制標記（任務 4.5）

使用 mock LLM 客戶端，避免實際 API 呼叫。
需求：1.1、1.2、1.3、1.4、1.5
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api_gateway.main import app
from app.api_gateway.routers.scam import _scam_scripts_store
from app.scam_engine.generator import (
    LLMErrorCode,
    ScamSample,
    _call_llm_with_retry,
    _parse_llm_response,
    _validate_samples,
    build_error_response,
    generate_scam_samples,
)


# ── 測試用 LLM 回應資料 ───────────────────────────────────────────────────────

def _make_llm_response_json(count: int = 10) -> str:
    """建立模擬 LLM 回傳的 JSON 字串"""
    samples = [
        {
            "content": f"詐騙話術樣本 {i}：您的帳戶發現異常，請立即點擊連結驗證身份，否則帳戶將被凍結。",
            "psychological_tags": ["緊迫感製造", "權威偽裝"],
            "target_audience": "中老年族群",
        }
        for i in range(1, count + 1)
    ]
    return json.dumps({"samples": samples}, ensure_ascii=False)


def _make_mock_llm(response_content: str) -> MagicMock:
    """建立回傳指定內容的 mock LLM 客戶端"""
    mock = MagicMock()
    mock.ainvoke = AsyncMock(
        return_value=MagicMock(content=response_content)
    )
    return mock


# ── build_error_response 測試 ─────────────────────────────────────────────────

class TestBuildErrorResponse:
    """測試結構化錯誤回應建構函數"""

    def test_包含必要欄位(self):
        """錯誤回應應包含 error_code、description、timestamp、request_id"""
        result = build_error_response(
            error_code="LLM_TIMEOUT",
            description="LLM 服務逾時",
        )
        assert "error_code" in result
        assert "description" in result
        assert "timestamp" in result
        assert "request_id" in result

    def test_error_code_正確(self):
        """error_code 應與傳入值一致"""
        result = build_error_response(
            error_code=LLMErrorCode.TIMEOUT,
            description="逾時",
        )
        assert result["error_code"] == LLMErrorCode.TIMEOUT

    def test_description_非空(self):
        """description 應為非空字串"""
        result = build_error_response(
            error_code="LLM_API_ERROR",
            description="API 錯誤",
        )
        assert result["description"] == "API 錯誤"

    def test_timestamp_為_ISO8601格式(self):
        """timestamp 應為合法的 ISO 8601 格式"""
        result = build_error_response(
            error_code="LLM_TIMEOUT",
            description="逾時",
        )
        # 嘗試解析 timestamp，若格式錯誤會拋出例外
        datetime.fromisoformat(result["timestamp"])

    def test_自訂_request_id(self):
        """傳入自訂 request_id 時應使用該值"""
        custom_id = "test-request-id-123"
        result = build_error_response(
            error_code="LLM_TIMEOUT",
            description="逾時",
            request_id=custom_id,
        )
        assert result["request_id"] == custom_id

    def test_自動生成_request_id(self):
        """未傳入 request_id 時應自動生成 UUID"""
        result = build_error_response(
            error_code="LLM_TIMEOUT",
            description="逾時",
        )
        # 驗證為合法 UUID 格式
        uuid.UUID(result["request_id"])

    def test_包含_retry_after(self):
        """傳入 retry_after 時應包含在回應中"""
        result = build_error_response(
            error_code="LLM_TIMEOUT",
            description="逾時",
            retry_after=30,
        )
        assert result["retry_after"] == 30

    def test_不傳_retry_after_時不包含該欄位(self):
        """未傳入 retry_after 時回應不應包含該欄位"""
        result = build_error_response(
            error_code="LLM_API_ERROR",
            description="API 錯誤",
        )
        assert "retry_after" not in result


# ── _parse_llm_response 測試 ──────────────────────────────────────────────────

class TestParseLLMResponse:
    """測試 LLM 回應 JSON 解析函數"""

    def test_解析合法JSON(self):
        """合法 JSON 格式應正確解析"""
        raw = _make_llm_response_json(10)
        samples = _parse_llm_response(raw)
        assert len(samples) == 10

    def test_解析含額外文字的回應(self):
        """LLM 回應包含額外說明文字時仍應正確解析"""
        json_part = _make_llm_response_json(5)
        raw = f"以下是生成的詐騙話術樣本：\n{json_part}\n請注意這些僅供研究使用。"
        samples = _parse_llm_response(raw)
        assert len(samples) == 5

    def test_無效JSON拋出ValueError(self):
        """無效 JSON 應拋出 ValueError"""
        with pytest.raises(ValueError):
            _parse_llm_response("這不是 JSON 格式的回應")

    def test_缺少samples欄位拋出ValueError(self):
        """缺少 samples 欄位應拋出 ValueError"""
        with pytest.raises(ValueError):
            _parse_llm_response('{"data": []}')


# ── _validate_samples 測試 ────────────────────────────────────────────────────

class TestValidateSamples:
    """測試詐騙樣本驗證函數"""

    def test_合法樣本通過驗證(self):
        """所有欄位合法的樣本應通過驗證"""
        raw = [
            {
                "content": "您的帳戶異常，請立即驗證",
                "psychological_tags": ["緊迫感製造"],
                "target_audience": "中老年族群",
            }
        ]
        result = _validate_samples(raw)
        assert len(result) == 1
        assert isinstance(result[0], ScamSample)

    def test_空content被跳過(self):
        """content 為空的樣本應被跳過"""
        raw = [
            {
                "content": "",
                "psychological_tags": ["緊迫感製造"],
                "target_audience": "中老年族群",
            }
        ]
        result = _validate_samples(raw)
        assert len(result) == 0

    def test_空tags被跳過(self):
        """psychological_tags 為空的樣本應被跳過"""
        raw = [
            {
                "content": "詐騙話術",
                "psychological_tags": [],
                "target_audience": "中老年族群",
            }
        ]
        result = _validate_samples(raw)
        assert len(result) == 0

    def test_空audience被跳過(self):
        """target_audience 為空的樣本應被跳過"""
        raw = [
            {
                "content": "詐騙話術",
                "psychological_tags": ["緊迫感製造"],
                "target_audience": "",
            }
        ]
        result = _validate_samples(raw)
        assert len(result) == 0

    def test_混合合法與不合法樣本(self):
        """混合合法與不合法樣本時，只有合法樣本通過"""
        raw = [
            {
                "content": "合法樣本",
                "psychological_tags": ["信任建立"],
                "target_audience": "年輕族群",
            },
            {
                "content": "",  # 不合法：空 content
                "psychological_tags": ["緊迫感製造"],
                "target_audience": "中老年族群",
            },
        ]
        result = _validate_samples(raw)
        assert len(result) == 1
        assert result[0].content == "合法樣本"


# ── generate_scam_samples 測試 ────────────────────────────────────────────────

class TestGenerateScamSamples:
    """測試詐騙話術生成主函數"""

    @pytest.mark.asyncio
    async def test_成功生成10個樣本(self):
        """正常情況下應成功生成至少 10 個樣本（需求 1.1）"""
        mock_llm = _make_mock_llm(_make_llm_response_json(10))

        result = await generate_scam_samples(
            scenario="假冒銀行客服",
            target_audience="中老年族群",
            min_samples=10,
            llm_client=mock_llm,
        )

        assert "error_code" not in result
        assert "samples" in result
        assert result["count"] >= 10
        assert len(result["samples"]) >= 10

    @pytest.mark.asyncio
    async def test_每個樣本包含必要欄位(self):
        """每個樣本應包含 content、psychological_tags、target_audience（需求 1.1）"""
        mock_llm = _make_mock_llm(_make_llm_response_json(10))

        result = await generate_scam_samples(
            scenario="投資詐騙",
            target_audience="年輕投資者",
            llm_client=mock_llm,
        )

        for sample in result["samples"]:
            assert "content" in sample
            assert "psychological_tags" in sample
            assert "target_audience" in sample
            assert sample["content"]  # 非空
            assert sample["psychological_tags"]  # 非空列表
            assert sample["target_audience"]  # 非空

    @pytest.mark.asyncio
    async def test_回傳包含request_id(self):
        """成功回應應包含 request_id"""
        mock_llm = _make_mock_llm(_make_llm_response_json(10))

        result = await generate_scam_samples(
            scenario="假冒政府機關",
            target_audience="一般民眾",
            request_id="test-req-001",
            llm_client=mock_llm,
        )

        assert result["request_id"] == "test-req-001"

    @pytest.mark.asyncio
    async def test_LLM逾時回傳結構化錯誤(self):
        """LLM 逾時應回傳包含 error_code=LLM_TIMEOUT 的結構化錯誤（需求 1.3）"""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            side_effect=asyncio.TimeoutError("LLM 回應逾時")
        )

        result = await generate_scam_samples(
            scenario="假冒客服",
            target_audience="中老年族群",
            llm_client=mock_llm,
        )

        assert "error_code" in result
        assert result["error_code"] == LLMErrorCode.TIMEOUT
        assert "description" in result
        assert "timestamp" in result
        assert "request_id" in result

    @pytest.mark.asyncio
    async def test_LLM_API錯誤回傳結構化錯誤(self):
        """LLM API 錯誤應回傳包含 error_code=LLM_API_ERROR 的結構化錯誤（需求 1.3）"""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            side_effect=Exception("API 服務不可用")
        )

        result = await generate_scam_samples(
            scenario="假冒客服",
            target_audience="中老年族群",
            llm_client=mock_llm,
        )

        assert "error_code" in result
        assert result["error_code"] == LLMErrorCode.API_ERROR
        assert "description" in result
        assert "timestamp" in result
        assert "request_id" in result

    @pytest.mark.asyncio
    async def test_LLM回應格式錯誤回傳結構化錯誤(self):
        """LLM 回應無法解析時應回傳 error_code=LLM_PARSE_ERROR（需求 1.3）"""
        mock_llm = _make_mock_llm("這不是 JSON 格式")

        result = await generate_scam_samples(
            scenario="假冒客服",
            target_audience="中老年族群",
            llm_client=mock_llm,
        )

        assert "error_code" in result
        assert result["error_code"] == LLMErrorCode.PARSE_ERROR

    @pytest.mark.asyncio
    async def test_錯誤回應包含四個必要欄位(self):
        """任何錯誤情境的回應都應包含 error_code、description、timestamp、request_id（需求 1.3）"""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("任意錯誤"))

        result = await generate_scam_samples(
            scenario="假冒客服",
            target_audience="中老年族群",
            llm_client=mock_llm,
        )

        # 驗證四個必要欄位均存在且非空（需求 1.3）
        assert result.get("error_code")
        assert result.get("description")
        assert result.get("timestamp")
        assert result.get("request_id")


# ── _call_llm_with_retry 測試 ─────────────────────────────────────────────────

class TestCallLLMWithRetry:
    """測試指數退避重試邏輯"""

    @pytest.mark.asyncio
    async def test_第一次成功不重試(self):
        """第一次呼叫成功時不應重試"""
        mock_llm = _make_mock_llm("成功回應")

        result = await _call_llm_with_retry(
            llm=mock_llm,
            messages=[],
            request_id="test-001",
        )

        assert result == "成功回應"
        assert mock_llm.ainvoke.call_count == 1

    @pytest.mark.asyncio
    async def test_失敗後重試(self):
        """第一次失敗後應重試"""
        mock_llm = MagicMock()
        # 第一次失敗，第二次成功
        mock_llm.ainvoke = AsyncMock(
            side_effect=[
                Exception("第一次失敗"),
                MagicMock(content="第二次成功"),
            ]
        )

        result = await _call_llm_with_retry(
            llm=mock_llm,
            messages=[],
            request_id="test-002",
            initial_delay=0.01,  # 縮短測試等待時間
        )

        assert result == "第二次成功"
        assert mock_llm.ainvoke.call_count == 2

    @pytest.mark.asyncio
    async def test_達到最大重試次數後拋出例外(self):
        """達到最大重試次數後應拋出最後一次例外"""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("持續失敗"))

        with pytest.raises(Exception, match="持續失敗"):
            await _call_llm_with_retry(
                llm=mock_llm,
                messages=[],
                request_id="test-003",
                max_attempts=3,
                initial_delay=0.01,
            )

        assert mock_llm.ainvoke.call_count == 3

    @pytest.mark.asyncio
    async def test_逾時不重試直接拋出(self):
        """逾時錯誤應直接拋出，不重試"""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            side_effect=asyncio.TimeoutError("逾時")
        )

        with pytest.raises(asyncio.TimeoutError):
            await _call_llm_with_retry(
                llm=mock_llm,
                messages=[],
                request_id="test-004",
                max_attempts=3,
                initial_delay=0.01,
            )

        # 逾時不重試，只呼叫一次
        assert mock_llm.ainvoke.call_count == 1


# ── POST /v1/scam/generate 端點測試 ──────────────────────────────────────────

class TestScamGenerateEndpoint:
    """測試 POST /v1/scam/generate 端點"""

    @pytest.fixture(autouse=True)
    def clear_store(self):
        """每個測試前清空 in-memory 儲存"""
        _scam_scripts_store.clear()
        yield
        _scam_scripts_store.clear()

    VALID_API_KEY = "test-key-001"

    @pytest.fixture
    def client(self):
        """建立測試用 FastAPI 客戶端（帶有效 API 金鑰）"""
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    def _headers(self):
        return {"X-API-Key": self.VALID_API_KEY}

    def test_未授權角色回傳403(self, client):
        """一般操作員角色應被拒絕，回傳 HTTP 403（需求 1.4）"""
        with patch("app.api_gateway.routers.scam.generate_scam_samples"):
            response = client.post(
                "/v1/scam/generate",
                headers=self._headers(),
                json={
                    "scenario": "假冒銀行客服",
                    "target_audience": "中老年族群",
                    "operator_id": "op-001",
                    "operator_role": "一般操作員",
                },
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_不合法角色回傳403(self, client):
        """不合法角色字串應被拒絕，回傳 HTTP 403（需求 1.4）"""
        response = client.post(
            "/v1/scam/generate",
            headers=self._headers(),
            json={
                "scenario": "假冒銀行客服",
                "target_audience": "中老年族群",
                "operator_id": "op-001",
                "operator_role": "不存在的角色",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_授權成功回傳202(self, client):
        """詐騙分析師角色應授權成功，回傳 HTTP 202（需求 1.4）"""
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

        with patch("app.api_gateway.routers.scam.generate_scam_samples",
                   new=AsyncMock(return_value=mock_result)):
            response = client.post(
                "/v1/scam/generate",
                headers=self._headers(),
                json={
                    "scenario": "假冒銀行客服",
                    "target_audience": "中老年族群",
                    "operator_id": "analyst-001",
                    "operator_role": "詐騙分析師",
                },
            )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "accepted"

    def test_生成後Scam_Script儲存且is_regulated為True(self, client):
        """生成完成後 Scam_Script 應儲存至 in-memory，is_regulated 恆為 True（需求 1.5）"""
        mock_result = {
            "samples": [
                {
                    "content": f"詐騙話術樣本 {i}，您的帳戶發現異常，請立即驗證身份。",
                    "psychological_tags": ["緊迫感製造", "權威偽裝"],
                    "target_audience": "中老年族群",
                }
                for i in range(10)
            ],
            "count": 10,
            "request_id": "test-task-id",
        }

        with patch("app.api_gateway.routers.scam.generate_scam_samples",
                   new=AsyncMock(return_value=mock_result)):
            response = client.post(
                "/v1/scam/generate",
                headers=self._headers(),
                json={
                    "scenario": "假冒銀行客服",
                    "target_audience": "中老年族群",
                    "operator_id": "analyst-001",
                    "operator_role": "詐騙分析師",
                },
            )

        assert response.status_code == status.HTTP_202_ACCEPTED

        # 驗證所有儲存的 Scam_Script is_regulated 恆為 True（需求 1.5）
        assert len(_scam_scripts_store) == 10
        for script in _scam_scripts_store:
            assert script.is_regulated is True

    def test_LLM錯誤回傳503(self, client):
        """LLM 發生錯誤時應回傳 HTTP 503（需求 1.3）"""
        mock_error = {
            "error_code": LLMErrorCode.TIMEOUT,
            "description": "LLM 服務逾時",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": "test-req-001",
        }

        with patch("app.api_gateway.routers.scam.generate_scam_samples",
                   new=AsyncMock(return_value=mock_error)):
            response = client.post(
                "/v1/scam/generate",
                headers=self._headers(),
                json={
                    "scenario": "假冒銀行客服",
                    "target_audience": "中老年族群",
                    "operator_id": "analyst-001",
                    "operator_role": "詐騙分析師",
                },
            )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_系統管理員角色授權成功(self, client):
        """系統管理員角色應授權成功（需求 1.4）"""
        mock_result = {
            "samples": [
                {
                    "content": f"詐騙話術 {i}",
                    "psychological_tags": ["信任建立"],
                    "target_audience": "一般民眾",
                }
                for i in range(10)
            ],
            "count": 10,
            "request_id": "test-task-id",
        }

        with patch("app.api_gateway.routers.scam.generate_scam_samples",
                   new=AsyncMock(return_value=mock_result)):
            response = client.post(
                "/v1/scam/generate",
                headers=self._headers(),
                json={
                    "scenario": "假冒政府機關",
                    "target_audience": "一般民眾",
                    "operator_id": "admin-001",
                    "operator_role": "系統管理員",
                },
            )

        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_External_Client角色被拒絕(self, client):
        """External_Client 角色應被拒絕（需求 1.4）"""
        response = client.post(
            "/v1/scam/generate",
            headers=self._headers(),
            json={
                "scenario": "假冒銀行客服",
                "target_audience": "中老年族群",
                "operator_id": "ext-client-001",
                "operator_role": "External_Client",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ── ScamScript is_regulated 不變量測試 ───────────────────────────────────────

class TestScamScriptRegulatedInvariant:
    """測試 Scam_Script.is_regulated 恆為 True 的不變量（需求 1.5）"""

    def test_is_regulated_恆為True(self):
        """直接建立 ScamScript 時 is_regulated 應為 True"""
        from app.models.scam_script import ScamScript

        script = ScamScript(
            id=str(uuid.uuid4()),
            task_id=str(uuid.uuid4()),
            content="測試詐騙話術",
            scenario="假冒客服",
            target_audience="中老年族群",
            psychological_tags=["緊迫感製造"],
            language="zh-TW",
            is_regulated=True,
            created_at=datetime.now(timezone.utc),
            created_by="analyst-001",
        )
        assert script.is_regulated is True

    def test_設為False時拋出ValueError(self):
        """嘗試將 is_regulated 設為 False 時應拋出 ValueError（需求 1.5）"""
        from app.models.scam_script import ScamScript

        with pytest.raises(ValueError, match="is_regulated"):
            ScamScript(
                id=str(uuid.uuid4()),
                task_id=str(uuid.uuid4()),
                content="測試詐騙話術",
                scenario="假冒客服",
                target_audience="中老年族群",
                psychological_tags=["緊迫感製造"],
                language="zh-TW",
                is_regulated=False,  # 應拋出 ValueError
                created_at=datetime.now(timezone.utc),
                created_by="analyst-001",
            )
