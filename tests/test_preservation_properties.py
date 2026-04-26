"""
Preservation 保留性測試

驗證現有正確行為在修復前後不變。
這些測試在未修復程式碼上應全部 PASS，修復後也應全部 PASS。

**Validates: Requirements 3.1, 3.2, 3.3, 3.5, 3.8, 3.10**
"""

import pytest
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st
from fastapi.testclient import TestClient

from app.pattern_analyzer.xai_highlighter import XAIHighlighter
from app.dashboard.page_modules.risk_map import compute_risk_index
from app.api_gateway.main import app
from app.data_import.pii_remover import PiiRemover
from app.dashboard.page_modules.hotwords import compute_hotword_ranking
from data.taiwan_scam_data import SCAM_TYPE_STATS, REAL_HOTWORDS


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def highlighter() -> XAIHighlighter:
    return XAIHighlighter()


@pytest.fixture
def pii_remover() -> PiiRemover:
    return PiiRemover()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ── Property 1: XAIHighlighter.highlight() spans 與 coverage_ratio 合法性 ────


class TestXAIHighlighterPreservation:
    """
    Property: 對任意字串輸入，XAIHighlighter.highlight() 回傳的 spans
    位置在文字範圍內，coverage_ratio 在 [0.0, 1.0] 之間。

    **Validates: Requirements 3.2**
    """

    @h_settings(max_examples=50)
    @given(text=st.text(min_size=0, max_size=500))
    def test_highlight_spans_within_bounds(self, text: str) -> None:
        """spans 的 start/end 必須在 [0, len(text)] 範圍內"""
        highlighter = XAIHighlighter()
        result = highlighter.highlight(text)

        assert result.text == text
        for span in result.spans:
            assert 0 <= span.start < span.end <= len(text), (
                f"Span ({span.start}, {span.end}) out of bounds for text length {len(text)}"
            )

    @h_settings(max_examples=50)
    @given(text=st.text(min_size=0, max_size=500))
    def test_highlight_coverage_ratio_in_range(self, text: str) -> None:
        """coverage_ratio 必須在 [0.0, 1.0] 之間"""
        highlighter = XAIHighlighter()
        result = highlighter.highlight(text)

        assert 0.0 <= result.coverage_ratio <= 1.0, (
            f"coverage_ratio {result.coverage_ratio} out of [0.0, 1.0]"
        )

    @h_settings(max_examples=50)
    @given(text=st.text(min_size=0, max_size=500))
    def test_highlight_span_scores_in_range(self, text: str) -> None:
        """每個 span 的 score 必須在 [0.0, 1.0] 之間"""
        highlighter = XAIHighlighter()
        result = highlighter.highlight(text)

        for span in result.spans:
            assert 0.0 <= span.score <= 1.0, (
                f"Span score {span.score} out of [0.0, 1.0]"
            )

    @h_settings(max_examples=50)
    @given(text=st.text(min_size=0, max_size=500))
    def test_highlight_triggered_tags_subset_of_spans(self, text: str) -> None:
        """triggered_tags 必須是 spans 中出現的 tag 的子集"""
        highlighter = XAIHighlighter()
        result = highlighter.highlight(text)

        span_tags = {s.tag for s in result.spans}
        for tag in result.triggered_tags:
            assert tag in span_tags or len(result.spans) == 0


# ── Property 2: compute_risk_index() 回傳值在 [0.0, 1.0] ────────────────────

class TestComputeRiskIndexPreservation:
    """
    Property: 對任意風險向量資料，compute_risk_index() 回傳值在 [0.0, 1.0] 之間。

    **Validates: Requirements 3.1**
    """

    @h_settings(max_examples=50)
    @given(
        risk_vectors=st.lists(
            st.fixed_dictionaries({
                "target_audience": st.text(min_size=0, max_size=20),
                "region": st.text(min_size=0, max_size=10),
                "risk_score": st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
            }),
            min_size=0,
            max_size=10,
        ),
        age_group=st.sampled_from(["18歲以下", "18-29歲", "30-44歲", "45-59歲", "60歲以上"]),
        region=st.sampled_from(["台北市", "新北市", "桃園市", "台中市", "高雄市"]),
    )
    def test_risk_index_in_unit_range(
        self, risk_vectors: list, age_group: str, region: str
    ) -> None:
        """compute_risk_index() 回傳值必須在 [0.0, 1.0]"""
        result = compute_risk_index(risk_vectors, age_group, region)
        assert 0.0 <= result <= 1.0, (
            f"risk_index {result} out of [0.0, 1.0]"
        )

    def test_risk_index_empty_vectors_returns_zero(self) -> None:
        """空的風險向量列表應回傳 0.0"""
        result = compute_risk_index([], "18-29歲", "台北市")
        assert result == 0.0


