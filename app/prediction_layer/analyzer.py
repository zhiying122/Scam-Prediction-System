"""
預測分析模組

載入最新語意向量批次，執行時間序列趨勢分析與異常偵測。
使用 Isolation Forest 進行異常偵測，識別新興詐騙手法的趨勢變化。
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

# 異常偵測預設參數
DEFAULT_CONTAMINATION = 0.1  # 預期異常比例（10%）
DEFAULT_N_ESTIMATORS = 100   # Isolation Forest 樹的數量


class AnomalyDetector:
    """
    異常偵測器

    使用 Isolation Forest 對語意向量批次執行異常偵測，
    識別偏離正常分布的新興詐騙手法。
    """

    def __init__(
        self,
        contamination: float = DEFAULT_CONTAMINATION,
        n_estimators: int = DEFAULT_N_ESTIMATORS,
        random_state: int = 42,
    ) -> None:
        """
        初始化異常偵測器

        Args:
            contamination: 預期異常比例（0.0 ~ 0.5）
            n_estimators: Isolation Forest 樹的數量
            random_state: 隨機種子（確保可重現性）
        """
        self._model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
        )
        self._is_fitted = False

    def fit_predict(self, vectors: list[list[float]]) -> list[bool]:
        """
        訓練並預測異常

        Args:
            vectors: 語意向量列表，每個向量為浮點數列表

        Returns:
            布林列表，True 表示該向量為異常點

        Raises:
            ValueError: 若向量列表為空
        """
        if not vectors:
            raise ValueError("向量列表不可為空")

        X = np.array(vectors)
        # Isolation Forest 回傳 -1（異常）或 1（正常）
        predictions = self._model.fit_predict(X)
        self._is_fitted = True
        return [pred == -1 for pred in predictions]

    def detect_anomalies(self, vectors: list[list[float]]) -> dict[str, Any]:
        """
        執行異常偵測並回傳詳細結果

        Args:
            vectors: 語意向量列表

        Returns:
            包含異常索引、異常比例與異常分數的字典
        """
        if not vectors:
            return {"anomaly_indices": [], "anomaly_ratio": 0.0, "scores": []}

        is_anomaly = self.fit_predict(vectors)
        X = np.array(vectors)
        scores = self._model.score_samples(X).tolist()

        anomaly_indices = [i for i, flag in enumerate(is_anomaly) if flag]
        anomaly_ratio = len(anomaly_indices) / len(vectors)

        return {
            "anomaly_indices": anomaly_indices,
            "anomaly_ratio": anomaly_ratio,
            "scores": scores,
        }


class TrendAnalyzer:
    """
    趨勢分析器

    對累積的語意向量執行簡單的時間序列趨勢分析，
    識別新興詐騙手法的頻率變化趨勢。
    """

    def analyze_trend(
        self, time_series: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        分析時間序列趨勢

        Args:
            time_series: 時間序列資料，每筆包含 timestamp 與 count

        Returns:
            趨勢分析結果，包含趨勢方向（上升/下降/穩定）與變化率
        """
        if len(time_series) < 2:
            return {"trend": "資料不足", "change_rate": 0.0, "is_emerging": False}

        counts = [item.get("count", 0) for item in time_series]
        # 計算簡單線性趨勢（最後一期 vs 前一期的變化率）
        recent = counts[-1]
        previous = counts[-2] if counts[-2] != 0 else 1
        change_rate = (recent - previous) / abs(previous)

        if change_rate > 0.2:
            trend = "上升"
            is_emerging = True
        elif change_rate < -0.2:
            trend = "下降"
            is_emerging = False
        else:
            trend = "穩定"
            is_emerging = False

        return {
            "trend": trend,
            "change_rate": round(change_rate, 4),
            "is_emerging": is_emerging,
        }


class PredictionAnalyzer:
    """
    預測分析主控器

    整合異常偵測與趨勢分析，對語意向量批次執行完整分析流程。
    分析結果用於生成 AlertEvent 與 RiskVector。
    """

    def __init__(self) -> None:
        self._anomaly_detector = AnomalyDetector()
        self._trend_analyzer = TrendAnalyzer()
        # in-memory 儲存（模擬資料庫）
        self._vector_store: list[dict[str, Any]] = []
        self._analysis_results: list[dict[str, Any]] = []

    def load_latest_vectors(self, limit: int = 1000) -> list[dict[str, Any]]:
        """
        載入最新語意向量批次

        Args:
            limit: 最多載入的向量數量

        Returns:
            語意向量資料列表
        """
        return self._vector_store[-limit:] if self._vector_store else []

    def add_vectors(self, vectors: list[dict[str, Any]]) -> None:
        """
        新增語意向量至儲存區（供測試與整合使用）

        Args:
            vectors: 語意向量資料列表，每筆需包含 embedding 與 cluster_label
        """
        self._vector_store.extend(vectors)

    def run_analysis(self) -> dict[str, Any]:
        """
        執行完整分析流程

        載入最新向量批次，執行趨勢分析與異常偵測，
        回傳分析結果供後續生成 AlertEvent 與 RiskVector 使用。

        Returns:
            分析結果字典，包含異常偵測結果、趨勢分析結果與時間範圍
        """
        now = datetime.now(timezone.utc)
        time_range_start = now - timedelta(hours=24)

        vectors_data = self.load_latest_vectors()
        logger.info("載入 %d 筆語意向量進行分析", len(vectors_data))

        result: dict[str, Any] = {
            "analysis_id": str(uuid.uuid4()),
            "time_range_start": time_range_start,
            "time_range_end": now,
            "vector_count": len(vectors_data),
            "anomalies": [],
            "trend": {"trend": "資料不足", "change_rate": 0.0, "is_emerging": False},
            "has_anomaly": False,
        }

        if not vectors_data:
            logger.info("無可用向量資料，跳過分析")
            self._analysis_results.append(result)
            return result

        # 提取嵌入向量
        embeddings = [v["embedding"] for v in vectors_data if "embedding" in v]
        if embeddings:
            anomaly_result = self._anomaly_detector.detect_anomalies(embeddings)
            result["anomalies"] = anomaly_result["anomaly_indices"]
            result["anomaly_ratio"] = anomaly_result["anomaly_ratio"]
            result["has_anomaly"] = len(anomaly_result["anomaly_indices"]) > 0

        # 執行趨勢分析（依時間分組計算頻率）
        time_series = self._build_time_series(vectors_data)
        result["trend"] = self._trend_analyzer.analyze_trend(time_series)

        self._analysis_results.append(result)
        logger.info(
            "分析完成：偵測到 %d 個異常點，趨勢：%s",
            len(result["anomalies"]),
            result["trend"]["trend"],
        )
        return result

    def _build_time_series(
        self, vectors_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        將向量資料轉換為時間序列格式

        Args:
            vectors_data: 語意向量資料列表

        Returns:
            按小時分組的時間序列資料
        """
        from collections import defaultdict

        hourly_counts: dict[str, int] = defaultdict(int)
        for v in vectors_data:
            created_at = v.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    continue
            if isinstance(created_at, datetime):
                hour_key = created_at.strftime("%Y-%m-%dT%H:00:00")
                hourly_counts[hour_key] += 1

        return [
            {"timestamp": ts, "count": count}
            for ts, count in sorted(hourly_counts.items())
        ]
