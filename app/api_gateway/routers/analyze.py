"""
XAI 可解釋性分析路由

提供 POST /v1/analyze/highlight 端點，
對詐騙話術文本執行 XAI 高亮分析，回傳觸發片段位置與心理特徵標籤。
"""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.pattern_analyzer.xai_highlighter import XAIHighlighter

router = APIRouter(prefix="/analyze", tags=["XAI 可解釋性分析"])

_highlighter = XAIHighlighter()


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
