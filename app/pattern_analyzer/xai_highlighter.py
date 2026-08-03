"""
XAI 可解釋性高亮模組

對詐騙話術文本執行可解釋性分析，標記觸發各心理操控特徵的具體片段。
輸出每個觸發片段的字元位置、對應標籤與信心分數，供前端高亮渲染使用。
"""

import re
from dataclasses import dataclass

from app.pattern_analyzer.psych_classifier import (
    _TAG_PATTERNS,
)


@dataclass
class HighlightSpan:
    """單一高亮片段"""

    text: str
    """觸發的文字片段"""

    start: int
    """片段起始字元索引（含）"""

    end: int
    """片段結束字元索引（不含）"""

    tag: str
    """對應的心理操控特徵標籤"""

    score: float
    """信心分數（0.0 ~ 1.0），基於片段長度與匹配精確度計算"""


@dataclass
class XAIResult:
    """XAI 可解釋性分析結果"""

    text: str
    """原始輸入文本"""

    spans: list[HighlightSpan]
    """所有觸發片段列表，依 start 位置排序"""

    triggered_tags: list[str]
    """本文本觸發的所有心理特徵標籤（去重）"""

    coverage_ratio: float
    """高亮片段覆蓋率（高亮字元數 / 總字元數）"""


def _compute_score(match: re.Match, pattern_str: str) -> float:
    """
    計算匹配片段的信心分數

    基於匹配長度與 pattern 精確度（是否為精確詞彙 vs 寬鬆 regex）。
    分數範圍 0.5 ~ 1.0。

    Args:
        match: regex 匹配物件
        pattern_str: 原始 pattern 字串

    Returns:
        信心分數（float）
    """
    matched_len = len(match.group())
    # 精確詞彙（無特殊 regex 字元）給較高分
    is_exact = not any(c in pattern_str for c in r".*+?[](){}^$|\\")
    base = 0.85 if is_exact else 0.65
    # 匹配片段越長，分數微幅提升（最多 +0.1）
    length_bonus = min(matched_len / 50, 0.1)
    return round(min(base + length_bonus, 1.0), 3)


class XAIHighlighter:
    """
    XAI 可解釋性高亮器

    使用 psych_classifier 的 regex patterns 反查觸發片段，
    輸出每個片段的位置、標籤與信心分數。
    """

    def __init__(self) -> None:
        # 預編譯所有 pattern，保留原始字串以計算分數
        self._tag_patterns: dict[str, list[tuple[re.Pattern, str]]] = {}
        for tag, patterns in _TAG_PATTERNS.items():
            self._tag_patterns[tag] = [
                (re.compile(p, re.IGNORECASE | re.UNICODE), p)
                for p in patterns
            ]

    def highlight(self, text: str) -> XAIResult:
        """
        對文本執行 XAI 高亮分析

        Args:
            text: 詐騙話術文本

        Returns:
            XAIResult 包含所有觸發片段與統計資訊
        """
        if not text or not text.strip():
            return XAIResult(text=text, spans=[], triggered_tags=[], coverage_ratio=0.0)

        spans: list[HighlightSpan] = []
        triggered_tags: set[str] = set()

        for tag, compiled_patterns in self._tag_patterns.items():
            for pattern, pattern_str in compiled_patterns:
                for match in pattern.finditer(text):
                    triggered_tags.add(tag)
                    spans.append(HighlightSpan(
                        text=match.group(),
                        start=match.start(),
                        end=match.end(),
                        tag=tag,
                        score=_compute_score(match, pattern_str),
                    ))

        # 依 start 位置排序，start 相同時依 tag 排序
        spans.sort(key=lambda s: (s.start, s.tag))

        # 計算覆蓋率（合併重疊區間後計算）
        coverage_ratio = _compute_coverage(text, spans)

        return XAIResult(
            text=text,
            spans=spans,
            triggered_tags=sorted(triggered_tags),
            coverage_ratio=round(coverage_ratio, 4),
        )

    def highlight_batch(self, texts: list[str]) -> list[XAIResult]:
        """批次處理多個文本"""
        return [self.highlight(t) for t in texts]


def _compute_coverage(text: str, spans: list[HighlightSpan]) -> float:
    """計算高亮片段在文本中的覆蓋率（合併重疊區間）"""
    if not text or not spans:
        return 0.0

    # 合併重疊區間
    intervals = sorted((s.start, s.end) for s in spans)
    merged: list[tuple[int, int]] = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    covered = sum(e - s for s, e in merged)
    return covered / len(text)
