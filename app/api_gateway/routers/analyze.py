"""
XAI 可解釋性分析路由 & 完整分析路由

提供 POST /v1/analyze/highlight 端點，
對詐騙話術文本執行 XAI 高亮分析，回傳觸發片段位置與心理特徵標籤。

提供 POST /v1/analyze/batch 端點，
對詐騙話術文本列表執行完整分析流程（關鍵詞、心理標籤、分群標籤），
不暴露原始嵌入向量。
"""

import uuid

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.pattern_analyzer.analyzer import PatternAnalyzer, AnalysisInput
from app.pattern_analyzer.xai_highlighter import XAIHighlighter

router = APIRouter(prefix="/analyze", tags=["XAI 可解釋性分析"])

_highlighter = XAIHighlighter()
_pattern_analyzer = PatternAnalyzer()


# ── 請求 / 回應模型 ───────────────────────────────────────────────────────────

class HighlightRequest(BaseModel):
    text: str = Field(..., min_length=1, description="詐騙話術文本")


class SpanOut(BaseModel):
    text: str
    start: int
    end: int
    tag: str
    score: float


class HighlightResponse(BaseModel):
    text: str
    spans: list[SpanOut]
    triggered_tags: list[str]
    coverage_ratio: float


class BatchHighlightRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=100)


class BatchHighlightResponse(BaseModel):
    results: list[HighlightResponse]
    total: int


class BatchAnalyzeRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=100, description="詐騙話術文本列表")


class AnalysisResultOut(BaseModel):
    script_id: str
    language: str
    is_skipped: bool
    keywords: list[str]
    psychological_tags: list[str]
    cluster_label: str


class BatchAnalyzeResponse(BaseModel):
    results: list[AnalysisResultOut]
    total_count: int
    processed_count: int
    skipped_count: int


# ── 端點 ──────────────────────────────────────────────────────────────────────

@router.post(
    "/highlight",
    response_model=HighlightResponse,
    status_code=status.HTTP_200_OK,
    summary="單一文本 XAI 高亮分析",
)
def highlight_text(body: HighlightRequest) -> HighlightResponse:
    """
    對單一詐騙話術文本執行 XAI 高亮分析。

    回傳每個觸發片段的字元位置、心理特徵標籤與信心分數，
    供前端高亮渲染使用。
    """
    result = _highlighter.highlight(body.text)
    return HighlightResponse(
        text=result.text,
        spans=[
            SpanOut(text=s.text, start=s.start, end=s.end, tag=s.tag, score=s.score)
            for s in result.spans
        ],
        triggered_tags=result.triggered_tags,
        coverage_ratio=result.coverage_ratio,
    )


@router.post(
    "/highlight/batch",
    response_model=BatchHighlightResponse,
    status_code=status.HTTP_200_OK,
    summary="批次文本 XAI 高亮分析",
)
def highlight_batch(body: BatchHighlightRequest) -> BatchHighlightResponse:
    """批次對多個文本執行 XAI 高亮分析（最多 100 筆）。"""
    results = _highlighter.highlight_batch(body.texts)
    return BatchHighlightResponse(
        results=[
            HighlightResponse(
                text=r.text,
                spans=[
                    SpanOut(text=s.text, start=s.start, end=s.end, tag=s.tag, score=s.score)
                    for s in r.spans
                ],
                triggered_tags=r.triggered_tags,
                coverage_ratio=r.coverage_ratio,
            )
            for r in results
        ],
        total=len(results),
    )


@router.post(
    "/batch",
    response_model=BatchAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="批次完整分析",
)
def analyze_batch(body: BatchAnalyzeRequest) -> BatchAnalyzeResponse:
    """
    對多個詐騙話術文本執行完整分析流程（最多 100 筆）。

    觸發 PatternAnalyzer.analyze_batch()，回傳關鍵詞、心理標籤、分群標籤。
    不暴露原始 384 維嵌入向量。
    """
    inputs = [
        AnalysisInput(script_id=str(uuid.uuid4()), content=text)
        for text in body.texts
    ]
    batch_result = _pattern_analyzer.analyze_batch(inputs)
    return BatchAnalyzeResponse(
        results=[
            AnalysisResultOut(
                script_id=r.script_id,
                language=r.language,
                is_skipped=r.is_skipped,
                keywords=r.keywords,
                psychological_tags=r.psychological_tags,
                cluster_label=r.cluster_label,
            )
            for r in batch_result.results
        ],
        total_count=batch_result.total_count,
        processed_count=batch_result.processed_count,
        skipped_count=batch_result.skipped_count,
    )
