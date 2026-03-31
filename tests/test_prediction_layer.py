"""
Prediction_Layer 測試模組

包含單元測試與屬性測試（hypothesis），驗證：
- 屬性 10：預警事件結構完整性
- 屬性 11：準確率計算範圍不變量
- 屬性 12：格式不符資料拒絕
- 屬性 13：Risk_Vector 結構不變量
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st

from app.models.alert_event import AlertEvent, VALID_RISK_LEVELS
from app.models.risk_vector import RiskVector
from app.prediction_layer.alerting import AlertingService, determine_risk_level, build_trigger_features
from app.prediction_layer.analyzer import AnomalyDetector, PredictionAnalyzer, TrendAnalyzer
from app.prediction_layer.risk_vector import (
    RiskVectorGenerator,
    RiskVectorRepository,
    MockRedisCache,
    calculate_risk_score,
    score_to_risk_level,
)
from app.prediction_layer.scheduler import PredictionScheduler
from app.prediction_layer.validator import validate_case_report_batch


# ── 輔助工廠函數 ───────────────────────────────────────────────────────────────

def make_risk_vector_id() -> str:
    return str(uuid.uuid4())


def make_datetime() -> datetime:
    return datetime.now(timezone.utc)


# ══════════════════════════════════════════════════════════════════════════════
# 屬性測試
# ══════════════════════════════════════════════════════════════════════════════

# ── 屬性 10：預警事件結構完整性 ────────────────────────────────────────────────

@settings(max_examples=100)
@given(
    risk_level=st.sampled_from(["高", "中", "低"]),
    trigger_features=st.lists(
        st.text(min_size=1, max_size=50).filter(lambda s: s.strip()),
        min_size=1,
        max_size=5,
    ),
)
def test_alert_event_structure(risk_level: str, trigger_features: list[str]) -> None:
    """
    **Validates: Requirements 3.2**

    # Feature: ai-scam-evolution-prediction, Property 10: 預警事件結構完整性
    對於任意由異常偵測觸發的預警事件，AlertEvent 應包含合法的風險等級（高/中/低）
    與至少一個非空的觸發特徵描述，不得出現此三個等級以外的值。
    """
    service = AlertingService()
    rv_id = make_risk_vector_id()

    alert = service.create_alert_from_params(
        risk_level=risk_level,
        trigger_features=trigger_features,
        risk_vector_id=rv_id,
    )

    # 風險等級必須合法
    assert alert.risk_level in VALID_RISK_LEVELS, (
        f"risk_level 必須為 高/中/低 之一，實際值：{alert.risk_level}"
    )
    # 觸發特徵至少一個非空
    assert len(alert.trigger_features) >= 1
    assert all(f.strip() for f in alert.trigger_features), (
        "所有觸發特徵描述不可為空字串"
    )
    # 必要欄位存在且非空
    assert alert.id
    assert alert.risk_vector_id == rv_id
    assert isinstance(alert.created_at, datetime)
    assert isinstance(alert.notified_at, datetime)


@settings(max_examples=100)
@given(
    risk_level=st.text().filter(lambda s: s not in VALID_RISK_LEVELS and s.strip()),
)
def test_alert_event_rejects_invalid_risk_level(risk_level: str) -> None:
    """
    # Feature: ai-scam-evolution-prediction, Property 10: 預警事件結構完整性
    非法風險等級應被拒絕。
    """
    service = AlertingService()
    with pytest.raises(ValueError, match="risk_level"):
        service.create_alert_from_params(
            risk_level=risk_level,
            trigger_features=["測試特徵"],
            risk_vector_id=make_risk_vector_id(),
        )


# ── 屬性 11：準確率計算範圍不變量 ──────────────────────────────────────────────

@settings(max_examples=100)
@given(
    predictions=st.lists(st.floats(min_value=0.0, max_value=1.0, allow_nan=False), min_size=1, max_size=50),
    actuals=st.lists(st.floats(min_value=0.0, max_value=1.0, allow_nan=False), min_size=1, max_size=50),
)
def test_accuracy_score_range(predictions: list[float], actuals: list[float]) -> None:
    """
    **Validates: Requirements 3.4**

    # Feature: ai-scam-evolution-prediction, Property 11: 準確率計算範圍不變量
    對於任意預測結果集合與真實報案資料集合，計算出的預測準確率應在 [0.0, 1.0] 閉區間內。
    """
    generator = RiskVectorGenerator()
    accuracy = generator.calculate_accuracy(predictions, actuals)

    assert 0.0 <= accuracy <= 1.0, (
        f"準確率必須在 [0.0, 1.0] 閉區間內，實際值：{accuracy}"
    )


@settings(max_examples=100)
@given(
    predictions=st.lists(st.floats(min_value=0.0, max_value=1.0, allow_nan=False), min_size=1, max_size=20),
    actuals=st.lists(st.floats(min_value=0.0, max_value=1.0, allow_nan=False), min_size=1, max_size=20),
)
def test_accuracy_score_manual_verification(predictions: list[float], actuals: list[float]) -> None:
    """
    **Validates: Requirements 3.4**

    # Feature: ai-scam-evolution-prediction, Property 11: 準確率計算範圍不變量
    計算結果應與手動計算（正確預測數 / 總預測數）結果一致。
    """
    generator = RiskVectorGenerator()
    accuracy = generator.calculate_accuracy(predictions, actuals)

    # 手動計算驗證
    n = min(len(predictions), len(actuals))
    threshold = 0.5
    correct = sum(
        1 for p, a in zip(predictions[:n], actuals[:n])
        if (p >= threshold) == (a >= threshold)
    )
    expected = correct / n if n > 0 else 0.0

    assert abs(accuracy - expected) < 1e-9, (
        f"準確率計算結果不一致：計算值={accuracy}，手動驗證={expected}"
    )


# ── 屬性 12：格式不符資料拒絕 ──────────────────────────────────────────────────

# 合法記錄策略
_valid_record_strategy = st.fixed_dictionaries({
    "source": st.text(min_size=1, max_size=20).filter(lambda s: s.strip()),
    "scam_type": st.text(min_size=1, max_size=20).filter(lambda s: s.strip()),
    "description": st.text(min_size=1, max_size=100).filter(lambda s: s.strip()),
    "reported_at": st.just("2024-01-01T00:00:00+00:00"),
    "import_batch_id": st.uuids().map(str),
    "pii_removed": st.booleans(),
})

# 缺少必要欄位的記錄策略
_missing_field_strategy = st.one_of(
    # 缺少 source
    st.fixed_dictionaries({
        "scam_type": st.just("投資詐騙"),
        "description": st.just("測試描述"),
        "reported_at": st.just("2024-01-01T00:00:00+00:00"),
        "import_batch_id": st.uuids().map(str),
        "pii_removed": st.just(True),
    }),
    # 缺少 scam_type
    st.fixed_dictionaries({
        "source": st.just("警政署"),
        "description": st.just("測試描述"),
        "reported_at": st.just("2024-01-01T00:00:00+00:00"),
        "import_batch_id": st.uuids().map(str),
        "pii_removed": st.just(True),
    }),
    # 缺少 description
    st.fixed_dictionaries({
        "source": st.just("警政署"),
        "scam_type": st.just("投資詐騙"),
        "reported_at": st.just("2024-01-01T00:00:00+00:00"),
        "import_batch_id": st.uuids().map(str),
        "pii_removed": st.just(True),
    }),
    # 缺少 pii_removed
    st.fixed_dictionaries({
        "source": st.just("警政署"),
        "scam_type": st.just("投資詐騙"),
        "description": st.just("測試描述"),
        "reported_at": st.just("2024-01-01T00:00:00+00:00"),
        "import_batch_id": st.uuids().map(str),
    }),
)


@settings(max_examples=100)
@given(
    invalid_records=st.lists(_missing_field_strategy, min_size=1, max_size=5),
)
def test_invalid_format_rejected(invalid_records: list[dict]) -> None:
    """
    **Validates: Requirements 3.5**

    # Feature: ai-scam-evolution-prediction, Property 12: 格式不符資料拒絕
    對於任意不符合系統規範格式的報案資料批次，Prediction_Layer 應拒絕整批資料
    並回傳包含具體格式錯誤說明的回應，不得部分匯入。
    """
    result = validate_case_report_batch(invalid_records)

    # 整批應被拒絕
    assert result["valid"] is False, "格式不符的批次應被拒絕"
    assert result["error_code"] is not None, "應回傳錯誤代碼"
    assert len(result["details"]) > 0, "應包含具體錯誤說明"
    assert result["accepted_count"] == 0, "不得部分匯入（接受數應為 0）"
    assert result["rejected_count"] == len(invalid_records), (
        f"拒絕數應等於批次大小 {len(invalid_records)}"
    )


@settings(max_examples=100)
@given(
    valid_records=st.lists(_valid_record_strategy, min_size=1, max_size=10),
)
def test_valid_format_accepted(valid_records: list[dict]) -> None:
    """
    # Feature: ai-scam-evolution-prediction, Property 12: 格式不符資料拒絕（反向驗證）
    符合規範的批次應通過驗證。
    """
    result = validate_case_report_batch(valid_records)

    assert result["valid"] is True, f"合法批次應通過驗證，錯誤：{result['details']}"
    assert result["error_code"] is None
    assert result["accepted_count"] == len(valid_records)
    assert result["rejected_count"] == 0


# ── 屬性 13：Risk_Vector 結構不變量 ────────────────────────────────────────────

@settings(max_examples=100)
@given(
    high_risk_features=st.lists(
        st.text(min_size=1, max_size=30).filter(lambda s: s.strip()),
        min_size=1,
        max_size=10,
    ),
    scam_cluster_label=st.text(min_size=1, max_size=30).filter(lambda s: s.strip()),
    risk_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_risk_vector_invariant(
    high_risk_features: list[str],
    scam_cluster_label: str,
    risk_score: float,
) -> None:
    """
    **Validates: Requirements 3.6**

    # Feature: ai-scam-evolution-prediction, Property 13: Risk_Vector 結構不變量
    對於任意由 Prediction_Layer 生成的 Risk_Vector，應包含至少一個高風險語意特徵、
    非空的詐騙類群標籤，且風險分數應在 [0.0, 1.0] 閉區間內。
    """
    generator = RiskVectorGenerator()
    now = make_datetime()

    rv = generator.generate_from_params(
        high_risk_features=high_risk_features,
        scam_cluster_label=scam_cluster_label,
        risk_score=risk_score,
        time_range_start=now,
        time_range_end=now,
    )

    # 至少一個高風險語意特徵
    assert len(rv.high_risk_features) >= 1, "應包含至少一個高風險語意特徵"
    assert all(f.strip() for f in rv.high_risk_features), "所有特徵不可為空字串"

    # 非空的詐騙類群標籤
    assert rv.scam_cluster_label and rv.scam_cluster_label.strip(), (
        "詐騙類群標籤不可為空字串"
    )

    # 風險分數在 [0.0, 1.0] 閉區間
    assert 0.0 <= rv.risk_score <= 1.0, (
        f"風險分數必須在 [0.0, 1.0] 範圍內，實際值：{rv.risk_score}"
    )

    # 風險等級合法
    assert rv.risk_level in VALID_RISK_LEVELS, (
        f"風險等級必須為 高/中/低 之一，實際值：{rv.risk_level}"
    )

    # 版本號非空
    assert rv.version and rv.version.strip(), "版本號不可為空字串"

    # 時間範圍欄位存在
    assert isinstance(rv.time_range_start, datetime)
    assert isinstance(rv.time_range_end, datetime)


# ══════════════════════════════════════════════════════════════════════════════
# 單元測試
# ══════════════════════════════════════════════════════════════════════════════

class TestAnomalyDetector:
    """異常偵測器單元測試"""

    def test_detect_anomalies_returns_result(self) -> None:
        """偵測異常應回傳包含必要欄位的結果"""
        detector = AnomalyDetector()
        vectors = [[float(i), float(i * 2)] for i in range(20)]
        result = detector.detect_anomalies(vectors)

        assert "anomaly_indices" in result
        assert "anomaly_ratio" in result
        assert "scores" in result
        assert 0.0 <= result["anomaly_ratio"] <= 1.0

    def test_detect_anomalies_empty_returns_empty(self) -> None:
        """空向量列表應回傳空結果"""
        detector = AnomalyDetector()
        result = detector.detect_anomalies([])

        assert result["anomaly_indices"] == []
        assert result["anomaly_ratio"] == 0.0

    def test_fit_predict_raises_on_empty(self) -> None:
        """空向量列表應拋出 ValueError"""
        detector = AnomalyDetector()
        with pytest.raises(ValueError, match="不可為空"):
            detector.fit_predict([])


class TestTrendAnalyzer:
    """趨勢分析器單元測試"""

    def test_insufficient_data(self) -> None:
        """資料不足時應回傳資料不足狀態"""
        analyzer = TrendAnalyzer()
        result = analyzer.analyze_trend([{"timestamp": "2024-01-01", "count": 10}])
        assert result["trend"] == "資料不足"

    def test_rising_trend(self) -> None:
        """上升趨勢應被正確識別"""
        analyzer = TrendAnalyzer()
        series = [
            {"timestamp": "2024-01-01T00:00:00", "count": 10},
            {"timestamp": "2024-01-01T01:00:00", "count": 15},
        ]
        result = analyzer.analyze_trend(series)
        assert result["trend"] == "上升"
        assert result["is_emerging"] is True

    def test_stable_trend(self) -> None:
        """穩定趨勢應被正確識別"""
        analyzer = TrendAnalyzer()
        series = [
            {"timestamp": "2024-01-01T00:00:00", "count": 10},
            {"timestamp": "2024-01-01T01:00:00", "count": 10},
        ]
        result = analyzer.analyze_trend(series)
        assert result["trend"] == "穩定"
        assert result["is_emerging"] is False


class TestPredictionAnalyzer:
    """預測分析主控器單元測試"""

    def test_run_analysis_empty_store(self) -> None:
        """無向量資料時應回傳空分析結果"""
        analyzer = PredictionAnalyzer()
        result = analyzer.run_analysis()

        assert result["vector_count"] == 0
        assert result["has_anomaly"] is False
        assert "analysis_id" in result

    def test_run_analysis_with_vectors(self) -> None:
        """有向量資料時應執行完整分析"""
        analyzer = PredictionAnalyzer()
        now = datetime.now(timezone.utc)

        vectors = [
            {
                "embedding": [float(i % 10), float((i * 3) % 10)],
                "cluster_label": "投資詐騙",
                "top_keywords": ["投資", "獲利"],
                "created_at": now,
            }
            for i in range(30)
        ]
        analyzer.add_vectors(vectors)
        result = analyzer.run_analysis()

        assert result["vector_count"] == 30
        assert "anomalies" in result
        assert "trend" in result


class TestAlertingService:
    """預警服務單元測試"""

    def test_create_alert_valid(self) -> None:
        """合法參數應成功建立預警事件"""
        service = AlertingService()
        alert = service.create_alert_from_params(
            risk_level="高",
            trigger_features=["新型詐騙手法頻率異常上升"],
            risk_vector_id=make_risk_vector_id(),
        )

        assert alert.risk_level == "高"
        assert len(alert.trigger_features) == 1
        assert alert.id

    def test_create_alert_invalid_risk_level(self) -> None:
        """非法風險等級應拋出 ValueError"""
        service = AlertingService()
        with pytest.raises(ValueError, match="risk_level"):
            service.create_alert_from_params(
                risk_level="極高",
                trigger_features=["測試"],
                risk_vector_id=make_risk_vector_id(),
            )

    def test_create_alert_empty_features(self) -> None:
        """空觸發特徵應拋出 ValueError"""
        service = AlertingService()
        with pytest.raises(ValueError, match="trigger_features"):
            service.create_alert_from_params(
                risk_level="中",
                trigger_features=[],
                risk_vector_id=make_risk_vector_id(),
            )

    def test_subscribe_and_notify(self) -> None:
        """訂閱操作人員後應出現在通知列表"""
        service = AlertingService()
        service.subscribe_operator("operator-001")
        service.subscribe_operator("operator-002")

        alert = service.create_alert_from_params(
            risk_level="低",
            trigger_features=["測試特徵"],
            risk_vector_id=make_risk_vector_id(),
        )

        assert "operator-001" in alert.notified_operators
        assert "operator-002" in alert.notified_operators

    def test_get_alerts_returns_list(self) -> None:
        """取得預警列表應回傳正確結果"""
        service = AlertingService()
        for _ in range(3):
            service.create_alert_from_params(
                risk_level="中",
                trigger_features=["特徵描述"],
                risk_vector_id=make_risk_vector_id(),
            )

        alerts = service.get_alerts()
        assert len(alerts) == 3

    def test_determine_risk_level_high(self) -> None:
        """高異常比例應判定為高風險"""
        level = determine_risk_level(anomaly_ratio=0.35, trend_is_emerging=False)
        assert level == "高"

    def test_determine_risk_level_low(self) -> None:
        """低異常比例且無新興趨勢應判定為低風險"""
        level = determine_risk_level(anomaly_ratio=0.05, trend_is_emerging=False)
        assert level == "低"


class TestRiskVectorGenerator:
    """Risk_Vector 生成器單元測試"""

    def test_generate_from_params_valid(self) -> None:
        """合法參數應成功生成 RiskVector"""
        generator = RiskVectorGenerator()
        now = make_datetime()

        rv = generator.generate_from_params(
            high_risk_features=["假冒客服", "緊迫感製造"],
            scam_cluster_label="假冒客服詐騙",
            risk_score=0.75,
            time_range_start=now,
            time_range_end=now,
        )

        assert rv.risk_score == 0.75
        assert rv.risk_level == "高"
        assert rv.scam_cluster_label == "假冒客服詐騙"
        assert len(rv.high_risk_features) == 2

    def test_generate_from_params_empty_features(self) -> None:
        """空特徵列表應拋出 ValueError"""
        generator = RiskVectorGenerator()
        now = make_datetime()
        with pytest.raises(ValueError, match="high_risk_features"):
            generator.generate_from_params(
                high_risk_features=[],
                scam_cluster_label="測試",
                risk_score=0.5,
                time_range_start=now,
                time_range_end=now,
            )

    def test_generate_from_params_empty_cluster(self) -> None:
        """空類群標籤應拋出 ValueError"""
        generator = RiskVectorGenerator()
        now = make_datetime()
        with pytest.raises(ValueError, match="scam_cluster_label"):
            generator.generate_from_params(
                high_risk_features=["特徵"],
                scam_cluster_label="",
                risk_score=0.5,
                time_range_start=now,
                time_range_end=now,
            )

    def test_generate_from_params_invalid_score(self) -> None:
        """超出範圍的風險分數應拋出 ValueError"""
        generator = RiskVectorGenerator()
        now = make_datetime()
        with pytest.raises(ValueError):
            generator.generate_from_params(
                high_risk_features=["特徵"],
                scam_cluster_label="測試",
                risk_score=1.5,
                time_range_start=now,
                time_range_end=now,
            )

    def test_calculate_accuracy_empty_raises(self) -> None:
        """空列表應拋出 ValueError"""
        generator = RiskVectorGenerator()
        with pytest.raises(ValueError):
            generator.calculate_accuracy([], [])

    def test_calculate_accuracy_all_correct(self) -> None:
        """全部正確預測應回傳 1.0"""
        generator = RiskVectorGenerator()
        predictions = [0.8, 0.9, 0.7]
        actuals = [0.9, 0.8, 0.6]
        accuracy = generator.calculate_accuracy(predictions, actuals)
        assert accuracy == 1.0

    def test_calculate_accuracy_all_wrong(self) -> None:
        """全部錯誤預測應回傳 0.0"""
        generator = RiskVectorGenerator()
        predictions = [0.8, 0.9, 0.7]  # 全部 >= 0.5（高風險）
        actuals = [0.1, 0.2, 0.3]      # 全部 < 0.5（低風險）
        accuracy = generator.calculate_accuracy(predictions, actuals)
        assert accuracy == 0.0

    def test_score_to_risk_level(self) -> None:
        """風險分數轉換應正確"""
        assert score_to_risk_level(0.8) == "高"
        assert score_to_risk_level(0.5) == "中"
        assert score_to_risk_level(0.2) == "低"


class TestRiskVectorRepository:
    """Risk_Vector 儲存庫單元測試"""

    def test_save_and_get_by_id(self) -> None:
        """儲存後應可依 ID 查詢"""
        cache = MockRedisCache()
        repo = RiskVectorRepository(redis_cache=cache)
        now = make_datetime()

        rv = RiskVector(
            id=str(uuid.uuid4()),
            high_risk_features=["特徵一"],
            scam_cluster_label="測試類群",
            risk_score=0.6,
            risk_level="中",
            time_range_start=now,
            time_range_end=now,
            version="1.0.0",
            created_at=now,
        )

        saved = repo.save(rv)
        retrieved = repo.get_by_id(rv.id)

        assert retrieved is not None
        assert retrieved.id == rv.id
        assert retrieved.risk_score == rv.risk_score

    def test_cache_is_updated_on_save(self) -> None:
        """儲存後 Redis 快取應被更新"""
        cache = MockRedisCache()
        repo = RiskVectorRepository(redis_cache=cache)
        now = make_datetime()

        rv = RiskVector(
            id=str(uuid.uuid4()),
            high_risk_features=["特徵"],
            scam_cluster_label="類群",
            risk_score=0.5,
            risk_level="中",
            time_range_start=now,
            time_range_end=now,
            version="1.0.0",
            created_at=now,
        )
        repo.save(rv)

        cache_key = f"risk_vector:{rv.id}"
        assert cache.get(cache_key) is not None


class TestValidateCaseReportBatch:
    """報案資料格式驗證單元測試"""

    def _valid_record(self) -> dict:
        return {
            "source": "警政署",
            "scam_type": "投資詐騙",
            "description": "受害者被誘導投入資金至假投資平台",
            "reported_at": "2024-01-15T10:30:00+00:00",
            "import_batch_id": str(uuid.uuid4()),
            "pii_removed": True,
        }

    def test_valid_batch_passes(self) -> None:
        """合法批次應通過驗證"""
        batch = [self._valid_record() for _ in range(3)]
        result = validate_case_report_batch(batch)
        assert result["valid"] is True
        assert result["accepted_count"] == 3

    def test_empty_batch_rejected(self) -> None:
        """空批次應被拒絕"""
        result = validate_case_report_batch([])
        assert result["valid"] is False
        assert result["error_code"] == "EMPTY_BATCH"

    def test_non_list_rejected(self) -> None:
        """非列表格式應被拒絕"""
        result = validate_case_report_batch({"source": "警政署"})
        assert result["valid"] is False
        assert result["error_code"] == "INVALID_FORMAT"

    def test_missing_required_field_rejected(self) -> None:
        """缺少必要欄位應被拒絕"""
        record = self._valid_record()
        del record["source"]
        result = validate_case_report_batch([record])
        assert result["valid"] is False
        assert any("source" in detail for detail in result["details"])

    def test_wrong_type_pii_removed_rejected(self) -> None:
        """pii_removed 型別錯誤應被拒絕"""
        record = self._valid_record()
        record["pii_removed"] = "yes"  # 應為 bool
        result = validate_case_report_batch([record])
        assert result["valid"] is False

    def test_empty_string_field_rejected(self) -> None:
        """空字串欄位應被拒絕"""
        record = self._valid_record()
        record["source"] = "   "  # 空白字串
        result = validate_case_report_batch([record])
        assert result["valid"] is False

    def test_invalid_date_format_rejected(self) -> None:
        """無效日期格式應被拒絕"""
        record = self._valid_record()
        record["reported_at"] = "not-a-date"
        result = validate_case_report_batch([record])
        assert result["valid"] is False

    def test_partial_invalid_rejects_whole_batch(self) -> None:
        """批次中有任一筆不合法應拒絕整批"""
        batch = [self._valid_record() for _ in range(3)]
        batch[1]["source"] = ""  # 第二筆不合法
        result = validate_case_report_batch(batch)
        assert result["valid"] is False
        assert result["accepted_count"] == 0
        assert result["rejected_count"] == 3

    def test_datetime_object_accepted(self) -> None:
        """reported_at 為 datetime 物件應通過驗證"""
        record = self._valid_record()
        record["reported_at"] = datetime.now(timezone.utc)
        result = validate_case_report_batch([record])
        assert result["valid"] is True


class TestPredictionScheduler:
    """排程器單元測試"""

    def test_scheduler_not_running_initially(self) -> None:
        """排程器初始狀態應為未執行"""
        scheduler = PredictionScheduler()
        assert scheduler.is_running is False

    def test_trigger_now_calls_analysis_func(self) -> None:
        """手動觸發應呼叫分析函數"""
        mock_func = MagicMock()
        scheduler = PredictionScheduler(analysis_func=mock_func)
        scheduler.trigger_now()
        mock_func.assert_called_once()

    def test_scheduler_start_and_stop(self) -> None:
        """排程器應可正常啟動與停止"""
        mock_func = MagicMock()
        scheduler = PredictionScheduler(analysis_func=mock_func, interval_hours=24)
        scheduler.start()
        assert scheduler.is_running is True
        scheduler.stop()
        assert scheduler.is_running is False
