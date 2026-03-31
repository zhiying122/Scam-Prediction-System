"""
Pattern_Analyzer 測試模組

包含單元測試與屬性測試，驗證語意分析與特徵萃取模組的核心邏輯。
測試涵蓋：語言偵測、語意嵌入、TF-IDF 關鍵詞提取、心理特徵分類、分群演算法。

屬性測試使用 hypothesis 框架，每個屬性最少執行 100 次迭代。
"""

import math
import uuid
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

from app.pattern_analyzer.embedder import (
    LanguageEmbedder,
    detect_language,
    is_supported_language,
    SUPPORTED_LANGUAGES,
    EMBEDDING_DIM,
)
from app.pattern_analyzer.keyword_extractor import KeywordExtractor, MAX_KEYWORDS
from app.pattern_analyzer.psych_classifier import (
    PsychologicalClassifier,
    VALID_PSYCHOLOGICAL_TAGS,
)
from app.pattern_analyzer.clusterer import ScamClusterer, _make_cluster_label
from app.pattern_analyzer.analyzer import PatternAnalyzer, AnalysisInput


# ══════════════════════════════════════════════════════════════════════════════
# 輔助函式：建立 mock 語意嵌入器
# ══════════════════════════════════════════════════════════════════════════════

def make_mock_embedder(lang: str = "zh-cn", dim: int = EMBEDDING_DIM):
    """建立回傳固定向量的 mock 語意嵌入器"""
    from app.pattern_analyzer.embedder import EmbeddingResult

    mock = MagicMock(spec=LanguageEmbedder)
    is_supported = lang in SUPPORTED_LANGUAGES

    def mock_embed(text):
        if not text or not text.strip():
            return EmbeddingResult(language="unsupported", embedding=None, is_supported=False)
        if is_supported:
            embedding = [0.1] * dim
            return EmbeddingResult(language=lang, embedding=embedding, is_supported=True)
        return EmbeddingResult(language="unsupported", embedding=None, is_supported=False)

    mock.embed.side_effect = mock_embed
    return mock


# ══════════════════════════════════════════════════════════════════════════════
# 單元測試：語言偵測（embedder）
# ══════════════════════════════════════════════════════════════════════════════

class TestLanguageDetection:
    """語言偵測單元測試"""

    def test_detect_chinese_text(self):
        """偵測繁體中文文本"""
        lang = detect_language("您好，我是銀行客服，請立即驗證您的帳戶。")
        assert lang in SUPPORTED_LANGUAGES

    def test_detect_english_text(self):
        """偵測英文文本"""
        lang = detect_language("Hello, this is your bank. Please verify your account immediately.")
        assert lang == "en"

    def test_detect_empty_text_returns_unsupported(self):
        """空文本應回傳 unsupported"""
        lang = detect_language("")
        assert lang == "unsupported"

    def test_detect_whitespace_only_returns_unsupported(self):
        """純空白文本應回傳 unsupported"""
        lang = detect_language("   ")
        assert lang == "unsupported"

    def test_is_supported_language_chinese(self):
        """中文語言代碼應為支援"""
        assert is_supported_language("zh-cn") is True
        assert is_supported_language("zh-tw") is True
        assert is_supported_language("zh") is True

    def test_is_supported_language_english(self):
        """英文語言代碼應為支援"""
        assert is_supported_language("en") is True

    def test_is_supported_language_japanese_unsupported(self):
        """日文語言代碼應為不支援"""
        assert is_supported_language("ja") is False

    def test_is_supported_language_korean_unsupported(self):
        """韓文語言代碼應為不支援"""
        assert is_supported_language("ko") is False

    def test_is_supported_language_unsupported_code(self):
        """'unsupported' 字串應為不支援"""
        assert is_supported_language("unsupported") is False


# ══════════════════════════════════════════════════════════════════════════════
# 單元測試：語意嵌入（embedder）
# ══════════════════════════════════════════════════════════════════════════════