# ── Property 3: 缺少 X-API-Key 的請求回傳 HTTP 401 ──────────────────────────

class TestAPIKeyRequiredPreservation:
    """
    Property: 對任意缺少 X-API-Key 標頭的 API 請求，回傳 HTTP 401。

    **Validates: Requirements 3.10**
    """

    @h_settings(max_examples=30)
    @given(
        endpoint=st.sampled_from([
            "/v1/risk-vectors",
            "/v1/predictions/alerts",
        ])
    )
    def test_missing_api_key_returns_401(self, endpoint: str) -> None:
        """缺少 X-API-Key 標頭的請求必須回傳 HTTP 401"""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(endpoint)
        assert response.status_code == 401, (
            f"Expected 401 for {endpoint} without API key, got {response.status_code}"
        )

    @h_settings(max_examples=30)
    @given(
        endpoint=st.sampled_from([
            "/v1/risk-vectors",
            "/v1/predictions/alerts",
        ])
    )
    def test_empty_api_key_returns_401(self, endpoint: str) -> None:
        """空字串 X-API-Key 標頭的請求必須回傳 HTTP 401"""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(endpoint, headers={"X-API-Key": ""})
        assert response.status_code == 401

    @h_settings(max_examples=30)
    @given(
        endpoint=st.sampled_from([
            "/v1/risk-vectors",
            "/v1/predictions/alerts",
        ])
    )
    def test_401_response_has_error_fields(self, endpoint: str) -> None:
        """HTTP 401 回應必須包含 error_code 與 description"""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(endpoint)
        assert response.status_code == 401
        data = response.json()
        assert "error_code" in data
        assert "description" in data


# ── Property 4: PiiRemover 去識別化行為一致性 ────────────────────────────────

class TestPiiRemoverPreservation:
    """
    Property: 對任意 PII 資料，PiiRemover 去識別化行為一致（相同輸入 → 相同輸出）。

    **Validates: Requirements 3.8**
    """

    @h_settings(max_examples=50)
    @given(text=st.text(min_size=0, max_size=300))
    def test_pii_removal_is_deterministic(self, text: str) -> None:
        """相同輸入呼叫兩次 remove_from_text 應產生相同結果"""
        remover = PiiRemover()
        result1, detected1 = remover.remove_from_text(text)
        result2, detected2 = remover.remove_from_text(text)
        assert result1 == result2
        assert detected1 == detected2

    @h_settings(max_examples=30)
    @given(
        records=st.lists(
            st.fixed_dictionaries({
                "description": st.text(min_size=0, max_size=100),
                "source": st.text(min_size=0, max_size=50),
                "scam_type": st.text(min_size=0, max_size=30),
                "import_batch_id": st.text(min_size=1, max_size=10),
            }),
            min_size=0,
            max_size=5,
        )
    )
    def test_batch_removal_is_deterministic(self, records: list) -> None:
        """相同批次資料呼叫兩次 remove_from_batch 應產生相同結果"""
        remover = PiiRemover()
        result1 = remover.remove_from_batch(records)
        result2 = remover.remove_from_batch(records)
        assert result1 == result2

    @h_settings(max_examples=30)
    @given(
        records=st.lists(
            st.fixed_dictionaries({
                "description": st.text(min_size=0, max_size=100),
                "source": st.text(min_size=0, max_size=50),
                "scam_type": st.text(min_size=0, max_size=30),
                "import_batch_id": st.text(min_size=1, max_size=10),
            }),
            min_size=0,
            max_size=5,
        )
    )
    def test_batch_removal_sets_pii_removed_flag(self, records: list) -> None:
        """remove_from_batch 後每筆記錄的 pii_removed 必須為 True"""
        remover = PiiRemover()
        result = remover.remove_from_batch(records)
        for r in result:
            assert r["pii_removed"] is True


# ── Property 5: SCAM_TYPE_STATS 資料結構正確性 ──────────────────────────────

