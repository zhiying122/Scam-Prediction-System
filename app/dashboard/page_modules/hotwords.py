"""
熱詞排行榜頁面邏輯

提供詐騙熱詞排行榜的計算函數，按頻率降序排列，最多回傳前 20 名。
每 24 小時自動更新，資料來源為 Pattern_Analyzer 提取的關鍵詞頻率。

需求：4.1
"""

from typing import Any


def compute_hotword_ranking(keyword_freq: dict[str, Any]) -> list[str]:
    """
    計算熱詞排行榜

    依關鍵詞出現頻率降序排列，回傳前 20 名熱詞列表。
    若頻率相同，則依字典序排列以確保結果穩定。

    Args:
        keyword_freq: 關鍵詞與其頻率的對應字典，例如 {"詐騙": 100, "轉帳": 80}

    Returns:
        按頻率降序排列的熱詞列表，長度 <= 20

    需求：4.1
    """
    if not keyword_freq:
        return []

    # 過濾非數值頻率，並確保頻率為正數
    valid_items = [
        (word, freq)
        for word, freq in keyword_freq.items()
        if isinstance(freq, (int, float)) and freq > 0 and word
    ]

    # 依頻率降序排列（頻率相同時依字典序升序，確保穩定性）
    sorted_items = sorted(valid_items, key=lambda x: (-x[1], x[0]))

    # 回傳前 20 名熱詞
    return [word for word, _ in sorted_items[:20]]


def get_hotword_page_data(keyword_freq: dict[str, Any]) -> dict:
    """
    取得熱詞排行榜頁面資料

    整合熱詞排行計算結果，回傳頁面所需的完整資料結構。

    Args:
        keyword_freq: 關鍵詞頻率字典

    Returns:
        包含排行榜資料的字典，格式為：
        {
            "ranking": list[str],       # 熱詞排行列表（最多 20 筆）
            "total_keywords": int,      # 原始關鍵詞總數
            "displayed_count": int,     # 實際顯示筆數
        }
    """
    ranking = compute_hotword_ranking(keyword_freq)
    return {
        "ranking": ranking,
        "total_keywords": len(keyword_freq),
        "displayed_count": len(ranking),
    }
