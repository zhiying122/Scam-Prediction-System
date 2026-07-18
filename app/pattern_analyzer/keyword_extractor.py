"""
TF-IDF 關鍵詞提取模組

使用 scikit-learn 的 TF-IDF 演算法從文本中提取前 20 個關鍵詞，
確保輸出關鍵詞列表無重複詞彙。

中文處理策略：
  - 對中文文本使用字符 2-gram（bigram）切割，有效處理無空格分詞問題
  - 對英文/混合文本使用 word-level tokenizer
  - 自動偵測文本語言並選擇對應策略

需求：2.2
"""

import re
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


# 最大關鍵詞數量上限
MAX_KEYWORDS: int = 20

# 中文字符偵測（CJK Unified Ideographs）
_CJK_PATTERN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')


def _is_chinese_dominant(text: str) -> bool:
    """判斷文本是否以中文為主（CJK 字符佔比 > 30%）"""
    if not text:
        return False
    cjk_count = len(_CJK_PATTERN.findall(text))
    return cjk_count / max(len(text), 1) > 0.3


def _chinese_char_tokenize(text: str) -> list[str]:
    """
    中文字符 bigram 切割

    將中文文本切割為 2-gram 字符片段，過濾標點與空白。
    例：「請立即提供驗證碼」→ ['請立', '立即', '即提', '提供', '供驗', '驗證', '證碼']
    """
    # 提取 CJK 字符與英文字母數字序列
    tokens = []
    # 提取連續中文字符序列並做 bigram
    for chunk in re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]+', text):
        if len(chunk) == 1:
            tokens.append(chunk)
        else:
            tokens.extend(chunk[i:i+2] for i in range(len(chunk) - 1))
    # 提取英文詞彙
    for word in re.findall(r'[a-zA-Z0-9]+', text):
        if len(word) >= 2:
            tokens.append(word.lower())
    return tokens


class KeywordExtractor:
    """
    TF-IDF 關鍵詞提取器（支援中英文）

    使用 scikit-learn TfidfVectorizer 對單一文本或語料庫提取關鍵詞。
    中文文本使用字符 bigram，英文文本使用 word-level tokenizer。
    輸出關鍵詞列表長度 <= 20，且不含重複詞彙。
    """

    def __init__(self, max_keywords: int = MAX_KEYWORDS):
        """
        初始化關鍵詞提取器

        Args:
            max_keywords: 最大關鍵詞數量，預設 20
        """
        self._max_keywords = max_keywords

    def _make_vectorizer(self, is_chinese: bool) -> TfidfVectorizer:
        """建立對應語言的 TF-IDF 向量化器"""
        if is_chinese:
            # 中文：使用自訂 tokenizer（字符 bigram）
            return TfidfVectorizer(
                max_features=self._max_keywords * 3,
                tokenizer=_chinese_char_tokenize,
                token_pattern=None,   # 使用自訂 tokenizer 時須設為 None
                sublinear_tf=True,
                lowercase=False,
            )
        else:
            # 英文 / 混合：word-level
            return TfidfVectorizer(
                max_features=self._max_keywords * 2,
                analyzer="word",
                token_pattern=r"(?u)\b\w+\b",
                sublinear_tf=True,
            )

    def extract(self, text: str) -> list[str]:
        """
        從單一文本提取 TF-IDF 關鍵詞

        對單一文本使用 TF-IDF 計算詞彙重要性，
        回傳按 TF-IDF 分數降序排列的前 N 個關鍵詞。

        Args:
            text: 輸入文本（支援中文、英文、中英混合）

        Returns:
            關鍵詞列表（長度 <= 20，無重複）
        """
        if not text or not text.strip():
            return []

        is_chinese = _is_chinese_dominant(text)

        try:
            vectorizer = self._make_vectorizer(is_chinese)
            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]

            # 按分數降序排列，取前 N 個
            sorted_indices = np.argsort(scores)[::-1]
            keywords = []
            seen = set()

            for idx in sorted_indices:
                if scores[idx] == 0:
                    break
                word = feature_names[idx]
                if word not in seen:
                    keywords.append(word)
                    seen.add(word)
                if len(keywords) >= self._max_keywords:
                    break

            return keywords

        except ValueError:
            return []

    def extract_from_corpus(self, texts: list[str]) -> list[list[str]]:
        """
        從語料庫中為每個文本提取 TF-IDF 關鍵詞

        使用整個語料庫計算 IDF，使關鍵詞更具區分性。
        自動偵測語料庫主要語言（中文 / 英文）並選擇對應策略。

        Args:
            texts: 文本列表

        Returns:
            每個文本對應的關鍵詞列表
        """
        if not texts:
            return []

        valid_texts = [t if t and t.strip() else " " for t in texts]

        # 依整個語料庫的中文佔比決定策略
        combined = " ".join(valid_texts)
        is_chinese = _is_chinese_dominant(combined)

        try:
            vectorizer = self._make_vectorizer(is_chinese)
            # 調整 max_features 供語料庫模式
            if is_chinese:
                vectorizer.max_features = self._max_keywords * 4
            else:
                vectorizer.max_features = self._max_keywords * 2

            tfidf_matrix = vectorizer.fit_transform(valid_texts)
            feature_names = vectorizer.get_feature_names_out()

            results = []
            for i in range(len(texts)):
                scores = tfidf_matrix.toarray()[i]
                sorted_indices = np.argsort(scores)[::-1]
                keywords = []
                seen = set()

                for idx in sorted_indices:
                    if scores[idx] == 0:
                        break
                    word = feature_names[idx]
                    if word not in seen:
                        keywords.append(word)
                        seen.add(word)
                    if len(keywords) >= self._max_keywords:
                        break

                results.append(keywords)

            return results

        except ValueError:
            return [[] for _ in texts]
