"""
語言偵測與 Sentence-BERT 語意嵌入模組

負責偵測輸入文本的語言，並使用 paraphrase-multilingual-MiniLM-L12-v2
模型對中文或英文樣本產生 384 維語意向量。

需求：2.1、2.5
"""

import math
from dataclasses import dataclass
from typing import Optional

from langdetect import detect, LangDetectException


# 支援的語言代碼集合（中文系列與英文）
SUPPORTED_LANGUAGES: frozenset[str] = frozenset({
    "zh-cn", "zh-tw", "zh",  # 中文（簡體、繁體、通用）
    "en",                     # 英文
})

# 語意向量維度（MiniLM 模型固定輸出）
EMBEDDING_DIM: int = 384


@dataclass
class EmbeddingResult:
    """
    語意嵌入結果

    包含語言偵測結果與語意向量（若語言不支援則向量為 None）。
    """

    language: str
    """偵測到的語言代碼，不支援時為 'unsupported'"""

    embedding: Optional[list[float]]
    """384 維語意向量，語言不支援時為 None"""

    is_supported: bool
    """是否為支援的語言（中文或英文）"""


def detect_language(text: str) -> str:
    """
    偵測輸入文本的語言

    使用 langdetect 函式庫偵測語言代碼。
    若偵測失敗或語言不支援，回傳 'unsupported'。

    Args:
        text: 輸入文本

    Returns:
        語言代碼字串（如 'zh-cn'、'en'）或 'unsupported'
    """
    if not text or not text.strip():
        return "unsupported"

    try:
        lang = detect(text)
        return lang
    except LangDetectException:
        return "unsupported"


def is_supported_language(lang_code: str) -> bool:
    """
    判斷語言代碼是否為支援的語言（中文或英文）

    Args:
        lang_code: 語言代碼字串

    Returns:
        True 表示支援，False 表示不支援
    """
    return lang_code in SUPPORTED_LANGUAGES


def _validate_embedding(embedding: list[float]) -> None:
    """
    驗證語意向量不含 NaN 或 Inf 值

    Args:
        embedding: 語意向量列表

    Raises:
        ValueError: 若向量含有 NaN 或 Inf 值
    """
    for i, val in enumerate(embedding):
        if math.isnan(val):
            raise ValueError(f"語意向量第 {i} 維含有 NaN 值")
        if math.isinf(val):
            raise ValueError(f"語意向量第 {i} 維含有 Inf 值")


class LanguageEmbedder:
    """
    語言偵測與語意嵌入器

    整合語言偵測與 Sentence-BERT 語意嵌入功能。
    對支援語言（中文/英文）的文本產生 384 維語意向量；
    對不支援語言的文本標記為 'unsupported' 並跳過嵌入。
    """

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        初始化語意嵌入器

        Args:
            model_name: Sentence-BERT 模型名稱，預設使用多語言 MiniLM 模型
        """
        self._model_name = model_name
        self._model = None  # 延遲載入，避免初始化時耗費大量時間

    def _load_model(self):
        """
        延遲載入 Sentence-BERT 模型

        首次呼叫時才載入模型，後續呼叫直接使用已載入的模型。
        """
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed(self, text: str) -> EmbeddingResult:
        """
        對輸入文本執行語言偵測與語意嵌入

        若語言不支援，回傳 language='unsupported' 且 embedding=None。
        若語言支援，產生 384 維語意向量並驗證不含 NaN/Inf。

        Args:
            text: 輸入文本

        Returns:
            EmbeddingResult 包含語言代碼與語意向量

        Raises:
            ValueError: 若產生的向量含有 NaN 或 Inf 值
        """
        lang = detect_language(text)

        if not is_supported_language(lang):
            return EmbeddingResult(
                language="unsupported",
                embedding=None,
                is_supported=False,
            )

        model = self._load_model()
        raw_embedding = model.encode(text, convert_to_numpy=True)
        embedding = raw_embedding.tolist()

        _validate_embedding(embedding)

        return EmbeddingResult(
            language=lang,
            embedding=embedding,
            is_supported=True,
        )

    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """
        批次處理多個文本的語言偵測與語意嵌入

        Args:
            texts: 輸入文本列表

        Returns:
            EmbeddingResult 列表，順序與輸入對應
        """
        return [self.embed(text) for text in texts]