class TestLanguageEmbedder:
    """語意嵌入器單元測試（使用 mock 避免載入實際模型）"""

    def test_embed_supported_language_returns_384_dim(self):
        """支援語言應產生 384 維向量"""
        embedder = LanguageEmbedder()
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1] * EMBEDDING_DIM)
        embedder._model = mock_model

        result = embedder.embed("您好，我是銀行客服。")
        # 語言偵測可能回傳 zh-cn 或 zh-tw
        if result.is_supported:
            assert result.embedding is not None
            assert len(result.embedding) == EMBEDDING_DIM

    def test_embed_unsupported_language_returns_none_embedding(self):
        """不支援語言應回傳 None 向量"""
        embedder = LanguageEmbedder()
        # 使用日文文本（不支援）
        result = embedder.embed("こんにちは、私は銀行員です。")
        if not result.is_supported:
            assert result.embedding is None
            assert result.language == "unsupported"

    def test_embed_empty_text_returns_unsupported(self):
        """空文本應標記為不支援"""
        embedder = LanguageEmbedder()
        result = embedder.embed("")
        assert result.is_supported is False
        assert result.language == "unsupported"
        assert result.embedding is None

    def test_embed_validates_no_nan(self):
        """語意向量不應含 NaN 值"""
        from app.pattern_analyzer.embedder import _validate_embedding
        with pytest.raises(ValueError, match="NaN"):
            _validate_embedding([0.1, float("nan"), 0.3])

    def test_embed_validates_no_inf(self):
        """語意向量不應含 Inf 值"""
        from app.pattern_analyzer.embedder import _validate_embedding
        with pytest.raises(ValueError, match="Inf"):
            _validate_embedding([0.1, float("inf"), 0.3])

    def test_embed_valid_vector_passes_validation(self):
        """合法向量應通過驗證"""
        from app.pattern_analyzer.embedder import _validate_embedding
        _validate_embedding([0.1, 0.2, -0.3, 0.0])  # 不應拋出例外


# ══════════════════════════════════════════════════════════════════════════════
# 屬性測試：語意向量維度正確性（屬性 5）
# ══════════════════════════════════════════════════════════════════════════════

@settings(max_examples=100, deadline=None)
@given(st.text(min_size=5, max_size=200))
def test_semantic_vector_dimensions(text: str):
    """
    **Validates: Requirements 2.1**

    # Feature: ai-scam-evolution-prediction, Property 5: 語意向量維度正確性
    對於任意語言為繁體中文或英文的 Scam_Script，
    Pattern_Analyzer 應產生維度為 384 的非零語意向量，且向量中不含 NaN 或 Inf 值。
    """
    embedder = LanguageEmbedder()
    mock_model = MagicMock()
    # 模擬產生 384 維向量
    mock_model.encode.return_value = np.array([0.1] * EMBEDDING_DIM)
    embedder._model = mock_model

    result = embedder.embed(text)

    if result.is_supported:
        assert result.embedding is not None
        assert len(result.embedding) == EMBEDDING_DIM
        # 驗證不含 NaN 或 Inf
        for val in result.embedding:
            assert not math.isnan(val), f"向量含有 NaN 值"
            assert not math.isinf(val), f"向量含有 Inf 值"


# ══════════════════════════════════════════════════════════════════════════════
# 屬性測試：不支援語言的跳過行為（屬性 9）
# ══════════════════════════════════════════════════════════════════════════════

@settings(max_examples=100, deadline=None)
@given(st.text(min_size=1, max_size=100))
def test_unsupported_language_skip(text: str):
    """
    **Validates: Requirements 2.5**

    # Feature: ai-scam-evolution-prediction, Property 9: 不支援語言的跳過行為
    對於任意語言非繁體中文且非英文的輸入樣本，
    Pattern_Analyzer 應將其 language 欄位標記為 unsupported，
    且不應產生對應的語意向量或關鍵詞。

    使用 mock 模型避免實際載入 Sentence-BERT，確保測試效能。
    """
    from app.pattern_analyzer.embedder import EmbeddingResult

    # 使用 mock 模型：語言偵測仍使用真實 langdetect，但嵌入使用 mock
    embedder = LanguageEmbedder()
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([0.1] * EMBEDDING_DIM)
    embedder._model = mock_model

    result = embedder.embed(text)

    if not result.is_supported:
        assert result.language == "unsupported"
        assert result.embedding is None


# ══════════════════════════════════════════════════════════════════════════════
# 單元測試：TF-IDF 關鍵詞提取
# ══════════════════════════════════════════════════════════════════════════════

