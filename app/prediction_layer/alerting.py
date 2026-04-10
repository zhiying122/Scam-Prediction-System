"""
預警事件生成與通知模組

偵測到異常模式時生成 AlertEvent，包含風險等級（高/中/低）與觸發特徵描述。
系統應在 5 分鐘內通知已訂閱的操作人員。
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.alert_event import AlertEvent, VALID_RISK_LEVELS

logger = logging.getLogger(__name__)

# 風險等級判斷閾值（基於異常向量比例）
# 注意：此閾值基於「異常比例」，與 risk_vector.py 的「綜合風險分數」閾值不同
HIGH_RISK_THRESHOLD = 0.3    # 異常比例 >= 30% 為高風險（異常比例維度）
MEDIUM_RISK_THRESHOLD = 0.1  # 異常比例 >= 10% 為中風險（異常比例維度）


def determine_risk_level(anomaly_ratio: float, trend_is_emerging: bool) -> str:
    """
    根據異常比例與趨勢判斷風險等級

    Args:
        anomaly_ratio: 異常向量比例（0.0 ~ 1.0）
        trend_is_emerging: 是否偵測到新興趨勢

    Returns:
        風險等級字串（高 / 中 / 低）
    """
    if anomaly_ratio >= HIGH_RISK_THRESHOLD or (trend_is_emerging and anomaly_ratio >= MEDIUM_RISK_THRESHOLD):
        return "高"
    elif anomaly_ratio >= MEDIUM_RISK_THRESHOLD or trend_is_emerging:
        return "中"
    else:
        return "低"


def build_trigger_features(
    analysis_result: dict[str, Any],
    vectors_data: list[dict[str, Any]],
) -> list[str]:
    """
    根據分析結果建立觸發特徵描述列表

    Args:
        analysis_result: 分析結果字典（來自 PredictionAnalyzer.run_analysis）
        vectors_data: 對應的語意向量資料列表

    Returns:
        觸發特徵描述列表（至少一個非空項目）
    """
    features: list[str] = []

    anomaly_indices = analysis_result.get("anomalies", [])
    anomaly_ratio = analysis_result.get("anomaly_ratio", 0.0)
    trend = analysis_result.get("trend", {})

    if anomaly_indices:
        features.append(
            f"偵測到 {len(anomaly_indices)} 個異常語意向量（異常比例：{anomaly_ratio:.1%}）"
        )

        # 提取異常向量的分群標籤
        anomaly_clusters: set[str] = set()
        for idx in anomaly_indices:
            if idx < len(vectors_data):
                label = vectors_data[idx].get("cluster_label", "")
                if label:
                    anomaly_clusters.add(label)

        if anomaly_clusters:
            features.append(f"異常集中於詐騙類群：{', '.join(sorted(anomaly_clusters))}")

    if trend.get("is_emerging"):
        change_rate = trend.get("change_rate", 0.0)
        features.append(f"新興詐騙手法頻率上升（變化率：{change_rate:+.1%}）")

    # 確保至少有一個特徵描述
    if not features:
        features.append("系統偵測到潛在異常模式，建議人工審查")

    return features


class AlertingService:
    """
    預警服務

    負責生成 AlertEvent 並通知已訂閱的操作人員。
    通知機制使用 in-memory 佇列模擬（實際部署時替換為 WebSocket / SMTP）。
    """

    def __init__(self) -> None:
        # in-memory 儲存（模擬 PostgreSQL）
        self._alert_store: list[AlertEvent] = []
        # 已訂閱的操作人員列表（模擬）
        self._subscribed_operators: list[str] = []

    def subscribe_operator(self, operator_id: str) -> None:
        """
        訂閱預警通知

        Args:
            operator_id: 操作人員識別碼
        """
        if operator_id not in self._subscribed_operators:
            self._subscribed_operators.append(operator_id)
            logger.info("操作人員 %s 已訂閱預警通知", operator_id)

    def generate_alert(
        self,
        analysis_result: dict[str, Any],
        vectors_data: list[dict[str, Any]],
        risk_vector_id: str,
    ) -> AlertEvent | None:
        """
        根據分析結果生成預警事件

        僅在偵測到異常或新興趨勢時生成預警。

        Args:
            analysis_result: 分析結果字典
            vectors_data: 對應的語意向量資料列表
            risk_vector_id: 關聯的 RiskVector UUID

        Returns:
            生成的 AlertEvent，若無異常則回傳 None
        """
        has_anomaly = analysis_result.get("has_anomaly", False)
        trend = analysis_result.get("trend", {})
        is_emerging = trend.get("is_emerging", False)

        if not has_anomaly and not is_emerging:
            logger.debug("未偵測到異常，不生成預警事件")
            return None

        anomaly_ratio = analysis_result.get("anomaly_ratio", 0.0)
        risk_level = determine_risk_level(anomaly_ratio, is_emerging)
        trigger_features = build_trigger_features(analysis_result, vectors_data)

        now = datetime.now(timezone.utc)
        alert = AlertEvent(
            id=str(uuid.uuid4()),
            risk_level=risk_level,
            trigger_features=trigger_features,
            risk_vector_id=risk_vector_id,
            notified_operators=list(self._subscribed_operators),
            notified_at=now,
            created_at=now,
        )

        self._alert_store.append(alert)
        self._notify_operators(alert)
        logger.info(
            "預警事件已生成：ID=%s，風險等級=%s，觸發特徵數=%d",
            alert.id,
            alert.risk_level,
            len(alert.trigger_features),
        )
        return alert

    def _notify_operators(self, alert: AlertEvent) -> None:
        """
        通知已訂閱的操作人員（模擬實作）

        實際部署時應替換為 WebSocket 推播或 SMTP 郵件通知。

        Args:
            alert: 要通知的預警事件
        """
        for operator_id in alert.notified_operators:
            logger.info(
                "通知操作人員 %s：風險等級 %s 預警事件（ID=%s）",
                operator_id,
                alert.risk_level,
                alert.id,
            )

    def get_alerts(self, limit: int = 100) -> list[AlertEvent]:
        """
        取得最新預警事件列表

        Args:
            limit: 最多回傳的事件數量

        Returns:
            預警事件列表（依建立時間降序）
        """
        return sorted(
            self._alert_store[-limit:],
            key=lambda a: a.created_at,
            reverse=True,
        )

    def create_alert_from_params(
        self,
        risk_level: str,
        trigger_features: list[str],
        risk_vector_id: str,
        notified_operators: list[str] | None = None,
    ) -> AlertEvent:
        """
        直接從參數建立預警事件（供外部呼叫使用）

        Args:
            risk_level: 風險等級（高 / 中 / 低）
            trigger_features: 觸發特徵描述列表（至少一個非空項目）
            risk_vector_id: 關聯的 RiskVector UUID
            notified_operators: 要通知的操作人員列表

        Returns:
            建立的 AlertEvent

        Raises:
            ValueError: 若風險等級不合法或觸發特徵為空
        """
        if risk_level not in VALID_RISK_LEVELS:
            raise ValueError(f"risk_level 必須為 高/中/低 之一，實際值：{risk_level}")

        non_empty_features = [f for f in trigger_features if f and f.strip()]
        if not non_empty_features:
            raise ValueError("trigger_features 必須包含至少一個非空的觸發特徵描述")

        now = datetime.now(timezone.utc)
        operators = notified_operators if notified_operators is not None else list(self._subscribed_operators)

        alert = AlertEvent(
            id=str(uuid.uuid4()),
            risk_level=risk_level,
            trigger_features=non_empty_features,
            risk_vector_id=risk_vector_id,
            notified_operators=operators,
            notified_at=now,
            created_at=now,
        )

        self._alert_store.append(alert)
        logger.info("預警事件已建立：ID=%s，風險等級=%s", alert.id, alert.risk_level)
        return alert
