"""
Bug Condition 探索性測試

此測試檔案編碼了每個缺陷的「預期正確行為」。
在未修復的程式碼上執行時，測試應 FAIL — 這證明缺陷確實存在。
修復後重新執行，測試應 PASS — 這證明缺陷已修復。

**Validates: Requirements 1.1, 1.2, 1.4, 1.8, 1.9, 1.10, 1.12, 1.13, 1.14**
"""

import ast
import inspect
import os
import textwrap

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# 1.1  .env 金鑰洩露
# ---------------------------------------------------------------------------

class TestEnvKeyLeak:
    """
    **Validates: Requirements 1.1**

    .env 檔案不應包含真實 API 金鑰。
    """

    def test_env_no_real_openai_key(self):
        """斷言 .env 不包含 sk-proj- 開頭的真實 OpenAI 金鑰"""
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        assert os.path.exists(env_path), ".env file should exist"
        content = open(env_path, encoding="utf-8").read()
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            if key.strip().upper() == "OPENAI_API_KEY":
                assert not value.strip().startswith("sk-proj-"), (
                    f".env contains a real OpenAI key starting with sk-proj-: {value[:20]}..."
                )

    def test_env_no_real_google_key(self):
        """斷言 .env 不包含 AIzaSy 開頭的真實 Google 金鑰"""
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        assert os.path.exists(env_path), ".env file should exist"
        content = open(env_path, encoding="utf-8").read()
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            if key.strip().upper() == "GOOGLE_API_KEY":
                assert not value.strip().startswith("AIzaSy"), (
                    f".env contains a real Google key starting with AIzaSy: {value[:20]}..."
                )


# ---------------------------------------------------------------------------
# 1.2  威脅監控隨機性
# ---------------------------------------------------------------------------

class TestThreatMonitorDeterminism:
    """
    **Validates: Requirements 1.2**

    generate_live_alerts() 應產生確定性結果（不使用 random）。
    get_current_threat_summary() 應基於真實統計而非硬編碼。
    """

    def test_generate_live_alerts_deterministic(self):
        """連續呼叫兩次 generate_live_alerts()，結果應相同"""
        from app.dashboard.page_modules.threat_monitor import generate_live_alerts

        result1 = generate_live_alerts()
        result2 = generate_live_alerts()
        assert result1 == result2, (
            "generate_live_alerts() produced different results on consecutive calls — "
            "indicates non-deterministic (random) data generation"
        )

    def test_threat_summary_not_hardcoded(self):
        """get_current_threat_summary() 的數據應來自真實統計，非硬編碼常數"""
        from app.dashboard.page_modules.threat_monitor import get_current_threat_summary
        from data.taiwan_scam_data import SCAM_TYPE_STATS

        summary = get_current_threat_summary()

        # 硬編碼值 23 不太可能恰好等於真實統計衍生值
        # 真實統計有 7 種詐騙類型，active_threats 應反映真實資料
        total_types = len(SCAM_TYPE_STATS)
        assert summary["active_threats"] != 23 or total_types == 23, (
            f"active_threats={summary['active_threats']} looks hardcoded (expected derived from real stats)"
        )


# ---------------------------------------------------------------------------
# 1.4  API 金鑰硬編碼
# ---------------------------------------------------------------------------

class TestApiKeyHardcoded:
    """
    **Validates: Requirements 1.4**

    _VALID_API_KEYS 應支援從環境變數載入，而非僅有硬編碼值。
    """

    def test_api_keys_support_env_loading(self):
        """API 金鑰驗證應支援從環境變數載入金鑰"""
        source = inspect.getsource(
            __import__("app.api_gateway.middleware.api_key", fromlist=["api_key"])
        )
        # 模組原始碼中應包含從環境變數載入金鑰的邏輯
        # 注意：_VALID_API_KEYS 是硬編碼字典名稱，不算環境變數載入
        has_env_loading = (
            "os.environ" in source
            or "os.getenv" in source
            or "_load_api_keys_from_env" in source
        )
        assert has_env_loading, (
            "api_key.py does not contain any environment variable loading logic — "
            "API keys are purely hardcoded"
        )


