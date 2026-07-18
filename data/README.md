# 資料集說明

本目錄存放詐騙案例相關資料，供系統訓練、測試與示範使用。

---

## 檔案清單

| 檔案名稱 | 說明 |
|---------|------|
| `taiwan_scam_data.py` | 台灣詐騙統計靜態基準資料（最終降級來源） |
| `sample_scam_cases.csv` | 示範用詐騙案例資料集（56 筆，已去識別化） |
| `live_cache.json` | 即時資料快取（系統自動更新，勿手動修改） |

---

## taiwan_scam_data.py

系統的靜態基準資料，當所有即時資料來源失敗時作為最終降級。

### 資料內容

| 變數名稱 | 說明 | 資料類型 |
|---------|------|---------|
| `TAIWAN_SCAM_CASES_BY_REGION` | 22 縣市詐騙案件數 | dict |
| `VICTIM_AGE_DISTRIBUTION` | 5 個年齡層受害比例 | dict |
| `SCAM_TYPE_STATS` | 8 種詐騙類型案件數、平均損失、趨勢 | dict |
| `MONTHLY_TREND` | 月度案件數與損失金額（2025-01 至 2026-03） | list |
| `REAL_HOTWORDS` | 38 個詐騙熱詞與頻率 | dict |
| `REAL_SCAM_SCRIPTS` | 8 則真實詐騙話術樣本（已去識別化） | list |
| `MODEL_PERFORMANCE` | 模型效能基準（1,200 筆測試集） | dict |
| `ANNUAL_STATS` | 2021-2026 年度總案件數與損失 | dict |

### 資料來源說明

| 資料 | 來源 | 類型 |
|------|------|------|
| 2021-2023 各縣市案件數 | 警政署 165 專線公開統計 | 真實統計 |
| 2021-2023 各年齡層受害比例 | 165 資料庫分析公開報告 | 真實統計 |
| 2021-2023 各詐騙類型統計 | 刑事警察局公開報告 | 真實統計 |
| 2024-2026 年統計數據 | 基於 2021-2023 趨勢線性外推 | 趨勢推估 |
| 月度趨勢（2025-2026） | 基於歷史趨勢外推 | 趨勢推估 |
| 詐騙熱詞（38 個） | 165 通報案件描述統計 | 真實統計 |
| 話術樣本（8 則） | 公開案例，已去識別化 | 真實案例 |
| 模型效能（88.9%） | 1,200 筆混合測試集 | 真實測試 |

---

## live_cache.json

系統每 6 小時自動嘗試從以下來源擷取最新資料並寫入此檔案：

1. **data.gov.tw** — 政府開放資料平台
2. **165.npa.gov.tw** — 警政署 165 反詐騙官網
3. **Google News + LLM** — 新聞搜尋 + Ollama / OpenAI 萃取數字

擷取成功時，Dashboard 會優先使用此快取資料覆蓋靜態基準。
所有來源失敗時，系統降級至 `taiwan_scam_data.py`。

**請勿手動修改此檔案**，系統會自動管理。

---

## sample_scam_cases.csv

示範用詐騙案例資料集，供 `/v1/data/import` API 端點測試使用。

### 欄位定義

| 欄位名稱 | 資料型別 | 說明 | 範例 |
|---------|---------|------|------|
| `source` | 字串 | 資料來源標記 | `示範資料`、`165反詐騙資料庫` |
| `scam_type` | 字串 | 詐騙類型分類 | `假冒銀行客服`、`投資詐騙` |
| `description` | 字串 | 案例描述（已去識別化） | 詐騙手法的文字描述 |
| `reported_at` | 日期 | 案例通報日期，格式 `YYYY-MM-DD` | `2026-01-05` |

### 涵蓋詐騙類型

| 類型 | 說明 |
|------|------|
| 假冒銀行客服 | 偽裝銀行客服，以帳戶異常為由騙取帳戶資訊或引導轉帳 |
| 投資詐騙 | 以高報酬、保證獲利吸引投資，常見假冒投資平台、虛擬貨幣詐騙 |
| 假冒政府機關 | 偽裝警察、檢察官、稅務機關，以涉案調查恐嚇受害者 |
| 購物詐騙 | 網路拍賣低價商品，收款後不出貨或消失 |
| 愛情詐騙 | 交友軟體建立感情後，以各種理由請求金錢援助 |
| 中獎詐騙 | 假冒中獎通知，以繳手續費或稅金為由騙取金錢 |
| 工作詐騙 | 以高薪工作機會吸引受害者繳交保證金或培訓費 |
| AI 深偽詐騙 | 利用 AI 語音克隆或深偽影像冒充親友或主管騙取匯款 |

---

## 如何匯入真實政府公開資料

### 資料來源

- **165 全民防騙網**：https://165.npa.gov.tw
- **政府資料開放平台**：https://data.gov.tw（搜尋「詐騙」相關資料集）
- **內政部警政署統計資料**：https://www.npa.gov.tw

### 匯入步驟

1. 從政府資料開放平台下載 CSV 或 JSON 格式的詐騙案例資料

2. 欄位對應轉換：

   ```python
   COLUMN_MAPPING = {
       "案件來源": "source",
       "詐騙類型": "scam_type",
       "案件描述": "description",
       "通報日期": "reported_at",
   }
   ```

3. 執行 PII 去識別化：

   ```python
   from app.data_import.pii_remover import PIIRemover

   remover = PIIRemover()
   cleaned_description = remover.remove(raw_description)
   ```

4. 使用資料匯入器批次匯入：

   ```python
   from app.data_import.importer import DataImporter

   importer = DataImporter()
   importer.import_csv("path/to/165_data.csv", column_mapping=COLUMN_MAPPING)
   ```

   或透過 API：

   ```bash
   curl -X POST http://localhost:8001/v1/data/import \
     -H "X-API-Key: test-key-001" \
     -F "file=@path/to/165_data.csv"
   ```

### 注意事項

- 匯入真實資料前，務必確認已取得合法授權
- 所有含個人資訊的欄位必須先完成去識別化處理
- 建議定期（每月）更新資料以保持模型準確性

---

## 資料授權

`sample_scam_cases.csv` 為虛構示範資料，僅供系統開發與測試使用，不代表真實案例。
`taiwan_scam_data.py` 中的統計數字基於政府公開報告，2024 年以後為趨勢推估值。
