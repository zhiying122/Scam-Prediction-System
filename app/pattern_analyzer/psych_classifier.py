"""
心理特徵分類器模組

使用規則式方法識別詐騙話術中的五類心理操控特徵：
信任建立、緊迫感製造、情緒勒索、權威偽裝、利益誘導。

每份樣本可標記多個特徵類別，輸出標籤必須屬於合法集合。

需求：2.3
"""

import re


# 合法的心理特徵標籤集合（五類）
VALID_PSYCHOLOGICAL_TAGS: frozenset[str] = frozenset({
    "信任建立",
    "緊迫感製造",
    "情緒勒索",
    "權威偽裝",
    "利益誘導",
})

# 各類特徵的關鍵詞規則（中英文混合）
_TRUST_BUILDING_PATTERNS: list[str] = [
    # 中文關鍵詞
    r"我是您的.*朋友",
    r"我們認識",
    r"您可以信任",
    r"為您著想",
    r"幫助您",
    r"保護您",
    r"您的利益",
    r"我了解您",
    r"我們一起",
    r"放心",
    r"安心",
    r"可靠",
    r"值得信賴",
    r"專業團隊",
    r"多年經驗",
    r"口碑",
    r"推薦",
    r"好評",
    r"客戶見證",
    r"成功案例",
    # 英文關鍵詞
    r"trust me",
    r"i'm here to help",
    r"for your benefit",
    r"we care about you",
    r"reliable",
    r"trusted",
]

_URGENCY_PATTERNS: list[str] = [
    # 中文關鍵詞
    r"立即",
    r"馬上",
    r"緊急",
    r"限時",
    r"今天",
    r"現在",
    r"快速",
    r"盡快",
    r"不要錯過",
    r"最後機會",
    r"即將截止",
    r"倒數",
    r"24小時",
    r"48小時",
    r"時間緊迫",
    r"趕快",
    r"速",
    r"急",
    r"過期",
    r"失效",
    r"凍結",
    r"封鎖",
    r"異常",
    # 英文關鍵詞
    r"urgent",
    r"immediately",
    r"right now",
    r"limited time",
    r"act now",
    r"expires",
    r"deadline",
    r"hurry",
    r"don't wait",
    r"last chance",
]

_EMOTIONAL_MANIPULATION_PATTERNS: list[str] = [
    # 中文關鍵詞
    r"您的家人",
    r"您的孩子",
    r"您的父母",
    r"家人安全",
    r"後悔",
    r"遺憾",
    r"對不起",
    r"愧疚",
    r"責任",
    r"義務",
    r"不孝",
    r"失職",
    r"傷心",
    r"難過",
    r"痛苦",
    r"受害",
    r"可憐",
    r"無辜",
    r"被騙",
    r"損失",
    r"賠償",
    r"補償",
    # 英文關鍵詞
    r"your family",
    r"your loved ones",
    r"feel guilty",
    r"you'll regret",
    r"it's your fault",
    r"you owe",
    r"responsibility",
]

_AUTHORITY_IMPERSONATION_PATTERNS: list[str] = [
    # 中文關鍵詞
    r"銀行",
    r"警察",
    r"警方",
    r"法院",
    r"檢察",
    r"政府",
    r"官方",
    r"客服",
    r"專員",
    r"主任",
    r"經理",
    r"總裁",
    r"董事",
    r"教授",
    r"博士",
    r"醫生",
    r"律師",
    r"會計師",
    r"金融監管",
    r"稅務",
    r"海關",
    r"移民",
    r"社會保險",
    r"健保",
    r"勞保",
    r"國稅局",
    r"財政部",
    r"金管會",
    r"調查局",
    r"刑事局",
    r"165",
    # 英文關鍵詞
    r"bank",
    r"police",
    r"government",
    r"official",
    r"authority",
    r"agent",
    r"officer",
    r"director",
    r"manager",
    r"irs",
    r"fbi",
    r"interpol",
]

_BENEFIT_LURE_PATTERNS: list[str] = [
    # 中文關鍵詞
    r"獲利",
    r"賺錢",
    r"投資",
    r"報酬",
    r"利潤",
    r"收益",
    r"分紅",
    r"獎金",
    r"獎勵",
    r"免費",
    r"贈品",
    r"優惠",
    r"折扣",
    r"中獎",
    r"抽獎",
    r"彩票",
    r"彩券",
    r"大獎",
    r"百萬",
    r"千萬",
    r"億",
    r"高報酬",
    r"穩定獲利",
    r"保證獲利",
    r"零風險",
    r"低風險",
    r"高利率",
    r"翻倍",
    r"暴富",
    r"財富自由",
    r"被動收入",
    # 英文關鍵詞
    r"profit",
    r"earn",
    r"investment",
    r"return",
    r"reward",
    r"bonus",
    r"free",
    r"prize",
    r"winner",
    r"million",
    r"guaranteed",
    r"risk.free",
    r"passive income",
]

# 規則對應表：標籤 -> 模式列表
_TAG_PATTERNS: dict[str, list[str]] = {
    "信任建立": _TRUST_BUILDING_PATTERNS,
    "緊迫感製造": _URGENCY_PATTERNS,
    "情緒勒索": _EMOTIONAL_MANIPULATION_PATTERNS,
    "權威偽裝": _AUTHORITY_IMPERSONATION_PATTERNS,
    "利益誘導": _BENEFIT_LURE_PATTERNS,
}


class PsychologicalClassifier:
    """
    心理特徵分類器

    使用規則式方法識別詐騙話術中的心理操控特徵。
    每份樣本可標記多個特徵類別，輸出標籤必須屬於合法集合。
    """

    def __init__(self):
        """初始化分類器，預編譯所有正則表達式以提升效能"""
        self._compiled_patterns: dict[str, list[re.Pattern]] = {}
        for tag, patterns in _TAG_PATTERNS.items():
            self._compiled_patterns[tag] = [
                re.compile(p, re.IGNORECASE | re.UNICODE)
                for p in patterns
            ]

    def classify(self, text: str) -> list[str]:
        """
        識別文本中的心理操控特徵標籤

        對輸入文本執行規則式比對，回傳所有匹配的特徵標籤。
        輸出標籤必須屬於 VALID_PSYCHOLOGICAL_TAGS 中的合法值。

        Args:
            text: 輸入文本（詐騙話術樣本）

        Returns:
            心理特徵標籤列表（可為空列表，標籤均屬合法集合）
        """
        if not text or not text.strip():
            return []

        matched_tags = []
        for tag, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    matched_tags.append(tag)
                    break  # 每個標籤只需匹配一次

        # 確保輸出標籤均屬合法集合（防禦性驗證）
        assert all(tag in VALID_PSYCHOLOGICAL_TAGS for tag in matched_tags), \
            f"分類器輸出了非法標籤：{set(matched_tags) - VALID_PSYCHOLOGICAL_TAGS}"

        return matched_tags

    def classify_batch(self, texts: list[str]) -> list[list[str]]:
        """
        批次處理多個文本的心理特徵分類

        Args:
            texts: 文本列表

        Returns:
            每個文本對應的心理特徵標籤列表
        """
        return [self.classify(text) for text in texts]
