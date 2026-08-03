"""
分群演算法與向量儲存模組

使用 K-Means 演算法對語意向量進行分群，自動決定群數（Elbow Method）。
確保每個向量的 cluster_label 為非空字串。

需求：2.4
"""

from typing import Optional

import numpy as np
from sklearn.cluster import KMeans


# 分群數量範圍
MIN_CLUSTERS: int = 2
MAX_CLUSTERS: int = 10

# 預設分群數量（當樣本數不足時使用）
DEFAULT_CLUSTER_COUNT: int = 2

# 詐騙類群標籤前綴
CLUSTER_LABEL_PREFIX: str = "詐騙類群"


def _find_optimal_k(vectors: np.ndarray, max_k: int = MAX_CLUSTERS) -> int:
    """
    使用 Elbow Method 自動決定最佳分群數量

    計算不同 k 值的 inertia（組內平方和），
    找出 inertia 下降趨勢明顯減緩的「肘點」。

    Args:
        vectors: 語意向量矩陣（n_samples x n_features）
        max_k: 最大嘗試的分群數量

    Returns:
        最佳分群數量 k
    """
    n_samples = len(vectors)

    # 樣本數不足時直接回傳最小值
    if n_samples <= MIN_CLUSTERS:
        return 1

    # 實際可用的最大 k 值（不能超過樣本數）
    actual_max_k = min(max_k, n_samples - 1)
    if actual_max_k < MIN_CLUSTERS:
        return MIN_CLUSTERS

    inertias = []
    k_range = range(MIN_CLUSTERS, actual_max_k + 1)

    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(vectors)
        inertias.append(kmeans.inertia_)

    # 使用 Elbow Method：找到 inertia 下降率最大的轉折點
    if len(inertias) <= 1:
        return MIN_CLUSTERS

    # 計算相鄰 inertia 的差值（二階差分）
    diffs = [inertias[i] - inertias[i + 1] for i in range(len(inertias) - 1)]
    if len(diffs) <= 1:
        return MIN_CLUSTERS

    second_diffs = [diffs[i] - diffs[i + 1] for i in range(len(diffs) - 1)]
    if not second_diffs:
        return MIN_CLUSTERS

    # 找到二階差分最大的位置（肘點）
    elbow_idx = second_diffs.index(max(second_diffs))
    optimal_k = list(k_range)[elbow_idx + 1]

    return optimal_k


def _make_cluster_label(cluster_id: int) -> str:
    """
    根據分群 ID 生成非空字串標籤

    Args:
        cluster_id: 分群編號（從 0 開始）

    Returns:
        非空字串標籤，格式為「詐騙類群-{N}」
    """
    label = f"{CLUSTER_LABEL_PREFIX}-{cluster_id + 1}"
    assert label and len(label) > 0, "cluster_label 不得為空字串"
    return label


class ScamClusterer:
    """
    詐騙話術語意向量分群器

    使用 K-Means 演算法對語意向量進行分群，
    自動決定最佳群數（Elbow Method）。
    確保每個向量的 cluster_label 為非空字串。
    """

    def __init__(
        self,
        min_clusters: int = MIN_CLUSTERS,
        max_clusters: int = MAX_CLUSTERS,
        random_state: int = 42,
    ):
        """
        初始化分群器

        Args:
            min_clusters: 最小分群數量
            max_clusters: 最大分群數量
            random_state: 隨機種子（確保結果可重現）
        """
        self._min_clusters = min_clusters
        self._max_clusters = max_clusters
        self._random_state = random_state
        self._kmeans: Optional[KMeans] = None
        self._cluster_count: int = 0

    def fit_predict(self, embeddings: list[list[float]]) -> list[str]:
        """
        對語意向量執行分群並回傳標籤列表

        自動決定最佳分群數量，對每個向量指派非空字串標籤。

        Args:
            embeddings: 語意向量列表（每個向量為 384 維 float 列表）

        Returns:
            cluster_label 列表，每個標籤為非空字串

        Raises:
            ValueError: 若輸入向量列表為空
        """
        if not embeddings:
            raise ValueError("輸入向量列表不得為空")

        vectors = np.array(embeddings)
        n_samples = len(vectors)

        # 樣本數為 1 時直接指派單一標籤
        if n_samples == 1:
            return [_make_cluster_label(0)]

        # 自動決定最佳分群數量
        optimal_k = _find_optimal_k(vectors, self._max_clusters)
        optimal_k = max(self._min_clusters, min(optimal_k, n_samples))

        # 執行 K-Means 分群
        self._kmeans = KMeans(
            n_clusters=optimal_k,
            random_state=self._random_state,
            n_init=10,
        )
        cluster_ids = self._kmeans.fit_predict(vectors)
        self._cluster_count = optimal_k

        # 將分群 ID 轉換為非空字串標籤
        labels = [_make_cluster_label(int(cid)) for cid in cluster_ids]

        # 防禦性驗證：確保所有標籤均為非空字串
        for label in labels:
            assert label and isinstance(label, str) and len(label) > 0, \
                f"cluster_label 不得為空字串，但得到：{repr(label)}"

        return labels

    def predict(self, embeddings: list[list[float]]) -> list[str]:
        """
        使用已訓練的模型對新向量進行分群預測

        Args:
            embeddings: 語意向量列表

        Returns:
            cluster_label 列表

        Raises:
            RuntimeError: 若尚未執行 fit_predict
        """
        if self._kmeans is None:
            raise RuntimeError("請先呼叫 fit_predict 訓練分群模型")

        vectors = np.array(embeddings)
        cluster_ids = self._kmeans.predict(vectors)
        labels = [_make_cluster_label(int(cid)) for cid in cluster_ids]

        for label in labels:
            assert label and isinstance(label, str) and len(label) > 0, \
                f"cluster_label 不得為空字串，但得到：{repr(label)}"

        return labels

    @property
    def cluster_count(self) -> int:
        """回傳目前的分群數量"""
        return self._cluster_count
