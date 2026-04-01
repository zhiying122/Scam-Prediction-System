"""資料匯入與清洗頁面"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import io
import json
import pandas as pd
import streamlit as st

from app.data_import.importer import DataImporter, ImportError as ImportErr
from app.data_import.pii_remover import PiiRemover

st.set_page_config(page_title="資料匯入", page_icon="📥", layout="wide")
st.title("📥 詐騙資料匯入與清洗")
st.caption("支援 CSV / JSON 格式，自動執行 PII 去識別化後送入分析流程")

importer = DataImporter()
remover = PiiRemover()

# ── 格式說明 ──────────────────────────────────────────────────────────────────
with st.expander("📋 支援的欄位格式", expanded=False):
    st.markdown("""
**必要欄位（CSV 標題列 / JSON 鍵名）：**

| 欄位名稱 | 說明 | 範例 |
|---|---|---|
| `source` | 資料來源 | 警政署、165專線、PTT |
| `scam_type` | 詐騙類型 | 假冒銀行客服、投資詐騙 |
| `description` | 案例描述（話術內容） | 受害者接到自稱銀行客服的電話... |
| `reported_at` | 報案時間 | 2024-01-15 或 2024-01-15T10:30:00 |

**選填欄位：**

| 欄位名稱 | 說明 |
|---|---|
| `region` | 地區（縣市） |
| `target_audience` | 目標受眾 |
| `loss_amount` | 損失金額（元） |
""")

# ── 下載範例檔案 ──────────────────────────────────────────────────────────────
st.subheader("下載範例檔案")
col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 4])

SAMPLE_CSV = """source,scam_type,description,reported_at,region,target_audience,loss_amount
警政署165專線,假冒銀行客服,受害者接到自稱台灣銀行客服的電話，對方表示帳戶出現異常交易，要求立即提供網路銀行密碼與驗證碼進行帳戶凍結保護，受害者依指示操作後發現帳戶遭盜領。,2024-03-15,台北市,中老年族群,250000
警政署165專線,投資詐騙,受害者在社群媒體上認識自稱投資顧問的人士，對方推薦一個保證每月獲利30%的投資平台，受害者陸續投入資金後平台突然無法登入，客服也失聯。,2024-03-18,新北市,商業人士,1500000
165反詐騙,假冒政府機關,受害者接到自稱調查局人員的電話，表示其帳戶涉及洗錢案件，要求配合調查將資金轉至指定安全帳戶，否則將遭逮捕。,2024-03-20,台中市,中老年族群,800000
PTT八卦版,購物詐騙,受害者在二手交易平台購買手機，賣家要求先付款再寄貨，收款後即失聯，商品從未寄出。,2024-03-22,高雄市,年輕族群,15000
警政署165專線,愛情詐騙,受害者在交友軟體認識外籍人士，交往數月後對方以急需手術費為由借款，受害者多次匯款後對方消失。,2024-03-25,台南市,年輕族群,320000
165反詐騙,中獎詐騙,受害者收到簡訊表示中得百萬大獎，需先繳納手續費才能領取，受害者繳費後對方要求繼續繳納稅金，循環詐騙。,2024-03-28,桃園市,一般民眾,45000
警政署165專線,假冒銀行客服,詐騙集團冒充銀行信用卡中心，謊稱受害者信用卡遭盜刷，誘導受害者至ATM操作解除分期付款設定，實際上是將資金轉出。,2024-04-01,新竹市,中老年族群,180000
PTT Gossiping,工作詐騙,受害者應徵網路兼職工作，需先墊付購買商品再等待退款，墊付多次後公司失聯，墊付款項無法追回。,2024-04-01,台北市,學生族群,28000
"""

SAMPLE_JSON = json.dumps({
    "records": [
        {
            "source": "警政署165專線",
            "scam_type": "假冒銀行客服",
            "description": "受害者接到自稱台灣銀行客服的電話，對方表示帳戶出現異常交易，要求立即提供網路銀行密碼與驗證碼進行帳戶凍結保護。",
            "reported_at": "2024-03-15",
            "region": "台北市",
            "target_audience": "中老年族群",
            "loss_amount": 250000
        },
        {
            "source": "165反詐騙",
            "scam_type": "投資詐騙",
            "description": "受害者在社群媒體認識自稱投資顧問的人士，推薦保證每月獲利30%的投資平台，陸續投入資金後平台突然無法登入。",
            "reported_at": "2024-03-18",
            "region": "新北市",
            "target_audience": "商業人士",
            "loss_amount": 1500000
        }
    ]
}, ensure_ascii=False, indent=2)

with col_dl1:
    st.download_button(
        "⬇️ 下載 CSV 範例",
        data=SAMPLE_CSV.encode("utf-8-sig"),
        file_name="scam_cases_sample.csv",
        mime="text/csv",
        use_container_width=True,
    )
with col_dl2:
    st.download_button(
        "⬇️ 下載 JSON 範例",
        data=SAMPLE_JSON.encode("utf-8"),
        file_name="scam_cases_sample.json",
        mime="application/json",
        use_container_width=True,
    )

st.divider()

# ── 檔案上傳 ──────────────────────────────────────────────────────────────────
st.subheader("上傳資料檔案")

uploaded = st.file_uploader(
    "選擇 CSV 或 JSON 檔案",
    type=["csv", "json"],
    help="檔案大小上限 200MB，編碼請使用 UTF-8",
)

use_sample = st.checkbox("使用內建範例資料（不上傳檔案）", value=False)

if use_sample or uploaded:
    st.divider()

    # ── 讀取內容 ──────────────────────────────────────────────────────────────
    if use_sample:
        content = SAMPLE_CSV.encode("utf-8")
        fmt = "csv"
        filename = "scam_cases_sample.csv"
    else:
        content = uploaded.read()
        fmt = uploaded.name.rsplit(".", 1)[-1].lower()
        filename = uploaded.name

    st.info(f"已載入：`{filename}`（格式：{fmt.upper()}）")

    # ── 匯入解析 ──────────────────────────────────────────────────────────────
    try:
        with st.spinner("解析資料中..."):
            result = importer.import_auto(content, fmt)
    except ImportErr as e:
        st.error(f"匯入失敗：{e.error_code}")
        for detail in e.details:
            st.warning(detail)
        st.stop()

    st.success(f"解析完成：共 {result.success_count} 筆，批次 ID：`{result.batch_id}`")
    if result.errors:
        with st.expander(f"⚠️ {len(result.errors)} 筆解析警告"):
            for err in result.errors:
                st.warning(err)

    # ── 原始資料預覽 ──────────────────────────────────────────────────────────
    st.subheader("原始資料預覽")
    df_raw = pd.DataFrame(result.records)
    st.dataframe(df_raw, use_container_width=True, hide_index=True, height=250)

    st.divider()

    # ── PII 去識別化 ──────────────────────────────────────────────────────────
    st.subheader("PII 去識別化")
    st.caption("自動偵測並遮蔽姓名、電話、身分證字號、地址、電子郵件")

    if st.button("🔒 執行 PII 去識別化", type="primary"):
        with st.spinner("去識別化處理中..."):
            cleaned = remover.remove_from_batch(result.records)

        # 比對哪些欄位有變化
        pii_found_count = 0
        diff_rows = []
        for raw, clean in zip(result.records, cleaned):
            changed_fields = []
            for field in ["description", "source", "scam_type"]:
                if raw.get(field) != clean.get(field):
                    changed_fields.append(field)
                    pii_found_count += 1
            diff_rows.append({
                "id": clean["id"][:8] + "...",
                "scam_type": clean["scam_type"],
                "PII已清除欄位": ", ".join(changed_fields) if changed_fields else "無",
                "description（清洗後）": clean["description"][:80] + "..." if len(clean["description"]) > 80 else clean["description"],
            })

        if pii_found_count > 0:
            st.warning(f"偵測到 {pii_found_count} 處 PII，已完成去識別化")
        else:
            st.success("未偵測到 PII，資料已符合規範")

        st.dataframe(
            pd.DataFrame(diff_rows),
            use_container_width=True,
            hide_index=True,
            height=280,
        )

        st.divider()

        # ── 統計摘要 ──────────────────────────────────────────────────────────
        st.subheader("資料統計摘要")
        df_clean = pd.DataFrame(cleaned)

        col_s1, col_s2, col_s3 = st.columns(3)

        with col_s1:
            st.markdown("**詐騙類型分布**")
            if "scam_type" in df_clean.columns:
                type_counts = df_clean["scam_type"].value_counts()
                st.bar_chart(type_counts, height=220)

        with col_s2:
            st.markdown("**資料來源分布**")
            if "source" in df_clean.columns:
                src_counts = df_clean["source"].value_counts()
                st.bar_chart(src_counts, height=220)

        with col_s3:
            st.markdown("**基本統計**")
            st.metric("總筆數", len(df_clean))
            st.metric("詐騙類型數", df_clean["scam_type"].nunique() if "scam_type" in df_clean.columns else "-")
            st.metric("資料來源數", df_clean["source"].nunique() if "source" in df_clean.columns else "-")

        # ── 匯出清洗後資料 ────────────────────────────────────────────────────
        st.divider()
        st.subheader("匯出清洗後資料")
        col_ex1, col_ex2 = st.columns(2)

        csv_out = df_clean.to_csv(index=False).encode("utf-8-sig")
        json_out = df_clean.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")

        with col_ex1:
            st.download_button(
                "⬇️ 匯出 CSV（已清洗）",
                data=csv_out,
                file_name=f"cleaned_{filename.rsplit('.', 1)[0]}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col_ex2:
            st.download_button(
                "⬇️ 匯出 JSON（已清洗）",
                data=json_out,
                file_name=f"cleaned_{filename.rsplit('.', 1)[0]}.json",
                mime="application/json",
                use_container_width=True,
            )

        st.session_state["cleaned_records"] = cleaned
        st.success("清洗完成，資料已準備好送入 Pattern Analyzer 分析流程。")
