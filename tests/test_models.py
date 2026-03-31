"""
核心資料模型單元測試

驗證所有資料類別的初始化、驗證邏輯與不變量。
"""

import uuid
from datetime import datetime, timezone

import pytest

from app.models import (
    AccessLog,
    AlertEvent,
    CaseReport,
    ModelVersion,
    RiskVector,
    ScamScript,
    SemanticVector,
)


class TestScamScript:
    """ScamScript 資料模型測試"""

    def test_建立合法的詐騙腳本(self, sample_scam_script_data: dict) -> None:
        """正常建立 ScamScript 實例"""
        script = ScamScript(**sample_scam_script_data)
        assert script.id == sample_scam_script_data["id"]
        assert script.is_regulated is True

    def test_is_regulated_恆為_True(self, sample_scam_script_data: dict) -> None:
        """is_regulated 設為 False 時應拋出 ValueError（需求 1.5）"""
        sample_scam_script_data["is_regulated"] = False
        with pytest.raises(ValueError, match="is_regulated 必須恆為 True"):
            ScamScript(**sample_scam_script_data)

    def test_心理標籤為列表(self, sample_scam_script_data: dict) -> None:
        """psychological_tags 應為列表型別"""
        script = ScamScript(**sample_scam_script_data)
        assert isinstance(script.psychological_tags, list)


class TestRiskVector:
    """RiskVector 資料模型測試"""

    def test_建立合法的風險向量(self, sample_risk_vector_data: dict) -> None:
        """正常建立 RiskVector 實例"""
        rv = RiskVector(**sample_risk_vector_data)
        assert rv.risk_score == 0.85
        assert rv.risk_level == "高"

    def test_風險分數超出範圍應拋出例外(self, sample_risk_vector_data: dict) -> None:
        """risk_score 超出 [0.0, 1.0] 時應拋出 ValueError"""
        sample_risk_vector_data["risk_score"] = 1.5
        with pytest.raises(ValueError, match="risk_score 必須在"):
            RiskVector(**sample_risk_vector_data)

    def test_非法風險等級應拋出例外(self, sample_risk_vector_data: dict) -> None:
        """risk_level 不在合法集合時應拋出 ValueError"""
        sample_risk_vector_data["risk_level"] = "極高"
        with pytest.raises(ValueError, match="risk_level 必須為"):
            RiskVector(**sample_risk_vector_data)

    @pytest.mark.parametrize("level", ["高", "中", "低"])
    def test_所有合法風險等級(self, sample_risk_vector_data: dict, level: str) -> None:
        """高/中/低 三個等級均應合法"""
        sample_risk_vector_data["risk_level"] = level
        rv = RiskVector(**sample_risk_vector_data)
        assert rv.risk_level == level


class TestAlertEvent:
    """AlertEvent 資料模型測試"""

    def test_建立合法的預警事件(self, sample_alert_event_data: dict) -> None:
        """正常建立 AlertEvent 實例"""
        event = AlertEvent(**sample_alert_event_data)
        assert event.risk_level == "高"

    def test_非法風險等級應拋出例外(self, sample_alert_event_data: dict) -> None:
        """risk_level 不在合法集合時應拋出 ValueError"""
        sample_alert_event_data["risk_level"] = "緊急"
        with pytest.raises(ValueError, match="risk_level 必須為"):
            AlertEvent(**sample_alert_event_data)


class TestModelVersion:
    """ModelVersion 資料模型測試"""

    def test_建立合法的模型版本(self, sample_model_version_data: dict) -> None:
        """正常建立 ModelVersion 實例"""
        mv = ModelVersion(**sample_model_version_data)
        assert mv.version == "1.0.0"
        assert mv.is_active is True

    def test_微調前準確率超出範圍應拋出例外(self, sample_model_version_data: dict) -> None:
        """accuracy_before 超出 [0.0, 1.0] 時應拋出 ValueError"""
        sample_model_version_data["accuracy_before"] = -0.1
        with pytest.raises(ValueError, match="accuracy_before 必須在"):
            ModelVersion(**sample_model_version_data)

    def test_微調後準確率超出範圍應拋出例外(self, sample_model_version_data: dict) -> None:
        """accuracy_after 超出 [0.0, 1.0] 時應拋出 ValueError"""
        sample_model_version_data["accuracy_after"] = 1.1
        with pytest.raises(ValueError, match="accuracy_after 必須在"):
            ModelVersion(**sample_model_version_data)


class TestCaseReport:
    """CaseReport 資料模型測試"""

    def test_建立合法的報案資料(self, sample_case_report_data: dict) -> None:
        """正常建立 CaseReport 實例"""
        report = CaseReport(**sample_case_report_data)
        assert report.pii_removed is True
        assert report.source == "警政署"


class TestAccessLog:
    """AccessLog 資料模型測試"""

    def test_建立合法的存取日誌(self, sample_access_log_data: dict) -> None:
        """正常建立 AccessLog 實例"""
        log = AccessLog(**sample_access_log_data)
        assert log.action == "read"
        assert len(log.current_hash) == 64
