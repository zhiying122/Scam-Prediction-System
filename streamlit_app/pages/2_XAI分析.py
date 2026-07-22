"""XAI 可解釋性分析頁面"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import streamlit.components.v1 as components

from app.pattern_analyzer.xai_highlighter import XAIHighlighter
from streamlit_app.utils.mock_data import SAMPLE_SCRIPTS

st.set_page_config(page_title="XAI 分析", page_icon="🔍", layout="wide")
st.title("🔍 XAI 可解釋性分析")
st.caption("高亮顯示詐騙話術中觸發心理操控特徵的具體片段")

# ── 標籤顏色對應 ──────────────────────────────────────────────────────────────
TAG_COLORS = {
    "信任建立": "#d4edda",
    "緊迫感製造": "#fff3cd",
    "情緒勒索":   "#f8d7da",
    "權威偽裝":   "#cce5ff",
    "利益誘導":   "#e2d9f3",
}
TAG_TEXT_COLORS = {
    "信任建立": "#155724",
    "緊迫感製造": "#856404",
    "情緒勒索":   "#721c24",
    "權威偽裝":   "#004085",
    "利益誘導":   "#4a235a",
}

highlighter = XAIHighlighter()

# ── 輸入區 ────────────────────────────────────────────────────────────────────
st.subheader("輸入話術文本")

col_input, col_sample = st.columns([3, 1])
with col_sample:
    st.markdown("**快速載入範例**")
    for i, script in enumerate(SAMPLE_SCRIPTS):
        if st.button(f"範例 {i+1}", key=f"sample_{i}", use_container_width=True):
            st.session_state["xai_input"] = script

with col_input:
    text_input = st.text_area(
        "請輸入詐騙話術文本",
        value=st.session_state.get("xai_input", SAMPLE_SCRIPTS[0]),
        height=120,
        key="xai_textarea",
        label_visibility="collapsed",
    )

analyze_btn = st.button("🔍 開始分析", type="primary", use_container_width=False)

# ── 分析結果 ──────────────────────────────────────────────────────────────────
if analyze_btn or text_input:
    result = highlighter.highlight(text_input)

    st.divider()
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("高亮顯示結果")

        # 建立 HTML 高亮文本
        if not result.spans:
            st.info("未偵測到心理操控特徵片段")
            st.write(text_input)
        else:
            # 合併重疊片段，逐字元建立 HTML
            html_parts = []
            prev_end = 0
            # 去重：同一位置只保留第一個 span
            seen_positions = set()
            unique_spans = []
            for s in result.spans:
                key = (s.start, s.end)
                if key not in seen_positions:
                    seen_positions.add(key)
                    unique_spans.append(s)

            for span in unique_spans:
                # 未高亮的文字
                if span.start > prev_end:
                    html_parts.append(text_input[prev_end:span.start])
                # 高亮片段
                color = TAG_COLORS.get(span.tag, "#ddd")
                text_color = TAG_TEXT_COLORS.get(span.tag, "#333")
                html_parts.append(
                    f'<mark style="background:{color};color:{text_color};'
                    f'padding:2px 4px;border-radius:3px;font-weight:600;" '
                    f'title="{span.tag}（信心分數：{span.score}）">'
                    f'{text_input[span.start:span.end]}</mark>'
                )
                prev_end = max(prev_end, span.end)

            # 剩餘文字
            if prev_end < len(text_input):
                html_parts.append(text_input[prev_end:])

            html_content = (
                '<div style="font-size:1.1rem;line-height:2;padding:12px;color:#1a2332;'
                'background:#fafafa;border:1px solid #dee2e6;border-radius:8px;">'
                + "".join(html_parts) + "</div>"
            )
            components.html(html_content, height=180, scrolling=True)

        # 圖例
        st.markdown("**圖例**")
        legend_cols = st.columns(len(TAG_COLORS))
        for col, (tag, color) in zip(legend_cols, TAG_COLORS.items()):
            text_c = TAG_TEXT_COLORS[tag]
            col.markdown(
                f'<span style="background:{color};color:{text_c};'
                f'padding:3px 8px;border-radius:4px;font-size:0.85rem;">{tag}</span>',
                unsafe_allow_html=True,
            )

    with col_right:
        st.subheader("分析摘要")

        # 觸發標籤
        if result.triggered_tags:
            st.markdown("**偵測到的心理操控特徵**")
            for tag in result.triggered_tags:
                color = TAG_COLORS.get(tag, "#ddd")
                text_c = TAG_TEXT_COLORS.get(tag, "#333")
                st.markdown(
                    f'<span style="background:{color};color:{text_c};'
                    f'padding:4px 10px;border-radius:4px;margin:2px;display:inline-block;">{tag}</span>',
                    unsafe_allow_html=True,
                )
        else:
            st.success("未偵測到心理操控特徵")

        st.divider()

        # 統計數字
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("觸發片段數", len(result.spans))
        col_m2.metric("覆蓋率", f"{result.coverage_ratio:.1%}")

        st.divider()

        # 片段明細
        if result.spans:
            st.markdown("**觸發片段明細**")
            import pandas as pd
            df_spans = pd.DataFrame([
                {
                    "片段": s.text,
                    "標籤": s.tag,
                    "信心分數": f"{s.score:.2f}",
                    "位置": f"{s.start}-{s.end}",
                }
                for s in result.spans
            ])
            st.dataframe(df_spans, use_container_width=True, hide_index=True)