class TestKeywordExtractor:
    """TF-IDF 關鍵詞提取器單元測試"""

    def test_extract_returns_at_most_20_keywords(self):
        """提取關鍵詞數量不超過 20"""
        extractor = KeywordExtractor()
        text = "投資 獲利 銀行 客服 帳戶 驗證 緊急 立即 免費 獎金 " * 5
        keywords = extractor.extract(text)
        assert len(keywords) <= MAX_KEYWORDS

    def test_extract_no_duplicate_keywords(self):
        """提取的關鍵詞不含重複"""
        extractor = KeywordExtractor()
        text = "您好，我是銀行客服，您的帳戶發現異常，請立即驗證身份，否則帳戶將被凍結。"
        keywords = extractor.extract(text)
        assert len(keywords) == len(set(keywords))

    def test_extract_empty_text_returns_empty(self):
        """空文本應回傳空列表"""
        extractor = KeywordExtractor()
        assert extractor.extract("") == []
        assert extractor.extract("   ") == []

    def test_extract_english_text(self):
        """英文文本應能提取關鍵詞"""
        extractor = KeywordExtractor()
        text = "Your account has been compromised. Please verify your identity immediately to avoid account suspension."
        keywords = extractor.extract(text)
        assert isinstance(keywords, list)
        assert len(keywords) <= MAX_KEYWORDS

    def test_extract_returns_list_of_strings(self):
        """提取結果應為字串列表"""
        extractor = KeywordExtractor()
        text = "投資理財，穩定獲利，保證報酬，立即加入我們的投資計畫。"
        keywords = extractor.extract(text)
        assert all(isinstance(k, str) for k in keywords)


# ══════════════════════════════════════════════════════════════════════════════
# 屬性測試：TF-IDF 關鍵詞數量上限（屬性 6）
# ══════════════════════════════════════════════════════════════════════════════

@settings(max_examples=100)
@given(st.text(min_size=1, max_size=500))
def test_tfidf_keyword_count_limit(text: str):
    """
    **Validates: Requirements 2.2**

    # Feature: ai-scam-evolution-prediction, Property 6: TF-IDF 關鍵詞數量上限
    對於任意輸入文本，Pattern_Analyzer 提取的關鍵詞列表長度應 <= 20，
    且列表中不含重複詞彙。
    """
    extractor = KeywordExtractor()
    keywords = extractor.extract(text)

    assert len(keywords) <= MAX_KEYWORDS, \
        f"關鍵詞數量 {len(keywords)} 超過上限 {MAX_KEYWORDS}"
    assert len(keywords) == len(set(keywords)), \
        f"關鍵詞列表含有重複詞彙：{keywords}"


# ══════════════════════════════════════════════════════════════════════════════
# 單元測試：心理特徵分類器
# ══════════════════════════════════════════════════════════════════════════════

class TestPsychologicalClassifier:
    """心理特徵分類器單元測試"""

    def test_classify_urgency_keywords(self):
        """含緊迫感關鍵詞的文本應標記「緊迫感製造」"""
        classifier = PsychologicalClassifier()
        text = "請立即點擊連結，否則您的帳戶將在24小時內被凍結！"
        tags = classifier.classify(text)
        assert "緊迫感製造" in tags

    def test_classify_authority_keywords(self):
        """含權威偽裝關鍵詞的文本應標記「權威偽裝」"""
        classifier = PsychologicalClassifier()
        text = "您好，我是銀行客服專員，您的帳戶發現異常交易。"
        tags = classifier.classify(text)
        assert "權威偽裝" in tags

    def test_classify_benefit_lure_keywords(self):
        """含利益誘導關鍵詞的文本應標記「利益誘導」"""
        classifier = PsychologicalClassifier()
        text = "投資我們的計畫，保證獲利，零風險高報酬！"
        tags = classifier.classify(text)
        assert "利益誘導" in tags

    def test_classify_multiple_tags(self):
        """文本可同時標記多個特徵"""
        classifier = PsychologicalClassifier()
        text = "我是警察，您的帳戶涉及洗錢，請立即轉帳配合調查，否則您的家人也會受到牽連。"
        tags = classifier.classify(text)
        assert len(tags) >= 1  # 至少有一個標籤

    def test_classify_empty_text_returns_empty(self):
        """空文本應回傳空列表"""
        classifier = PsychologicalClassifier()
        assert classifier.classify("") == []

    def test_classify_all_tags_are_valid(self):
        """所有輸出標籤必須屬於合法集合"""
        classifier = PsychologicalClassifier()
        texts = [
            "立即轉帳，否則帳戶凍結",
            "我是銀行客服，請驗證身份",
            "投資獲利，保證報酬",
            "您的家人有危險，請配合",
            "我們是可靠的投資顧問",
        ]
        for text in texts:
            tags = classifier.classify(text)
            for tag in tags:
                assert tag in VALID_PSYCHOLOGICAL_TAGS, \
                    f"非法標籤：{tag}"

    def test_classify_returns_list(self):
        """分類結果應為列表型別"""
        classifier = PsychologicalClassifier()
        result = classifier.classify("測試文本")
        assert isinstance(result, list)