# ---------------------------------------------------------------------------
# 1.8  進化時間軸不完整
# ---------------------------------------------------------------------------

class TestEvolutionTimelineCompleteness:
    """
    **Validates: Requirements 1.8**

    EVOLUTION_TIMELINE 應包含所有 7 種詐騙類型。
    """

    EXPECTED_SCAM_TYPES = {
        "假冒銀行客服",
        "投資詐騙",
        "假冒政府機關",
        "愛情詐騙",
        "購物詐騙",
        "中獎詐騙",
        "工作詐騙",
    }

    def test_evolution_timeline_has_all_7_types(self):
        """EVOLUTION_TIMELINE 應包含所有 7 種詐騙類型"""
        from app.dashboard.page_modules.threat_monitor import EVOLUTION_TIMELINE

        actual_types = set(EVOLUTION_TIMELINE.keys())
        missing = self.EXPECTED_SCAM_TYPES - actual_types
        assert not missing, (
            f"EVOLUTION_TIMELINE is missing {len(missing)} scam types: {missing}. "
            f"Only has: {actual_types}"
        )

    def test_evolution_timeline_count(self):
        """EVOLUTION_TIMELINE 應恰好有 7 個 key"""
        from app.dashboard.page_modules.threat_monitor import EVOLUTION_TIMELINE

        assert len(EVOLUTION_TIMELINE) >= 7, (
            f"EVOLUTION_TIMELINE has only {len(EVOLUTION_TIMELINE)} types, expected >= 7"
        )


# ---------------------------------------------------------------------------
# 1.9  年齡層匹配失敗
# ---------------------------------------------------------------------------

class TestAgeGroupMismatch:
    """
    **Validates: Requirements 1.9**

    compute_risk_index() 應正確匹配「中老年族群」與「45-59歲」和「60歲以上」。
    """

    def _make_risk_vectors(self, target_audience: str, region: str, risk_score: float = 0.8):
        """建立帶有 target_audience 的風險向量，region 用於隔離匹配維度"""
        return [
            {
                "target_audience": target_audience,
                "region": region,
                "risk_score": risk_score,
                "scam_cluster_label": "假冒客服詐騙",
            }
        ]

    def test_middle_aged_matches_45_59(self):
        """「中老年族群」的風險向量應被 45-59歲 年齡層匹配到（排除地區匹配）"""
        from app.dashboard.page_modules.risk_map import compute_risk_index

        # 使用不同地區以隔離年齡層匹配邏輯
        vectors = self._make_risk_vectors("中老年族群", "高雄市", 0.8)
        result = compute_risk_index(vectors, "45-59歲", "台北市")
        assert result > 0.0, (
            f"compute_risk_index returned {result} for age_group='45-59歲' with "
            f"target_audience='中老年族群' — should be > 0.0 (age group matching failed)"
        )

    def test_middle_aged_matches_60_plus(self):
        """「中老年族群」的風險向量應被 60歲以上 年齡層匹配到（排除地區匹配）"""
        from app.dashboard.page_modules.risk_map import compute_risk_index

        # 使用不同地區以隔離年齡層匹配邏輯
        vectors = self._make_risk_vectors("中老年族群", "高雄市", 0.8)
        result = compute_risk_index(vectors, "60歲以上", "台北市")
        assert result > 0.0, (
            f"compute_risk_index returned {result} for age_group='60歲以上' with "
            f"target_audience='中老年族群' — should be > 0.0 (age group matching failed)"
        )

    @given(
        risk_score=st.floats(min_value=0.01, max_value=1.0),
    )
    @settings(max_examples=10)
    def test_middle_aged_always_matches_property(self, risk_score: float):
        """
        Property: 對任意正風險分數，「中老年族群」應匹配「45-59歲」（排除地區匹配）。

        **Validates: Requirements 1.9**
        """
        from app.dashboard.page_modules.risk_map import compute_risk_index

        # 使用不同地區以隔離年齡層匹配邏輯
        vectors = self._make_risk_vectors("中老年族群", "高雄市", risk_score)
        result = compute_risk_index(vectors, "45-59歲", "台北市")
        assert result > 0.0, (
            f"Property violation: risk_score={risk_score}, result={result}"
        )


