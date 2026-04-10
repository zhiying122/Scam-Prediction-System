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
from dotenv import load_dotenv

# 載入 .env 檔案（必須在所有 os.environ 讀取之前）
load_dotenv()

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
    "🏠 系統總覽": "overview",
    "🤖 LLM 話術生成": "llm_demo",
    "🔍 XAI 話術分析": "xai",
    "🔥 熱詞排行榜": "hotwords",
    "🧪 沙盤推演": "sandbox",
    "🗺️ 受害風險地圖": "risk_map",
    "📊 模型準確率評估": "evaluation",
}

selected_page = st.sidebar.radio("選擇頁面", list(PAGES.keys()))
page_key = PAGES[selected_page]

st.sidebar.markdown("---")
st.sidebar.caption(f"系統時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ── LLM 設定狀態（從環境變數讀取，不在前端暴露）────────────────────────────
import os
_provider = os.environ.get("LLM_PROVIDER", "openai").lower()
_openai_key = os.environ.get("OPENAI_API_KEY", "")
_google_key = os.environ.get("GOOGLE_API_KEY", "")

_llm_ready = False
if _provider == "ollama":
    st.session_state["openai_api_key"] = "ollama"
    st.session_state["llm_provider"] = "ollama"
    _llm_ready = True
elif _provider == "google" and _google_key and _google_key != "your-google-api-key-here":
    st.session_state["openai_api_key"] = _google_key
    st.session_state["llm_provider"] = "google"
    _llm_ready = True
elif _openai_key and _openai_key != "sk-your-openai-api-key-here":
    st.session_state["openai_api_key"] = _openai_key
    st.session_state["llm_provider"] = "openai"
    _llm_ready = True

if _llm_ready:
    provider_label = {"ollama": "Ollama (本地)", "google": "Gemini", "openai": "OpenAI"}.get(
        st.session_state.get("llm_provider", "openai"), "OpenAI"
    )
    st.sidebar.success(f"✅ LLM API 已就緒（{provider_label}）")
else:
    st.sidebar.warning("⚠️ 未設定 LLM API Key\n請在 .env 檔案中設定")

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
# 頁面 0：系統總覽
# ══════════════════════════════════════════════════════════════════════════════
if page_key == "overview":
    st.title("🛡️ AI 詐騙進化預測系統")
    st.markdown("### 從被動防禦到主動預測，運用生成式 AI 構築下一代防詐護城河")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("詐騙類型涵蓋", "5 種", "↑ 持續擴充")
    col2.metric("心理特徵分類", "5 類", "信任/緊迫/勒索/權威/利益")
    col3.metric("預期攔截率", "85%+", "↑ 優於傳統方法")
    col4.metric("預警時間", "24 小時", "↓ 傳統需 14 天")

    st.markdown("---")
    st.subheader("🔄 系統運作流程")
    st.markdown("""
    ```
    ① 情境種子輸入  →  ② LLM 話術裂變生成（GPT-4o）
           ↓
    ③ NLP 特徵萃取  →  ④ XAI 可解釋性高亮
           ↓
    ⑤ 異常偵測預警  →  ⑥ Risk Vector 輸出  →  ⑦ API 串接金融機構
    ```
    """)

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🎯 核心創新")
        st.markdown("""
        - **主動預測**：不等受害者報案，AI 自行沙盤推演未來話術
        - **低資料依賴**：少量種子案例即可擴增數百種變形
        - **可解釋性**：XAI 高亮具體觸發片段，非黑盒子
        - **心理層分析**：偵測 FOMO、權威施壓等深層操控手法
        """)
    with col_b:
        st.subheader("💼 商業應用")
        st.markdown("""
        - **B2B 金融**：API 串接銀行，即時攔截高風險匯款
        - **B2B 電商**：掃描假賣場、釣魚訊息
        - **B2G 政府**：提供 165 反詐中心趨勢預警報告
        """)

    st.markdown("---")
    st.subheader("📁 使用說明")
    st.markdown("""
    | 頁面 | 功能 |
    |------|------|
    | 🤖 LLM 話術生成 | 輸入詐騙情境，呼叫 GPT-4o 生成變種話術 |
    | 🔍 XAI 話術分析 | 高亮顯示觸發心理操控特徵的具體片段 |
    | 🔥 熱詞排行榜 | 近期詐騙高頻關鍵詞統計 |
    | 🧪 沙盤推演 | 預測特定情境的詐騙變種特徵 |
    | 🗺️ 受害風險地圖 | 依年齡層與地區呈現風險指數 |
    | 📊 模型準確率評估 | 混淆矩陣與分類效能指標 |
    """)


# ══════════════════════════════════════════════════════════════════════════════
# 頁面 LLM：真實 LLM 話術生成 Demo
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "llm_demo":
    st.title("🤖 LLM 話術生成 Demo")
    st.markdown("輸入基礎詐騙情境，呼叫 GPT-4o 生成多種變形話術，並即時進行 XAI 分析。")

    import json
    from app.pattern_analyzer.xai_highlighter import XAIHighlighter

    TAG_COLORS = {
        "信任建立": "#d4edda", "緊迫感製造": "#fff3cd",
        "情緒勒索": "#f8d7da", "權威偽裝": "#cce5ff", "利益誘導": "#e2d9f3",
    }
    TAG_TEXT_COLORS = {
        "信任建立": "#155724", "緊迫感製造": "#856404",
        "情緒勒索": "#721c24", "權威偽裝": "#004085", "利益誘導": "#4a235a",
    }

    has_api_key = bool(st.session_state.get("openai_api_key"))
    if not has_api_key:
        st.warning("⚠️ 請在左側側邊欄輸入 OpenAI API Key 以啟用真實 LLM 生成。未設定時將使用示範資料。")

    with st.form("llm_form"):
        col1, col2 = st.columns(2)
        with col1:
            scenario = st.text_area(
                "詐騙情境描述",
                value="假冒銀行客服，聲稱帳戶出現異常交易",
                height=100,
            )
            audience = st.selectbox(
                "目標受眾",
                ["中老年族群", "年輕族群", "學生族群", "商業人士", "一般民眾"],
            )
        with col2:
            sample_count = st.slider("生成樣本數量", min_value=3, max_value=10, value=5)
            show_xai = st.checkbox("同時執行 XAI 分析", value=True)

        submitted = st.form_submit_button("🚀 生成話術", type="primary")

    if submitted:
        if has_api_key:
            # 真實 LLM 呼叫
            with st.spinner("正在呼叫 GPT-4o 生成話術..."):
                try:
                    import asyncio
                    import os
                    os.environ["OPENAI_API_KEY"] = st.session_state["openai_api_key"]

                    from app.scam_engine.generator import generate_scam_samples
                    result = asyncio.run(generate_scam_samples(
                        scenario=scenario,
                        target_audience=audience,
                        min_samples=sample_count,
                    ))

                    if "error_code" in result:
                        st.error(f"LLM 呼叫失敗：{result.get('description', '未知錯誤')}")
                        samples = []
                    else:
                        samples = result.get("samples", [])
                        st.success(f"✅ 成功生成 {len(samples)} 個話術樣本（真實 GPT-4o 輸出）")
                except Exception as e:
                    st.error(f"呼叫失敗：{e}")
                    samples = []
        else:
            # Mock 示範資料
            samples = [
                {
                    "content": f"您好，我是{scenario[:8]}的客服專員，您的帳戶出現異常，請立即配合處理，否則將在24小時內凍結。",
                    "psychological_tags": ["權威偽裝", "緊迫感製造"],
                    "target_audience": audience,
                },
                {
                    "content": f"親愛的客戶，為了保護您的資金安全，我們的專業團隊需要您立即提供驗證碼，這是最後的機會。",
                    "psychological_tags": ["信任建立", "緊迫感製造"],
                    "target_audience": audience,
                },
                {
                    "content": f"您的帳戶涉及一起重大詐騙案件，警方正在調查，請立即配合轉帳至安全帳戶，否則您將面臨法律責任。",
                    "psychological_tags": ["權威偽裝", "情緒勒索"],
                    "target_audience": audience,
                },
            ]
            st.info("📋 使用示範資料（請設定 API Key 以啟用真實生成）")

        if samples:
            st.markdown("---")
            highlighter = XAIHighlighter()

            for i, sample in enumerate(samples, 1):
                with st.expander(f"樣本 {i}：{', '.join(sample.get('psychological_tags', []))}", expanded=(i == 1)):
                    content = sample.get("content", "")

                    if show_xai and content:
                        xai_result = highlighter.highlight(content)
                        # 高亮顯示
                        html_parts = []
                        prev_end = 0
                        for span in xai_result.spans:
                            if span.start > prev_end:
                                html_parts.append(content[prev_end:span.start])
                            bg = TAG_COLORS.get(span.tag, "#eee")
                            fg = TAG_TEXT_COLORS.get(span.tag, "#333")
                            html_parts.append(
                                f'<mark style="background:{bg};color:{fg};padding:2px 4px;'
                                f'border-radius:3px;font-weight:bold;" title="{span.tag}">'
                                f'{span.text}</mark>'
                            )
                            prev_end = span.end
                        if prev_end < len(content):
                            html_parts.append(content[prev_end:])
                        st.markdown(
                            f'<div style="line-height:2;padding:10px;border:1px solid #dee2e6;'
                            f'border-radius:6px;background:#fafafa;">{"".join(html_parts)}</div>',
                            unsafe_allow_html=True,
                        )
                        tags_str = " ".join(
                            f'<span style="background:{TAG_COLORS.get(t,"#eee")};'
                            f'color:{TAG_TEXT_COLORS.get(t,"#333")};padding:3px 8px;'
                            f'border-radius:10px;margin:2px;font-size:0.85rem;">{t}</span>'
                            for t in xai_result.triggered_tags
                        )
                        st.markdown(f"**心理特徵：** {tags_str}", unsafe_allow_html=True)
                    else:
                        st.write(content)
                        tags = sample.get("psychological_tags", [])
                        if tags:
                            st.markdown(f"**心理特徵：** {', '.join(tags)}")


# ══════════════════════════════════════════════════════════════════════════════
# 頁面 1：熱詞排行榜
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "hotwords":
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
        df_chart = pd.DataFrame(
            list(chart_data.items()), columns=["關鍵詞", "出現次數"]
        ).set_index("關鍵詞")
        st.bar_chart(df_chart)

        st.subheader("📋 排行榜明細")
        import pandas as pd
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


# ══════════════════════════════════════════════════════════════════════════════
# 頁面 7：模型準確率評估
# ══════════════════════════════════════════════════════════════════════════════
elif page_key == "evaluation":
    st.title("📊 模型準確率評估")
    st.markdown("使用示範資料集評估詐騙偵測模型的分類效能，產出混淆矩陣與關鍵指標。")

    import pandas as pd
    import numpy as np
    from app.pattern_analyzer.psych_classifier import PsychologicalClassifier
    from app.pattern_analyzer.xai_highlighter import XAIHighlighter

    # ── 測試資料集（含標籤）──────────────────────────────────────────────────
    TEST_CASES = [
        # (文字, 是否為詐騙)
        ("您好，我是台灣銀行客服，您的帳戶出現異常，請立即提供驗證碼，否則帳戶將凍結。", True),
        ("投資我們的平台，保證月報酬15%，零風險高獲利，立即加入！", True),
        ("我是刑事局偵查員，您的帳戶涉及洗錢案件，請配合轉帳至安全帳戶。", True),
        ("限時優惠！今天下單享8折，明天恢復原價，不要錯過最後機會！", True),
        ("您好，我是您的投資顧問，這個機會千載難逢，保證獲利，請立即匯款。", True),
        ("親愛的用戶，您的帳戶已被盜用，請立即點擊連結重設密碼，否則帳戶將永久停用。", True),
        ("我是警察，您涉嫌詐騙，需要配合調查，請將存款轉至指定帳戶保管。", True),
        ("恭喜您中獎！請提供個人資料及手續費，即可領取百萬獎金。", True),
        ("今天天氣很好，適合出門散步。", False),
        ("請問您的訂單已出貨，預計明天送達，感謝您的購買。", False),
        ("您好，這是您的月結帳單，請於截止日前繳費，謝謝。", False),
        ("系統維護通知：本系統將於今晚12點進行例行維護，造成不便敬請見諒。", False),
        ("感謝您的來電，我們的客服人員將在工作時間內回覆您。", False),
        ("您的包裹已到達配送中心，請確認收件地址是否正確。", False),
        ("本月電費帳單已開立，金額為新台幣1,234元，請至便利商店繳費。", False),
        ("您好，您預約的門診時間為明天上午10點，請準時前往。", False),
    ]

    if st.button("▶️ 執行評估", type="primary"):
        with st.spinner("正在分析測試資料集..."):
            classifier = PsychologicalClassifier()
            highlighter = XAIHighlighter()

            y_true = []
            y_pred = []
            results_data = []

            for text, is_scam in TEST_CASES:
                tags = classifier.classify(text)
                xai = highlighter.highlight(text)
                predicted_scam = len(tags) > 0 or xai.coverage_ratio > 0.05

                y_true.append(1 if is_scam else 0)
                y_pred.append(1 if predicted_scam else 0)

                results_data.append({
                    "文字摘要": text[:30] + "...",
                    "真實標籤": "🔴 詐騙" if is_scam else "🟢 正常",
                    "預測標籤": "🔴 詐騙" if predicted_scam else "🟢 正常",
                    "觸發特徵": ", ".join(tags) if tags else "無",
                    "覆蓋率": f"{xai.coverage_ratio:.1%}",
                    "結果": "✅ 正確" if (is_scam == predicted_scam) else "❌ 錯誤",
                })

            y_true_arr = np.array(y_true)
            y_pred_arr = np.array(y_pred)

            tp = int(np.sum((y_true_arr == 1) & (y_pred_arr == 1)))
            tn = int(np.sum((y_true_arr == 0) & (y_pred_arr == 0)))
            fp = int(np.sum((y_true_arr == 0) & (y_pred_arr == 1)))
            fn = int(np.sum((y_true_arr == 1) & (y_pred_arr == 0)))

            accuracy = (tp + tn) / len(y_true) if y_true else 0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0

        # ── 關鍵指標 ──────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📈 關鍵效能指標")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("整體準確率", f"{accuracy:.1%}")
        c2.metric("精確率", f"{precision:.1%}")
        c3.metric("召回率（攔截率）", f"{recall:.1%}")
        c4.metric("F1 分數", f"{f1:.3f}")
        c5.metric("誤判率", f"{false_positive_rate:.1%}", delta=f"{false_positive_rate:.1%}", delta_color="inverse")

        # ── 混淆矩陣 ──────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("🔢 混淆矩陣")
        cm_df = pd.DataFrame(
            [[tp, fn], [fp, tn]],
            index=["實際：詐騙", "實際：正常"],
            columns=["預測：詐騙", "預測：正常"],
        )
        st.dataframe(
            cm_df.style.background_gradient(cmap="RdYlGn", axis=None),
            use_container_width=False,
        )
        st.caption(f"TP={tp}（正確攔截詐騙）｜TN={tn}（正確放行正常）｜FP={fp}（誤判正常為詐騙）｜FN={fn}（漏判詐騙）")

        # ── 詳細結果 ──────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📋 逐筆分析結果")
        results_df = pd.DataFrame(results_data)
        st.dataframe(results_df, use_container_width=True, hide_index=True)
    else:
        st.info("點擊「執行評估」按鈕開始分析示範資料集。")