class TestScamTypeStatsPreservation:
    """
    Property: SCAM_TYPE_STATS 包含 7 種詐騙類型，每種都有 cases/avg_loss_ntd/trend。

    **Validates: Requirements 3.1**
    """

    def test_scam_type_stats_has_7_types(self) -> None:
        """SCAM_TYPE_STATS 必須包含至少 7 種詐騙類型"""
        assert len(SCAM_TYPE_STATS) >= 7

    def test_scam_type_stats_required_keys(self) -> None:
        """每種詐騙類型必須包含 cases、avg_loss_ntd、trend 欄位"""
        required_keys = {"cases", "avg_loss_ntd", "trend"}
        for scam_type, stats in SCAM_TYPE_STATS.items():
            assert required_keys.issubset(stats.keys()), (
                f"{scam_type} missing keys: {required_keys - stats.keys()}"
            )

    def test_scam_type_stats_expected_types(self) -> None:
        """SCAM_TYPE_STATS 必須包含所有預期的 7 種基本詐騙類型"""
        expected_types = {
            "假冒銀行客服", "投資詐騙", "假冒政府機關",
            "愛情詐騙", "購物詐騙", "中獎詐騙", "工作詐騙",
        }
        assert expected_types.issubset(set(SCAM_TYPE_STATS.keys())), (
            f"缺少基本詐騙類型: {expected_types - set(SCAM_TYPE_STATS.keys())}"
        )

    def test_scam_type_stats_values_positive(self) -> None:
        """cases 和 avg_loss_ntd 必須為正數"""
        for scam_type, stats in SCAM_TYPE_STATS.items():
            assert stats["cases"] > 0, f"{scam_type} cases should be positive"
            assert stats["avg_loss_ntd"] > 0, f"{scam_type} avg_loss_ntd should be positive"

    def test_scam_type_stats_trend_valid(self) -> None:
        """trend 必須是 上升/下降/穩定 之一"""
        valid_trends = {"上升", "下降", "穩定"}
        for scam_type, stats in SCAM_TYPE_STATS.items():
            assert stats["trend"] in valid_trends, (
                f"{scam_type} trend '{stats['trend']}' not in {valid_trends}"
            )


# ── Property 6: REAL_HOTWORDS 排行正確性 ────────────────────────────────────

class TestHotwordRankingPreservation:
    """
    Property: REAL_HOTWORDS 資料經 compute_hotword_ranking() 排行後正確排序。

    **Validates: Requirements 3.3**
    """

    def test_hotword_ranking_returns_top_20(self) -> None:
        """compute_hotword_ranking(REAL_HOTWORDS) 應回傳最多 20 個熱詞"""
        ranking = compute_hotword_ranking(REAL_HOTWORDS)
        assert len(ranking) <= 20
        assert len(ranking) > 0

    def test_hotword_ranking_is_sorted_by_frequency(self) -> None:
        """排行結果應按頻率降序排列"""
        ranking = compute_hotword_ranking(REAL_HOTWORDS)
        for i in range(len(ranking) - 1):
            freq_current = REAL_HOTWORDS[ranking[i]]
            freq_next = REAL_HOTWORDS[ranking[i + 1]]
            assert freq_current >= freq_next, (
                f"'{ranking[i]}' ({freq_current}) should >= '{ranking[i+1]}' ({freq_next})"
            )

    def test_hotword_ranking_all_from_real_data(self) -> None:
        """排行中的每個熱詞都必須來自 REAL_HOTWORDS"""
        ranking = compute_hotword_ranking(REAL_HOTWORDS)
        for word in ranking:
            assert word in REAL_HOTWORDS

    @h_settings(max_examples=30)
    @given(
        freq=st.dictionaries(
            keys=st.text(min_size=1, max_size=10).filter(lambda s: s.strip()),
            values=st.integers(min_value=1, max_value=100000),
            min_size=0,
            max_size=30,
        )
    )
    def test_hotword_ranking_max_20(self, freq: dict) -> None:
        """對任意頻率字典，排行結果長度不超過 20"""
        ranking = compute_hotword_ranking(freq)
        assert len(ranking) <= 20


# ── Property 7: GET /v1/health 回傳正確格式且不需 API 金鑰 ──────────────────

class TestHealthEndpointPreservation:
    """
    Property: GET /v1/health 回傳正確格式且不需要 API 金鑰。

    **Validates: Requirements 3.5**
    """

    def test_health_returns_200_without_api_key(self) -> None:
        """GET /v1/health 不帶 API 金鑰應回傳 200"""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/v1/health")
        assert response.status_code == 200

    def test_health_response_has_required_fields(self) -> None:
        """健康檢查回應必須包含 status、service、timestamp、version"""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/v1/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "timestamp" in data
        assert "version" in data

    def test_health_response_version_format(self) -> None:
        """version 欄位應為非空字串"""
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/v1/health")
        data = response.json()
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0
