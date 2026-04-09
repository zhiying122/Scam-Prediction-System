"""
詐騙預測系統 — Streamlit 主儀表板

多頁面儀表板，提供以下功能：
  頁面 1：熱詞排行榜
  頁面 2：XAI 話術分析
  頁面 3：沙盤推演
  頁面 4：受害風險地圖

啟動指令：streamlit run app/dashboard/streamlit_app.py
"""

import streamlit as st
from datetime import datetime

# ── 頁面設定 ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="詐騙預測系統儀表板",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 側邊欄頁面選擇 ────────────────────────────────────────────────────────────
st.sidebar.title("🛡️ 詐騙預測系統")
st.sidebar.markdown("---")

PAGES = {
    "🔥 熱詞排行榜": "hotwords",
    "🔍 XAI 話術分析": "xai",
    "🧪 沙盤推演": "sandbox",
    "🗺️ 受害風險地圖": "risk_map",
}

selected_page = st.sidebar.radio("選擇頁面", list(PAGES.keys()))
page_key = PAGES[selected_page]

st.sidebar.markdown("---")
st.sidebar.caption(f"系統時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ── 快取管理器（全域共用）────────────────────────────────────────────────────
from app.dashboard.pages.cache import DashboardCache, format_cache_status

@st.cache_resource
def get_cache() -> DashboardCache:
    """取得全域快取管理器（Streamlit session 共用）"""
    return DashboardCache()

cache = get_cache()

# ── Mock 資料（後端不可用時的示範資料）──────────────────────────────────────

MOCK_KEYWORD_FREQ: dict[str, int] = {
    "轉帳": 320, "帳戶": 285, "凍結": 240, "警察": 210, "投資": 195,
    "獲利": 180, "緊急": 175, "銀行": 165, "客服": 150, "限時": 140,
    "免費": 130, "中獎": 125, "解除": 120, "驗證": 115, "個資": 110,
    "詐騙": 105, "保證": 98, "高報酬": 92, "官方": 88, "安全碼": 82,
}

MOCK_RISK_VECTORS: list[dict] = [
    {"scam_cluster_label": "假冒銀行客服", "risk_score": 0.85,
     "target_audience": "中老年族群", "region": "台北市",
     "high_risk_features": ["帳戶凍結話術", "緊急轉帳要求"]},
    {"scam_cluster_label": "投資詐騙", "risk_score": 0.78,
     "target_audience": "年輕族群", "region": "新北市",
     "high_risk_features": ["高報酬承諾", "保證獲利話術"]},
    {"scam_cluster_label": "假冒政府機關", "risk_score": 0.72,
     "target_audience": "中老年族群", "region": "台中市",
     "high_risk_features": ["官方身份偽裝", "法律威脅話術"]},
    {"scam_cluster_label": "購物詐騙", "risk_score": 0.55,
     "target_audience": "年輕族群", "region": "高雄市",
     "high_risk_features": ["假冒賣家", "預付款詐騙"]},
    {"scam_cluster_label": "愛情詐騙", "risk_score": 0.65,
     "target_audience": "一般民眾", "region": "桃園市",
     "high_risk_features": ["情感操控", "海外匯款要求"]},
]


def show_cache_warning(is_from_cache: bool, cached_at) -> None:
    """若使用快取資料，顯示警告橫幅"""
    status_msg = format_cache_status(is_from_cache, cached_at)
    if is_from_cache:
        st.warning(status_msg)
    else:
        st.success(status_msg)


# ══════════════════════════════════════════════════════════════════════════════
# 頁面 1：熱詞排行榜
# ══════════════════════════════════════════════════════════════════════════════
if page_key == "hotwords":
    st.title("🔥 熱詞排行榜")
    st.markdown("顯示近期詐騙話術中出現頻率最高的關鍵詞，每 24 小時自動更新。")

    from app.dashboard.pages.hotwords import compute_hotword_ranking, get_hotword_page_data

    def fetch_hotword_data():
        """從後端取得熱詞資料（示範：直接使用 mock 資料）"""
        return MOCK_KEYWORD_FREQ

    # 帶快取降級的資料載入
    data, is_from_cache, cached_at = cache.fetch_with_fallback(
        key="hotword_freq",
        fetch_fn=fetch_hotword_data,
    )
    show_cache_warning(is_from_cache, cached_at)

    # 計算排行榜
    page_data = get_hotword_page_data(data)
    ranking = page_data["ranking"]

    col1, col2, col3 = st.columns(3)
    col1.metric("關鍵詞總數", page_data["total_keywords"])
    col2.metric("顯示筆數", page_data["displayed_count"])
    col3.metric("最高頻詞", ranking[0] if ranking else "—")

    st.markdown("---")

    if ranking:
        # 建立圖表資料（保留頻率值以供顯示）
        chart_data = {word: data[word] for word in ranking if word in data}

        st.subheader("📊 熱詞頻率長條圖")
        import pandas as pd
        df = pd.DataFrame(
            {"關鍵詞": list(chart_data.keys()), "出現次數": list(chart_data.values())}
        ).set_index("關鍵詞")
        st.bar_chart(df)

        st.subheader("📋 排行榜明細")
        rank_df = pd.DataFrame(
            [{"排名": i + 1, "關鍵詞": word, "出現次數": data.get(word, 0)}
             for i, word in enumerate(ranking)]
        )
        st.dataframe(rank_df, use_container_width=True, hide_index=True)
    else:
        st.info("目前無熱詞資料。")


# ══════════════════════════════════════════════════════════════════════════════
# 頁面 2：XAI 話術分析
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "xai":
    st.title("🔍 XAI 話術分析")
    st.markdown("輸入詐騙話術文字，系統將高亮顯示觸發心理操控特徵的片段，並列出對應標籤。")

    from app.pattern_analyzer.xai_highlighter import XAIHighlighter

    # 標籤對應顏色（每個心理特徵使用不同背景色）
    TAG_COLORS: dict[str, str] = {
        "信任建立":   "#d4edda",   # 綠色
        "緊迫感製造": "#fff3cd",   # 黃色
        "情緒勒索":   "#f8d7da",   # 紅色
        "權威偽裝":   "#cce5ff",   # 藍色
        "利益誘導":   "#e2d9f3",   # 紫色
    }
    TAG_TEXT_COLORS: dict[str, str] = {
        "信任建立":   "#155724",
        "緊迫感製造": "#856404",
        "情緒勒索":   "#721c24",
        "權威偽裝":   "#004085",
        "利益誘導":   "#4a235a",
    }

    # 範例文字
    EXAMPLE_TEXT = (
        "您好，我是台灣銀行客服專員，您的帳戶出現異常交易，"
        "請立即撥打我們的官方電話，否則帳戶將在24小時內凍結。"
        "為了保護您的資金安全，請馬上提供驗證碼，我們的專業團隊會幫助您解決問題。"
    )

    input_text = st.text_area(
        "輸入話術文字",
        value=EXAMPLE_TEXT,
        height=150,
        placeholder="請輸入要分析的詐騙話術文字...",
    )

    if st.button("🔍 開始分析", type="primary"):
        if not input_text.strip():
            st.warning("請輸入文字後再進行分析。")
        else:
            highlighter = XAIHighlighter()
            result = highlighter.highlight(input_text)

            # ── 統計資訊 ──────────────────────────────────────────────────
            col1, col2, col3 = st.columns(3)
            col1.metric("觸發片段數", len(result.spans))
            col2.metric("觸發標籤數", len(result.triggered_tags))
            col3.metric("覆蓋率", f"{result.coverage_ratio:.1%}")

            st.markdown("---")

            # ── 高亮顯示 ──────────────────────────────────────────────────
            st.subheader("📝 高亮分析結果")

            if result.spans:
                # 建立 HTML 高亮文字
                html_parts: list[str] = []
                prev_end = 0
                for span in result.spans:
                    # 未高亮的部分
                    if span.start > prev_end:
                        plain = input_text[prev_end:span.start]
                        html_parts.append(plain.replace("\n", "<br>"))
                    # 高亮片段
                    bg = TAG_COLORS.get(span.tag, "#eeeeee")
                    fg = TAG_TEXT_COLORS.get(span.tag, "#333333")
                    html_parts.append(
                        f'<mark style="background-color:{bg};color:{fg};'
                        f'padding:2px 4px;border-radius:3px;font-weight:bold;" '
                        f'title="{span.tag}（信心：{span.score:.0%}）">'
                        f'{span.text}</mark>'
                    )
                    prev_end = span.end
                # 剩餘文字
                if prev_end < len(input_text):
                    html_parts.append(input_text[prev_end:].replace("\n", "<br>"))

                st.markdown(
                    f'<div style="line-height:2;font-size:1.05rem;padding:12px;'
                    f'border:1px solid #dee2e6;border-radius:6px;background:#fafafa;">'
                    f'{"".join(html_parts)}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.info("未偵測到心理操控特徵片段。")

            # ── 標籤圖例 ──────────────────────────────────────────────────
            st.markdown("---")
            st.subheader("🏷️ 顏色圖例")
            legend_cols = st.columns(len(TAG_COLORS))
            for col, (tag, bg) in zip(legend_cols, TAG_COLORS.items()):
                fg = TAG_TEXT_COLORS[tag]
                col.markdown(
                    f'<div style="background:{bg};color:{fg};padding:6px 10px;'
                    f'border-radius:4px;text-align:center;font-weight:bold;">{tag}</div>',
                    unsafe_allow_html=True,
                )

            # ── 觸發標籤列表 ──────────────────────────────────────────────
            st.markdown("---")
            st.subheader("📌 觸發的心理特徵標籤")
            if result.triggered_tags:
                for tag in result.triggered_tags:
                    bg = TAG_COLORS.get(tag, "#eeeeee")
                    fg = TAG_TEXT_COLORS.get(tag, "#333333")
                    # 計算該標籤的片段數與平均信心
                    tag_spans = [s for s in result.spans if s.tag == tag]
                    avg_score = sum(s.score for s in tag_spans) / len(tag_spans)
                    st.markdown(
                        f'<span style="background:{bg};color:{fg};padding:4px 10px;'
                        f'border-radius:12px;margin-right:8px;font-weight:bold;">'
                        f'{tag}</span> '
                        f'觸發 {len(tag_spans)} 個片段，平均信心 {avg_score:.0%}',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("本文字未觸發任何心理特徵標籤。")


# ══════════════════════════════════════════════════════════════════════════════
# 頁面 3：沙盤推演
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "sandbox":
    st.title("🧪 沙盤推演")
    st.markdown("設定詐騙情境參數，模擬預測可能出現的詐騙變種特徵與風險等級。")

    from app.dashboard.pages.sandbox import (
        SandboxParams, run_sandbox_simulation,
        VALID_SCENARIO_TYPES, VALID_TARGET_AUDIENCES,
    )

    with st.form("sandbox_form"):
        col1, col2 = st.columns(2)
        with col1:
            scenario_type = st.selectbox(
                "詐騙情境類型",
                sorted(VALID_SCENARIO_TYPES),
                index=0,
            )
            target_audience = st.selectbox(
                "目標受眾",
                sorted(VALID_TARGET_AUDIENCES),
                index=0,
            )
        with col2:
            risk_filter = st.selectbox(
                "風險等級篩選（可選）",
                ["不篩選", "高", "中", "低"],
                index=0,
            )
            time_window = st.slider(
                "分析時間視窗（天）",
                min_value=1, max_value=90, value=7,
            )

        submitted = st.form_submit_button("🚀 執行推演", type="primary")

    if submitted:
        def fetch_sandbox_result():
            params = SandboxParams(
                scenario_type=scenario_type,
                target_audience=target_audience,
                risk_level_filter=risk_filter if risk_filter != "不篩選" else None,
                time_window_days=time_window,
            )
            return run_sandbox_simulation(params, risk_vectors=MOCK_RISK_VECTORS)

        result, is_from_cache, cached_at = cache.fetch_with_fallback(
            key=f"sandbox_{scenario_type}_{target_audience}_{risk_filter}_{time_window}",
            fetch_fn=fetch_sandbox_result,
        )
        show_cache_warning(is_from_cache, cached_at)

        # ── 結果顯示 ──────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📊 推演結果")

        risk_color = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(result.predicted_risk_level, "⚪")
        col1, col2, col3 = st.columns(3)
        col1.metric("預測風險等級", f"{risk_color} {result.predicted_risk_level}")
        col2.metric("預測信心分數", f"{result.confidence_score:.0%}")
        col3.metric("識別特徵數", len(result.predicted_features))

        st.info(result.summary)

        if result.predicted_features:
            st.subheader("⚠️ 預測高風險特徵")
            for i, feature in enumerate(result.predicted_features, 1):
                st.markdown(f"**{i}.** {feature}")

        if result.related_cluster_labels:
            st.subheader("🔗 相關詐騙類群")
            st.write("、".join(result.related_cluster_labels))


# ══════════════════════════════════════════════════════════════════════════════
# 頁面 4：受害風險地圖
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "risk_map":
    st.title("🗺️ 受害風險地圖")
    st.markdown("依年齡層與地區維度呈現受害風險指數，資料來源為預測層輸出的風險向量。")

    from app.dashboard.pages.risk_map import build_risk_map, get_risk_map_summary, VALID_REGIONS, VALID_AGE_GROUPS
    import pandas as pd

    # 篩選選項
    with st.expander("🔧 篩選設定", expanded=False):
        selected_regions = st.multiselect(
            "選擇地區（留空顯示全部）",
            sorted(VALID_REGIONS),
            default=[],
        )
        selected_ages = st.multiselect(
            "選擇年齡層（留空顯示全部）",
            sorted(VALID_AGE_GROUPS),
            default=[],
        )

    def fetch_risk_map():
        regions = selected_regions if selected_regions else None
        ages = selected_ages if selected_ages else None
        return build_risk_map(MOCK_RISK_VECTORS, age_groups=ages, regions=regions)

    risk_map, is_from_cache, cached_at = cache.fetch_with_fallback(
        key=f"risk_map_{','.join(selected_regions)}_{','.join(selected_ages)}",
        fetch_fn=fetch_risk_map,
    )
    show_cache_warning(is_from_cache, cached_at)

    # ── 摘要指標 ──────────────────────────────────────────────────────────
    summary = get_risk_map_summary(risk_map)
    overall_icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(summary["overall_risk_level"], "⚪")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("整體風險等級", f"{overall_icon} {summary['overall_risk_level']}")
    col2.metric("🔴 高風險區域", summary["high_risk_count"])
    col3.metric("🟡 中風險區域", summary["medium_risk_count"])
    col4.metric("🟢 低風險區域", summary["low_risk_count"])

    if summary.get("highest_risk"):
        hr = summary["highest_risk"]
        st.error(
            f"⚠️ 最高風險：**{hr['age_group']}** × **{hr['region']}**"
            f"（風險指數 {hr['risk_index']:.2f}，主要詐騙類型：{hr['dominant_scam_type']}）"
        )

    st.markdown("---")

    # ── 風險地圖表格 ──────────────────────────────────────────────────────
    st.subheader("📋 風險指數明細表")

    if risk_map.entries:
        rows = []
        for entry in risk_map.entries:
            risk_icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(entry.risk_level, "⚪")
            rows.append({
                "年齡層": entry.age_group,
                "地區": entry.region,
                "風險指數": round(entry.risk_index, 4),
                "風險等級": f"{risk_icon} {entry.risk_level}",
                "相關案件數": entry.case_count,
                "主要詐騙類型": entry.dominant_scam_type,
            })

        df = pd.DataFrame(rows)
        # 依風險指數降序排列
        df = df.sort_values("風險指數", ascending=False).reset_index(drop=True)
        df.index += 1

        st.dataframe(df, use_container_width=True)
    else:
        st.info("目前無風險地圖資料。")
