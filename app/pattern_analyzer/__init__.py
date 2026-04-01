"""
語意分析與特徵萃取模組套件

提供 Pattern_Analyzer 的完整分析流程，包含：
- 語言偵測與 Sentence-BERT 語意嵌入（embedder）
- TF-IDF 關鍵詞提取（keyword_extractor）
- 心理特徵分類器（psych_classifier）
- 分群演算法（clusterer）
- 完整分析流程串接（analyzer）
"""

from app.pattern_analyzer.analyzer import PatternAnalyzer, AnalysisInput, AnalysisResult, BatchAnalysisResult
from app.pattern_analyzer.embedder import LanguageEmbedder, EmbeddingResult, detect_language, is_supported_language
from app.pattern_analyzer.keyword_extractor import KeywordExtractor
from app.pattern_analyzer.psych_classifier import PsychologicalClassifier, VALID_PSYCHOLOGICAL_TAGS
from app.pattern_analyzer.clusterer import ScamClusterer
from app.pattern_analyzer.xai_highlighter import XAIHighlighter, HighlightSpan, XAIResult

__all__ = [
    "PatternAnalyzer",
    "AnalysisInput",
    "AnalysisResult",
    "BatchAnalysisResult",
    "LanguageEmbedder",
    "EmbeddingResult",
    "detect_language",
    "is_supported_language",
    "KeywordExtractor",
    "PsychologicalClassifier",
    "VALID_PSYCHOLOGICAL_TAGS",
    "ScamClusterer",
    "XAIHighlighter",
    "HighlightSpan",
    "XAIResult",
]