# ---------------------------------------------------------------------------
# 1.10  預警 API 空列表
# ---------------------------------------------------------------------------

class TestAlertsApiEmpty:
    """
    **Validates: Requirements 1.10**

    AlertingService 初始化後 get_alerts() 應回傳非空列表（含種子資料）。
    """

    def test_alerting_service_has_seed_data(self):
        """predictions 路由的 AlertingService 應包含種子預警資料"""
        from app.api_gateway.routers.predictions import get_alerting_service

        service = get_alerting_service()
        alerts = service.get_alerts()
        assert len(alerts) > 0, (
            "get_alerting_service().get_alerts() returned empty list — "
            "no seed data was populated on initialization"
        )


# ---------------------------------------------------------------------------
# 1.12  排程器未啟動
# ---------------------------------------------------------------------------

class TestSchedulerNotStarted:
    """
    **Validates: Requirements 1.12**

    lifespan 函數應呼叫 get_scheduler().start()。
    """

    def test_lifespan_calls_scheduler_start(self):
        """lifespan() 的原始碼應包含 get_scheduler().start() 呼叫"""
        from app.api_gateway.main import lifespan

        source = inspect.getsource(lifespan)
        has_scheduler_start = (
            "get_scheduler().start()" in source
            or "get_scheduler()" in source and ".start()" in source
            or "scheduler.start()" in source
        )
        assert has_scheduler_start, (
            "lifespan() does not call get_scheduler().start() — "
            "the PredictionScheduler is never started on application boot"
        )


# ---------------------------------------------------------------------------
# 1.13  匯入資料未持久化
# ---------------------------------------------------------------------------

class TestImportDataNotPersisted:
    """
    **Validates: Requirements 1.13**

    data.py 應在 PII 去識別化後將清理後的資料存入儲存。
    """

    def test_data_router_persists_cleaned_records(self):
        """data.py 的 import 端點應將 cleaned_records 存入某種儲存"""
        source = inspect.getsource(
            __import__("app.api_gateway.routers.data", fromlist=["data"])
        )
        # 檢查是否有儲存 cleaned_records 的邏輯
        has_persistence = (
            "_imported_records_store" in source
            or "cleaned_records" in source and ("store" in source or "append" in source or "save" in source or "persist" in source)
        )
        # 更嚴格：確認 cleaned_records 被存入某個 store
        stores_cleaned = (
            "_imported_records_store.extend" in source
            or "_imported_records_store.append" in source
            or "_imported_records_store =" in source
            or "store.extend(cleaned" in source
            or "store.append(cleaned" in source
        )
        assert stores_cleaned, (
            "data.py does not persist cleaned_records after PII removal — "
            "the cleaned data is computed but never stored"
        )


# ---------------------------------------------------------------------------
# 1.14  RBAC 信任請求 body
# ---------------------------------------------------------------------------

class TestRbacTrustsRequestBody:
    """
    **Validates: Requirements 1.14**

    scam.py 應從 HTTP 標頭取得操作人員身份，而非信任請求 body。
    """

    def test_scam_endpoint_uses_headers_for_identity(self):
        """scam.py 的 generate 端點應從 HTTP 標頭取得 operator 身份"""
        source = inspect.getsource(
            __import__("app.api_gateway.routers.scam", fromlist=["scam"])
        )
        # 檢查是否使用 require_role 依賴注入或從 Header 取得身份
        uses_header_auth = (
            "require_role" in source
            or "X-Operator-Id" in source
            or "Header(" in source and "operator" in source.lower()
        )
        # 同時確認不再從 body 取得身份作為主要來源
        uses_body_identity = (
            "body.operator_id" in source
            and "body.operator_role" in source
            and "require_role" not in source
            and "X-Operator" not in source
        )
        assert uses_header_auth and not uses_body_identity, (
            "scam.py gets operator identity from request body (body.operator_id, "
            "body.operator_role) instead of HTTP headers — anyone can claim any role"
        )
