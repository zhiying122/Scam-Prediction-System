"""
Risk_Vector 生成與儲存模組

生成包含高風險語意特徵、詐騙類群標籤、風險分數（0.0~1.0）、
風險等級、時間範圍、版本號的 RiskVector。
儲存至 in-memory（模擬 PostgreSQL），同步更新 Redis 快取（mock）。
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.risk_vector import RiskVector, VALID_RISK_LEVELS

logger = logging.getLogger(__name__)

# 風險分數對應風險等級的閾值
HIGH_SCORE_THRESHOLD = 0.7   # 分數 >= 0.7 為高風險
MEDIUM_SCORE_THRESHOLD = 0.4  # 分數 >= 0.4 為中風險

# 當前模型版本號
CURRENT_MODEL_VERSION = "1.0.0"


def score_to_risk_level(risk_score: float) -> str:
    """
    將風險分數轉換為風險等級

    Args:
        risk_score: 風險分數（0.0 ~ 1.0）

    Returns:
        風險等級字串（高 / 中 / 低）
    """
    if risk_score >= HIGH_SCORE_THRESHOLD:
        return "高"
    elif risk_score >= MEDIUM_SCORE_THRESHOLD:
        return "中"
    else:
        return "低"


def calculate_risk_score(
    anomaly_ratio: float,
    trend_change_rate: float,
    is_emerging: bool,
) -> float:
    """
    根據異常比例與趨勢計算風險分數

    Args:
        anomaly_ratio: 異常向量比例（0.0 ~ 1.0）
        trend_change_rate: 趨勢變化率（可為負值）
        is_emerging: 是否為新興趨勢

    Returns:
        風險分數（0.0 ~ 1.0）
    """
    # 基礎分數來自異常比例（anomaly_ratio >= 0.3 時達到上限 0.6）
    # 乘以 2.0 使 30% 異常比例即可達到基礎分數上限，避免過度依賴單一指標
    base_score = min(anomaly_ratio * 2.0, 0.6)

    # 趨勢加成（最高 0.3）
    trend_bonus = 0.0
    if is_emerging:
        trend_bonus = min(abs(trend_change_rate) * 0.5, 0.3)

    # 新興趨勢額外加成（0.1）
    emerging_bonus = 0.1 if is_emerging else 0.0

    raw_score = base_score + trend_bonus + emerging_bonus
    # 確保分數在 [0.0, 1.0] 範圍內
    return round(min(max(raw_score, 0.0), 1.0), 4)


class MockRedisCache:
    """
    模擬 Redis 快取（in-memory 實作）

    在測試環境中替代實際 Redis 連線，
    提供相同的 get/set 介面。
    """

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """設定快取值"""
        self._store[key] = value

    def get(self, key: str) -> str | None:
        """取得快取值"""
        return self._store.get(key)

    def delete(self, key: str) -> None:
        """刪除快取值"""
        self._store.pop(key, None)

    def keys(self) -> list[str]:
        """取得所有快取鍵"""
        return list(self._store.keys())


class RiskVectorRepository:
    """
    Risk_Vector 儲存庫

    提供 RiskVector 的 CRUD 操作，
    使用 in-memory 儲存模擬 PostgreSQL，並同步更新 Redis 快取。
    """

    def __init__(self, redis_cache: MockRedisCache | None = None) -> None:
        # in-memory 儲存（模擬 PostgreSQL）
        self._store: dict[str, RiskVector] = {}
        # Redis 快取（mock）
        self._cache = redis_cache or MockRedisCache()
        self._cache_ttl = 86400  # 24 小時 TTL

    def save(self, risk_vector: RiskVector) -> RiskVector:
        """
        儲存 RiskVector 至 in-memory 儲存區並更新快取

        Args:
            risk_vector: 要儲存的 RiskVector

        Returns:
            已儲存的 RiskVector
        """
        self._store[risk_vector.id] = risk_vector

        # 同步更新 Redis 快取
        cache_key = f"risk_vector:{risk_vector.id}"
        cache_value = self._serialize(risk_vector)
        self._cache.set(cache_key, cache_value, ttl=self._cache_ttl)

        logger.info("RiskVector 已儲存：ID=%s，風險等級=%s", risk_vector.id, risk_vector.risk_level)
        return risk_vector

    def get_by_id(self, vector_id: str) -> RiskVector | None:
        """
        依 ID 查詢 RiskVector（優先從快取讀取）

        Args:
            vector_id: RiskVector UUID

        Returns:
            RiskVector 或 None（若不存在）
        """
        # 先查快取
        cache_key = f"risk_vector:{vector_id}"
        cached = self._cache.get(cache_key)
        if cached:
            return self._deserialize(cached)

        # 快取未命中，從 in-memory 儲存讀取
        return self._store.get(vector_id)

    def get_all(self) -> list[RiskVector]:
        """取得所有 RiskVector（依建立時間降序）"""
        return sorted(
            self._store.values(),
            key=lambda v: v.created_at,
            reverse=True,
        )

    def _serialize(self, risk_vector: RiskVector) -> str:
        """將 RiskVector 序列化為 JSON 字串"""
        data = {
            "id": risk_vector.id,
            "high_risk_features": risk_vector.high_risk_features,
            "scam_cluster_label": risk_vector.scam_cluster_label,
            "risk_score": risk_vector.risk_score,
            "risk_level": risk_vector.risk_level,
            "time_range_start": risk_vector.time_range_start.isoformat(),
            "time_range_end": risk_vector.time_range_end.isoformat(),
            "version": risk_vector.version,
            "created_at": risk_vector.created_at.isoformat(),
        }
        return json.dumps(data, ensure_ascii=False)

    def _deserialize(self, json_str: str) -> RiskVector:
        """將 JSON 字串反序列化為 RiskVector"""
        data = json.loads(json_str)
        return RiskVector(
            id=data["id"],
            high_risk_features=data["high_risk_features"],
            scam_cluster_label=data["scam_cluster_label"],
            risk_score=data["risk_score"],
            risk_level=data["risk_level"],
            time_range_start=datetime.fromisoformat(data["time_range_start"]),
            time_range_end=datetime.fromisoformat(data["time_range_end"]),
            version=data["version"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


class RiskVectorGenerator:
    """
    Risk_Vector 生成器

    根據分析結果生成 RiskVector，並透過 RiskVectorRepository 儲存。
    """

    def __init__(
        self,
        repository: RiskVectorRepository | None = None,
        model_version: str = CURRENT_MODEL_VERSION,
    ) -> None:
        self._repository = repository or RiskVectorRepository()
        self._model_version = model_version

    def generate(
        self,
        analysis_result: dict[str, Any],
        vectors_data: list[dict[str, Any]],
    ) -> RiskVector:
        """
        根據分析結果生成 RiskVector

        Args:
            analysis_result: 分析結果字典（來自 PredictionAnalyzer.run_analysis）
            vectors_data: 對應的語意向量資料列表

        Returns:
            生成並儲存的 RiskVector
        """
        now = datetime.now(timezone.utc)
        time_range_start = analysis_result.get("time_range_start", now)
        time_range_end = analysis_result.get("time_range_end", now)

        # 計算風險分數
        anomaly_ratio = analysis_result.get("anomaly_ratio", 0.0)
        trend = analysis_result.get("trend", {})
        trend_change_rate = trend.get("change_rate", 0.0)
        is_emerging = trend.get("is_emerging", False)

        risk_score = calculate_risk_score(anomaly_ratio, trend_change_rate, is_emerging)
        risk_level = score_to_risk_level(risk_score)

        # 提取高風險語意特徵
        high_risk_features = self._extract_high_risk_features(
            analysis_result, vectors_data
        )

        # 提取主要詐騙類群標籤
        scam_cluster_label = self._extract_dominant_cluster(vectors_data)

        risk_vector = RiskVector(
            id=str(uuid.uuid4()),
            high_risk_features=high_risk_features,
            scam_cluster_label=scam_cluster_label,
            risk_score=risk_score,
            risk_level=risk_level,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            version=self._model_version,
            created_at=now,
        )

        return self._repository.save(risk_vector)

    def generate_from_params(
        self,
        high_risk_features: list[str],
        scam_cluster_label: str,
        risk_score: float,
        time_range_start: datetime,
        time_range_end: datetime,
        version: str | None = None,
    ) -> RiskVector:
        """
        直接從參數生成 RiskVector（供外部呼叫使用）

        Args:
            high_risk_features: 高風險語意特徵列表（至少一個）
            scam_cluster_label: 詐騙類群標籤（非空字串）
            risk_score: 風險分數（0.0 ~ 1.0）
            time_range_start: 分析時間範圍起始
            time_range_end: 分析時間範圍結束
            version: 模型版本號（預設使用當前版本）

        Returns:
            生成並儲存的 RiskVector

        Raises:
            ValueError: 若參數不合法
        """
        if not high_risk_features or not any(f.strip() for f in high_risk_features):
            raise ValueError("high_risk_features 必須包含至少一個非空的語意特徵")

        if not scam_cluster_label or not scam_cluster_label.strip():
            raise ValueError("scam_cluster_label 不可為空字串")

        if not (0.0 <= risk_score <= 1.0):
            raise ValueError(f"risk_score 必須在 [0.0, 1.0] 範圍內，實際值：{risk_score}")

        risk_level = score_to_risk_level(risk_score)
        now = datetime.now(timezone.utc)

        risk_vector = RiskVector(
            id=str(uuid.uuid4()),
            high_risk_features=[f for f in high_risk_features if f.strip()],
            scam_cluster_label=scam_cluster_label.strip(),
            risk_score=risk_score,
            risk_level=risk_level,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            version=version or self._model_version,
            created_at=now,
        )

        return self._repository.save(risk_vector)

    def calculate_accuracy(
        self, predictions: list[float], actuals: list[float]
    ) -> float:
        """
        計算預測準確率

        將預測值與真實值進行比對，計算準確率。
        結果保證在 [0.0, 1.0] 閉區間內。

        Args:
            predictions: 預測值列表（0.0 ~ 1.0 的風險分數）
            actuals: 真實值列表（0.0 ~ 1.0 的風險分數）

        Returns:
            預測準確率（0.0 ~ 1.0）

        Raises:
            ValueError: 若輸入列表為空或長度不一致
        """
        if not predictions or not actuals:
            raise ValueError("predictions 與 actuals 不可為空列表")

        # 取兩者的最小長度進行比對
        n = min(len(predictions), len(actuals))
        if n == 0:
            return 0.0

        # 將連續分數轉換為二元分類（>= 0.5 為高風險）
        threshold = 0.5
        correct = sum(
            1
            for p, a in zip(predictions[:n], actuals[:n])
            if (p >= threshold) == (a >= threshold)
        )

        accuracy = correct / n
        # 確保結果在 [0.0, 1.0] 閉區間
        return min(max(accuracy, 0.0), 1.0)

    def _extract_high_risk_features(
        self,
        analysis_result: dict[str, Any],
        vectors_data: list[dict[str, Any]],
    ) -> list[str]:
        """
        從分析結果提取高風險語意特徵

        Args:
            analysis_result: 分析結果字典
            vectors_data: 語意向量資料列表

        Returns:
            高風險語意特徵列表（至少一個）
        """
        features: list[str] = []
        anomaly_indices = analysis_result.get("anomalies", [])

        # 從異常向量提取關鍵詞
        for idx in anomaly_indices[:10]:  # 最多取前 10 個異常向量
            if idx < len(vectors_data):
                keywords = vectors_data[idx].get("top_keywords", [])
                features.extend(keywords[:3])  # 每個向量取前 3 個關鍵詞

        # 去重並保留非空特徵
        seen: set[str] = set()
        unique_features: list[str] = []
        for f in features:
            if f and f not in seen:
                seen.add(f)
                unique_features.append(f)

        # 確保至少有一個特徵
        if not unique_features:
            trend = analysis_result.get("trend", {})
            if trend.get("is_emerging"):
                unique_features.append("新興詐騙手法頻率異常上升")
            else:
                unique_features.append("語意向量分布異常")

        return unique_features

    def _extract_dominant_cluster(self, vectors_data: list[dict[str, Any]]) -> str:
        """
        從向量資料提取主要詐騙類群標籤

        Args:
            vectors_data: 語意向量資料列表

        Returns:
            出現頻率最高的詐騙類群標籤（非空字串）
        """
        from collections import Counter

        labels = [
            v.get("cluster_label", "")
            for v in vectors_data
            if v.get("cluster_label", "").strip()
        ]

        if not labels:
            return "未分類詐騙手法"

        counter = Counter(labels)
        return counter.most_common(1)[0][0]
