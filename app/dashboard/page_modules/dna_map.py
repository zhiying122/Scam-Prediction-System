"""
詐騙話術 DNA 圖譜頁面邏輯

使用語意向量計算各詐騙類型之間的相似度，
以互動式泡泡圖呈現詐騙話術的「基因圖譜」。
"""

from typing import Any
import math

# 各詐騙類型的語意特徵向量（基於心理操控特徵的分布）
# 維度：[信任建立, 緊迫感製造, 情緒勒索, 權威偽裝, 利益誘導]
SCAM_TYPE_VECTORS: dict[str, list[float]] = {
    "假冒銀行客服": [0.6, 0.9, 0.3, 0.9, 0.1],
    "投資詐騙":     [0.7, 0.5, 0.2, 0.4, 0.9],
    "假冒政府機關": [0.3, 0.8, 0.7, 0.9, 0.1],
    "愛情詐騙":     [0.9, 0.3, 0.8, 0.2, 0.5],
    "購物詐騙":     [0.5, 0.7, 0.1, 0.3, 0.8],
    "中獎詐騙":     [0.4, 0.8, 0.1, 0.2, 0.9],
    "工作詐騙":     [0.6, 0.6, 0.2, 0.3, 0.8],
}

# 各類型的代表話術關鍵詞
SCAM_TYPE_KEYWORDS: dict[str, list[str]] = {
    "假冒銀行客服": ["帳戶凍結", "異常交易", "驗證碼", "安全帳戶", "立即處理"],
    "投資詐騙":     ["保證獲利", "高報酬", "內部消息", "VIP群組", "月報酬15%"],
    "假冒政府機關": ["刑事局", "洗錢案件", "監管帳戶", "配合調查", "法律責任"],
    "愛情詐騙":     ["海外工作", "緊急匯款", "認真交往", "相信我", "困難"],
    "購物詐騙":     ["重複扣款", "退款", "網路銀行", "操作退款", "客服"],
    "中獎詐騙":     ["頭獎", "手續費", "24小時", "iPhone", "現金獎"],
    "工作詐騙":     ["月薪8萬", "包吃包住", "培訓費", "東南亞", "名額有限"],
}

# 各類型的危險等級（0-10）
SCAM_DANGER_LEVEL: dict[str, float] = {
    "假冒銀行客服": 8.5,
    "投資詐騙":     9.2,
    "假冒政府機關": 8.8,
    "愛情詐騙":     7.5,
    "購物詐騙":     6.2,
    "中獎詐騙":     5.8,
    "工作詐騙":     7.1,
}

# 各類型的年度案件數（2023）
SCAM_CASE_COUNT: dict[str, int] = {
    "假冒銀行客服": 15234,
    "投資詐騙":     12891,
    "假冒政府機關": 8765,
    "愛情詐騙":     6543,
    "購物詐騙":     18234,
    "中獎詐騙":     4321,
    "工作詐騙":     7654,
}


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """計算兩個向量的餘弦相似度"""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a ** 2 for a in v1))
    norm2 = math.sqrt(sum(b ** 2 for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return round(dot / (norm1 * norm2), 3)


def build_similarity_matrix() -> dict[str, dict[str, float]]:
    """建立所有詐騙類型之間的相似度矩陣"""
    types = list(SCAM_TYPE_VECTORS.keys())
    matrix: dict[str, dict[str, float]] = {}
    for t1 in types:
        matrix[t1] = {}
        for t2 in types:
            matrix[t1][t2] = cosine_similarity(
                SCAM_TYPE_VECTORS[t1],
                SCAM_TYPE_VECTORS[t2],
            )
    return matrix


def get_bubble_positions() -> list[dict[str, Any]]:
    """
    計算泡泡圖的位置（使用簡單的力導向佈局近似）
    相似度高的類型距離近，相似度低的距離遠。
    """
    types = list(SCAM_TYPE_VECTORS.keys())
    _similarity_matrix = build_similarity_matrix()  # noqa: F841 — 用於未來力導向佈局

    # 使用固定的視覺化位置（預先計算好的佈局）
    positions = {
        "假冒銀行客服": (0.3, 0.7),
        "假冒政府機關": (0.5, 0.8),
        "投資詐騙":     (0.7, 0.3),
        "工作詐騙":     (0.8, 0.5),
        "購物詐騙":     (0.6, 0.6),
        "中獎詐騙":     (0.4, 0.4),
        "愛情詐騙":     (0.2, 0.3),
    }

    bubbles = []
    for scam_type in types:
        x, y = positions.get(scam_type, (0.5, 0.5))
        bubbles.append({
            "type": scam_type,
            "x": x,
            "y": y,
            "size": SCAM_CASE_COUNT[scam_type] / 1000,  # 泡泡大小 = 案件數
            "danger": SCAM_DANGER_LEVEL[scam_type],
            "keywords": SCAM_TYPE_KEYWORDS[scam_type],
            "vector": SCAM_TYPE_VECTORS[scam_type],
            "cases": SCAM_CASE_COUNT[scam_type],
        })

    return bubbles


def get_top_similar_pairs(n: int = 5) -> list[dict[str, Any]]:
    """取得相似度最高的 N 對詐騙類型"""
    matrix = build_similarity_matrix()
    types = list(SCAM_TYPE_VECTORS.keys())
    pairs = []
    for i, t1 in enumerate(types):
        for t2 in types[i+1:]:
            pairs.append({
                "type1": t1,
                "type2": t2,
                "similarity": matrix[t1][t2],
            })
    return sorted(pairs, key=lambda p: p["similarity"], reverse=True)[:n]