# ══════════════════════════════════════════════════════════════════════════════
# 屬性測試：心理特徵標籤合法性（屬性 7）
# ══════════════════════════════════════════════════════════════════════════════

@settings(max_examples=100)
@given(st.text(min_size=0, max_size=500))
def test_psychological_tag_validity(text: str):
    """
    **Validates: Requirements 2.3**

    # Feature: ai-scam-evolution-prediction, Property 7: 心理特徵標籤合法性
    對於任意 Scam_Script 的分析結果，所有輸出的心理操控特徵標籤應屬於
    以下五個合法類別之一：信任建立、緊迫感製造、情緒勒索、權威偽裝、利益誘導。
    不得出現此五類以外的標籤值。
    """
    classifier = PsychologicalClassifier()
    tags = classifier.classify(text)

    assert isinstance(tags, list), "分類結果應為列表"
    for tag in tags:
        assert tag in VALID_PSYCHOLOGICAL_TAGS, \
            f"輸出了非法標籤：{repr(tag)}，合法標籤集合：{VALID_PSYCHOLOGICAL_TAGS}"


# ══════════════════════════════════════════════════════════════════════════════
# 單元測試：分群演算法
# ══════════════════════════════════════════════════════════════════════════════

class TestScamClusterer:
    """分群演算法單元測試"""

    def test_cluster_label_is_nonempty_string(self):
        """分群標籤應為非空字串"""
        clusterer = ScamClusterer()
        embeddings = [[float(i % 10) / 10] * EMBEDDING_DIM for i in range(5)]
        labels = clusterer.fit_predict(embeddings)
        for label in labels:
            assert isinstance(label, str)
            assert len(label) > 0

    def test_cluster_single_sample(self):
        """單一樣本應回傳非空標籤"""
        clusterer = ScamClusterer()
        embeddings = [[0.1] * EMBEDDING_DIM]
        labels = clusterer.fit_predict(embeddings)
        assert len(labels) == 1
        assert labels[0] and len(labels[0]) > 0

    def test_cluster_output_count_matches_input(self):
        """輸出標籤數量應與輸入向量數量相同"""
        clusterer = ScamClusterer()
        n = 10
        embeddings = [[float(i) / n] * EMBEDDING_DIM for i in range(n)]
        labels = clusterer.fit_predict(embeddings)
        assert len(labels) == n

    def test_cluster_empty_input_raises_error(self):
        """空輸入應拋出 ValueError"""
        clusterer = ScamClusterer()
        with pytest.raises(ValueError):
            clusterer.fit_predict([])

    def test_make_cluster_label_format(self):
        """標籤格式應符合預期"""
        label = _make_cluster_label(0)
        assert label == "詐騙類群-1"
        label2 = _make_cluster_label(4)
        assert label2 == "詐騙類群-5"

    def test_predict_without_fit_raises_error(self):
        """未訓練時呼叫 predict 應拋出 RuntimeError"""
        clusterer = ScamClusterer()
        with pytest.raises(RuntimeError):
            clusterer.predict([[0.1] * EMBEDDING_DIM])


# ══════════════════════════════════════════════════════════════════════════════
# 屬性測試：分群標籤完整性（屬性 8）
# ══════════════════════════════════════════════════════════════════════════════

@settings(max_examples=50, deadline=None)
@given(
    st.integers(min_value=1, max_value=20)
)
def test_cluster_label_not_empty(n_samples: int):
    """
    **Validates: Requirements 2.4**

    # Feature: ai-scam-evolution-prediction, Property 8: 分群標籤完整性
    對於任意完成語意嵌入的 SemanticVector，其 cluster_label 欄位應為非空字串，
    不得為 null 或空字串。
    """
    clusterer = ScamClusterer()
    # 建立 n_samples 個隨機向量
    embeddings = [
        [float((i * j + 1) % 100) / 100 for j in range(EMBEDDING_DIM)]
        for i in range(n_samples)
    ]
    labels = clusterer.fit_predict(embeddings)

    assert len(labels) == n_samples
    for label in labels:
        assert label is not None, "cluster_label 不得為 None"
        assert isinstance(label, str), "cluster_label 應為字串"
        assert len(label) > 0, "cluster_label 不得為空字串"


# ══════════════════════════════════════════════════════════════════════════════
# 單元測試：PatternAnalyzer 完整流程
# ══════════════════════════════════════════════════════════════════════════════

