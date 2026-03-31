"""
Pattern_Analyzer 完整分析流程串接模組

串接語言偵測 → 語意嵌入 → TF-IDF 關鍵詞提取 → 心理特徵分類 → 分群演算法，
對 ScamScript 執行完整的語意分析與特徵萃取。

需求：2.1、2.2、2.3、2.4
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.pattern_analyzer.embedder import LanguageEmbedder, EMBEDDING_DIM
from app.pattern_analyzer.keyword_extractor import KeywordExtractor
from app.pattern_analyzer.psych_classifier import PsychologicalClassifier
from app.pattern_analyzer.clusterer import ScamClusterer
from app.models.semantic_vector import SemanticVector


@dataclass
class AnalysisInput:
    """
    分析輸入資料

    包含 ScamScript 的 ID 與文本內容。
    """

    script_id: str
    """對應的 ScamScript UUID"""

    content: str
    """詐騙話術文本內容"""


@dataclass
class AnalysisResult:
    """
    單一樣本的分析結果

    包含語言偵測、語意向量、關鍵詞、心理特徵標籤等資訊。
    若語言不支援，embedding 與 keywords 為空，is_skipped 為 True。
    """

    script_id: str
    """對應的 ScamScript UUID"""

    language: str
    """偵測到的語言代碼，不支援時為 'unsupported'"""

    is_skipped: bool
    """是否因語言不支援而跳過分析"""

    embedding: Optional[list[float]]
    """384 維語意向量，語言不支援時為 None"""

    keywords: list[str]
    """TF-IDF 提取的前 20 個關鍵詞，語言不支援時為空列表"""

    psychological_tags: list[str]
    """心理操控特徵標籤列表，語言不支援時為空列表"""

    cluster_label: str
    """分群標籤，語言不支援時為空字串"""


@dataclass
class BatchAnalysisResult:
    """
    批次分析結果

    包含所有樣本的分析結果，以及統計資訊。
    """

    results: list[AnalysisResult]
    """每個樣本的分析結果"""

    semantic_vectors: list[SemanticVector]
    """成功分析的樣本對應的 SemanticVector 物件"""

    total_count: int
    """輸入樣本總數"""

    processed_count: int
    """成功處理（語言支援）的樣本數"""

    skipped_count: int
    """因語言不支援而跳過的樣本數"""


class PatternAnalyzer:
    """
    Pattern_Analyzer 完整分析流程

    串接語言偵測 → 語意嵌入 → TF-IDF 關鍵詞提取 → 心理特徵分類 → 分群演算法，
    對 ScamScript 執行完整的語意分析與特徵萃取。
    """

    def __init__(
        self,
        embedder: Optional[LanguageEmbedder] = None,
        keyword_extractor: Optional[KeywordExtractor] = None,
        psych_classifier: Optional[PsychologicalClassifier] = None,
        clusterer: Optional[ScamClusterer] = None,
    ):
        """
        初始化 Pattern_Analyzer

        支援依賴注入，方便測試時替換各子模組。

        Args:
            embedder: 語言偵測與語意嵌入器（預設自動建立）
            keyword_extractor: TF-IDF 關鍵詞提取器（預設自動建立）
            psych_classifier: 心理特徵分類器（預設自動建立）
            clusterer: 分群器（預設自動建立）
        """
        self._embedder = embedder or LanguageEmbedder()
        self._keyword_extractor = keyword_extractor or KeywordExtractor()
        self._psych_classifier = psych_classifier or PsychologicalClassifier()
        self._clusterer = clusterer or ScamClusterer()

    def analyze(self, script_id: str, content: str) -> AnalysisResult:
        """
        對單一 ScamScript 執行完整分析流程

        流程：語言偵測 → 嵌入 → 關鍵詞 → 心理特徵 → 分群（單一樣本）

        Args:
            script_id: ScamScript UUID
            content: 詐騙話術文本

        Returns:
            AnalysisResult 包含完整分析結果
        """
        # 步驟 1：語言偵測與語意嵌入
        embedding_result = self._embedder.embed(content)

        # 若語言不支援，標記並跳過後續分析
        if not embedding_result.is_supported:
            return AnalysisResult(
                script_id=script_id,
                language="unsupported",
                is_skipped=True,
                embedding=None,
                keywords=[],
                psychological_tags=[],
                cluster_label="",
            )

        # 步驟 2：TF-IDF 關鍵詞提取
        keywords = self._keyword_extractor.extract(content)

        # 步驟 3：心理特徵分類
        psych_tags = self._psych_classifier.classify(content)

        # 步驟 4：單一樣本分群（使用預設標籤）
        cluster_label = "詐騙類群-1"

        return AnalysisResult(
            script_id=script_id,
            language=embedding_result.language,
            is_skipped=False,
            embedding=embedding_result.embedding,
            keywords=keywords,
            psychological_tags=psych_tags,
            cluster_label=cluster_label,
        )

    def analyze_batch(self, inputs: list[AnalysisInput]) -> BatchAnalysisResult:
        """
        批次分析多個 ScamScript

        對所有支援語言的樣本執行完整分析流程，
        並使用批次分群演算法歸類所有向量。

        Args:
            inputs: AnalysisInput 列表

        Returns:
            BatchAnalysisResult 包含所有樣本的分析結果
        """
        if not inputs:
            return BatchAnalysisResult(
                results=[],
                semantic_vectors=[],
                total_count=0,
                processed_count=0,
                skipped_count=0,
            )

        # 步驟 1：語言偵測與語意嵌入（批次）
        embedding_results = [
            self._embedder.embed(inp.content) for inp in inputs
        ]

        # 分離支援與不支援的樣本
        supported_indices = [
            i for i, er in enumerate(embedding_results) if er.is_supported
        ]
        unsupported_indices = [
            i for i, er in enumerate(embedding_results) if not er.is_supported
        ]

        # 步驟 2 & 3：對支援語言的樣本提取關鍵詞與心理特徵
        partial_results: dict[int, dict] = {}

        for i in supported_indices:
            content = inputs[i].content
            keywords = self._keyword_extractor.extract(content)
            psych_tags = self._psych_classifier.classify(content)
            partial_results[i] = {
                "keywords": keywords,
                "psych_tags": psych_tags,
                "embedding": embedding_results[i].embedding,
                "language": embedding_results[i].language,
            }

        # 步驟 4：批次分群（僅對支援語言的樣本）
        cluster_labels: dict[int, str] = {}
        if supported_indices:
            embeddings = [partial_results[i]["embedding"] for i in supported_indices]
            if len(embeddings) == 1:
                # 單一樣本直接指派預設標籤
                cluster_labels[supported_indices[0]] = "詐騙類群-1"
            else:
                labels = self._clusterer.fit_predict(embeddings)
                for idx, label in zip(supported_indices, labels):
                    cluster_labels[idx] = label

        # 組合最終結果
        results = []
        for i, inp in enumerate(inputs):
            if i in unsupported_indices:
                results.append(AnalysisResult(
                    script_id=inp.script_id,
                    language="unsupported",
                    is_skipped=True,
                    embedding=None,
                    keywords=[],
                    psychological_tags=[],
                    cluster_label="",
                ))
            else:
                data = partial_results[i]
                results.append(AnalysisResult(
                    script_id=inp.script_id,
                    language=data["language"],
                    is_skipped=False,
                    embedding=data["embedding"],
                    keywords=data["keywords"],
                    psychological_tags=data["psych_tags"],
                    cluster_label=cluster_labels.get(i, "詐騙類群-1"),
                ))

        # 建立 SemanticVector 物件（僅支援語言的樣本）
        now = datetime.now(timezone.utc)
        semantic_vectors = []
        for result in results:
            if not result.is_skipped and result.embedding is not None:
                sv = SemanticVector(
                    id=str(uuid.uuid4()),
                    script_id=result.script_id,
                    embedding=result.embedding,
                    top_keywords=result.keywords,
                    cluster_label=result.cluster_label,
                    psychological_tags=result.psychological_tags,
                    created_at=now,
                )
                semantic_vectors.append(sv)

        return BatchAnalysisResult(
            results=results,
            semantic_vectors=semantic_vectors,
            total_count=len(inputs),
            processed_count=len(supported_indices),
            skipped_count=len(unsupported_indices),
        )

    def extract_keywords(self, text: str) -> list[str]:
        """
        提取文本的 TF-IDF 關鍵詞（便捷方法）

        Args:
            text: 輸入文本

        Returns:
            關鍵詞列表（長度 <= 20，無重複）
        """
        return self._keyword_extractor.extract(text)

    def classify_psychological_features(self, text: str) -> list[str]:
        """
        識別文本的心理操控特徵標籤（便捷方法）

        Args:
            text: 輸入文本

        Returns:
            心理特徵標籤列表（均屬合法集合）
        """
        return self._psych_classifier.classify(text)
