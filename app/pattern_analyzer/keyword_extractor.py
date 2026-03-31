"""
TF-IDF 關鍵詞提取模組

使用 scikit-learn 的 TF-IDF 演算法從文本中提取前 20 個關鍵詞，
確保輸出關鍵詞列表無重複詞彙。

需求：2.2
"""

from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


# 最大關鍵詞數量上限
MAX_KEYWORDS: int = 20


class KeywordExtractor:
    """
    TF-IDF 關鍵詞提取器

    使用 scikit-learn TfidfVectorizer 對單一文本或語料庫提取關鍵詞。
    輸出關鍵詞列表長度 <= 20，且不含重複詞彙。
    """

    def __init__(self, max_keywords: int = MAX_KEYWORDS):
        """
        初始化關鍵詞提取器

        Args:
            max_keywords: 最大關鍵詞數量，預設 20
        """
        self._max_keywords = max_keywords

    def extract(self, text: str) -> list[str]:
        """
        從單一文本提取 TF-IDF 關鍵詞

        對單一文本使用 TF-IDF 計算詞彙重要性，
        回傳按 TF-IDF 分數降序排列的前 N 個關鍵詞。

        Args:
            text: 輸入文本

        Returns:
            關鍵詞列表（長度 <= 20，無重複）
        """
        if not text or not text.strip():
            return []

        # 使用字元 n-gram 支援中文（中文無空格分詞）
        # analyzer='char_wb' 對中文效果較好，但 'word' 對英文較佳
        # 此處使用 'word' 並搭配 token_pattern 支援中英文混合
        try:
            vectorizer = TfidfVectorizer(
                max_features=self._max_keywords,
                analyzer="word",
                token_pattern=r"(?u)\b\w+\b",  # 支援中英文詞彙
                sublinear_tf=True,              # 使用對數 TF 平滑
            )
            # 單一文本需包裝成列表
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
                # 確保無重複（TfidfVectorizer 本身不會重複，但防禦性檢查）
                if word not in seen:
                    keywords.append(word)
                    seen.add(word)
                if len(keywords) >= self._max_keywords:
                    break

            return keywords

        except ValueError:
            # 文本過短或無有效詞彙時回傳空列表
            return []

    def extract_from_corpus(self, texts: list[str]) -> list[list[str]]:
        """
        從語料庫中為每個文本提取 TF-IDF 關鍵詞

        使用整個語料庫計算 IDF，使關鍵詞更具區分性。

        Args:
            texts: 文本列表

        Returns:
            每個文本對應的關鍵詞列表
        """
        if not texts:
            return []

        # 過濾空文本
        valid_texts = [t if t and t.strip() else " " for t in texts]

        try:
            vectorizer = TfidfVectorizer(
                max_features=self._max_keywords * 2,  # 多取一些再篩選
                analyzer="word",
                token_pattern=r"(?u)\b\w+\b",
                sublinear_tf=True,
            )
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