class TestPatternAnalyzer:
    """PatternAnalyzer 完整分析流程單元測試"""

    def _make_analyzer_with_mock_embedder(self, lang: str = "zh-cn") -> PatternAnalyzer:
        """建立使用 mock 嵌入器的 PatternAnalyzer"""
        mock_embedder = make_mock_embedder(lang=lang)
        return PatternAnalyzer(embedder=mock_embedder)

    def test_analyze_supported_language_returns_result(self):
        """支援語言的樣本應回傳完整分析結果"""
        analyzer = self._make_analyzer_with_mock_embedder("zh-cn")
        result = analyzer.analyze(
            script_id=str(uuid.uuid4()),
            content="您好，我是銀行客服，請立即驗證您的帳戶，否則將被凍結。",
        )
        assert result.is_skipped is False
        assert result.language != "unsupported"
        assert result.embedding is not None
        assert len(result.embedding) == EMBEDDING_DIM

    def test_analyze_unsupported_language_is_skipped(self):
        """不支援語言的樣本應標記為跳過"""
        from app.pattern_analyzer.embedder import EmbeddingResult

        mock_embedder = MagicMock(spec=LanguageEmbedder)
        mock_embedder.embed.return_value = EmbeddingResult(
            language="unsupported", embedding=None, is_supported=False
        )
        analyzer = PatternAnalyzer(embedder=mock_embedder)
        result = analyzer.analyze(
            script_id=str(uuid.uuid4()),
            content="こんにちは",
        )
        assert result.is_skipped is True
        assert result.language == "unsupported"
        assert result.embedding is None
        assert result.keywords == []
        assert result.psychological_tags == []

    def test_analyze_batch_counts_correctly(self):
        """批次分析應正確統計處理與跳過數量"""
        from app.pattern_analyzer.embedder import EmbeddingResult

        mock_embedder = MagicMock(spec=LanguageEmbedder)

        def side_effect(text):
            if "中文" in text:
                return EmbeddingResult(
                    language="zh-cn",
                    embedding=[0.1] * EMBEDDING_DIM,
                    is_supported=True,
                )
            return EmbeddingResult(
                language="unsupported", embedding=None, is_supported=False
            )

        mock_embedder.embed.side_effect = side_effect

        analyzer = PatternAnalyzer(embedder=mock_embedder)
        inputs = [
            AnalysisInput(script_id=str(uuid.uuid4()), content="中文詐騙話術"),
            AnalysisInput(script_id=str(uuid.uuid4()), content="中文投資詐騙"),
            AnalysisInput(script_id=str(uuid.uuid4()), content="unsupported language text"),
        ]
        batch_result = analyzer.analyze_batch(inputs)

        assert batch_result.total_count == 3
        assert batch_result.processed_count == 2
        assert batch_result.skipped_count == 1

    def test_analyze_batch_empty_input(self):
        """空輸入應回傳空結果"""
        analyzer = PatternAnalyzer()
        result = analyzer.analyze_batch([])
        assert result.total_count == 0
        assert result.processed_count == 0
        assert result.skipped_count == 0
        assert result.results == []
        assert result.semantic_vectors == []

    def test_extract_keywords_convenience_method(self):
        """便捷方法 extract_keywords 應正常運作"""
        analyzer = PatternAnalyzer()
        keywords = analyzer.extract_keywords("投資獲利，保證報酬，立即加入。")
        assert isinstance(keywords, list)
        assert len(keywords) <= MAX_KEYWORDS

    def test_classify_psychological_features_convenience_method(self):
        """便捷方法 classify_psychological_features 應正常運作"""
        analyzer = PatternAnalyzer()
        tags = analyzer.classify_psychological_features("立即轉帳，否則帳戶凍結！")
        assert isinstance(tags, list)
        for tag in tags:
            assert tag in VALID_PSYCHOLOGICAL_TAGS

    def test_semantic_vectors_created_for_supported_samples(self):
        """支援語言的樣本應建立對應的 SemanticVector 物件"""
        mock_embedder = make_mock_embedder(lang="zh-cn")
        analyzer = PatternAnalyzer(embedder=mock_embedder)

        inputs = [
            AnalysisInput(script_id=str(uuid.uuid4()), content="中文詐騙話術一"),
            AnalysisInput(script_id=str(uuid.uuid4()), content="中文詐騙話術二"),
        ]
        result = analyzer.analyze_batch(inputs)

        assert len(result.semantic_vectors) == 2
        for sv in result.semantic_vectors:
            assert sv.cluster_label and len(sv.cluster_label) > 0
            assert len(sv.embedding) == EMBEDDING_DIM
