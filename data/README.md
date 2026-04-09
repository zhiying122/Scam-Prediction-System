# 詐騙案例資料集說明

本目錄存放詐騙案例相關資料，供系統訓練、測試與示範使用。

---

## 檔案清單

| 檔案名稱 | 說明 |
|---|---|
| `sample_scam_cases.csv` | 示範用詐騙案例資料集（20 筆，已去識別化） |

---

## 資料格式說明

### `sample_scam_cases.csv`

CSV 格式，UTF-8 編碼，欄位定義如下：

| 欄位名稱 | 資料型別 | 說明 | 範例 |
|---|---|---|---|
| `source` | 字串 | 資料來源標記 | `示範資料`、`165反詐騙資料庫` |
| `scam_type` | 字串 | 詐騙類型分類 | `假冒銀行客服`、`投資詐騙` |
| `description` | 字串 | 案例描述（已去識別化，不含真實個資） | 詐騙手法的文字描述 |
| `reported_at` | 日期 | 案例通報日期，格式 `YYYY-MM-DD` | `2024-01-05` |

### 詐騙類型分類

本資料集涵蓋以下五種主要詐騙類型：

| 類型 | 說明 |
|---|---|
| 假冒銀行客服 | 詐騙者偽裝成銀行或金融機構客服，以帳戶異常、信用卡盜刷等理由誘騙受害者提供帳戶資訊或轉帳 |
| 投資詐騙 | 以高報酬、保證獲利等話術吸引受害者投入資金，常見手法包括假冒投資平台、虛擬貨幣詐騙等 |
| 假冒政府機關 | 詐騙者偽裝成警察、檢察官、稅務機關等政府單位，以涉案調查、稅款未繳等理由恐嚇受害者 |
| 購物詐騙 | 在網路拍賣或二手交易平台以低價商品吸引買家，收款後不出貨或消失 |
| 愛情詐騙 | 透過交友軟體或社群媒體建立感情關係，再以各種理由請求金錢援助 |

---

## 資料去識別化說明

本資料集中的所有案例描述均已進行去識別化處理：

- 不含真實姓名、身分證字號、電話號碼、地址等個人識別資訊
- 不含真實銀行帳號、信用卡號等金融資訊
- 案例描述為通用化改寫，僅保留詐騙手法特徵

---

## 如何匯入真實政府公開資料（165 反詐騙資料庫）

### 資料來源

台灣 165 全民防騙網提供公開的詐騙案例統計資料，可透過以下管道取得：

- **165 全民防騙網**：[https://165.npa.gov.tw](https://165.npa.gov.tw)
- **政府資料開放平台**：[https://data.gov.tw](https://data.gov.tw)（搜尋「詐騙」相關資料集）
- **內政部警政署統計資料**：[https://www.npa.gov.tw](https://www.npa.gov.tw)

### 匯入步驟

1. **下載原始資料**

   從政府資料開放平台下載 CSV 或 JSON 格式的詐騙案例資料。

2. **欄位對應轉換**

   將原始資料欄位對應至本系統格式：

   ```python
   # 欄位對應範例（實際欄位名稱依原始資料而定）
   COLUMN_MAPPING = {
       "案件來源": "source",
       "詐騙類型": "scam_type",
       "案件描述": "description",
       "通報日期": "reported_at",
   }
   ```

3. **執行 PII 去識別化**

   使用系統內建的 `app/data_import/pii_remover.py` 模組移除個人識別資訊：

   ```python
   from app.data_import.pii_remover import PIIRemover

   remover = PIIRemover()
   cleaned_description = remover.remove(raw_description)
   ```

4. **使用資料匯入器**

   透過 `app/data_import/importer.py` 批次匯入資料：

   ```python
   from app.data_import.importer import DataImporter

   importer = DataImporter()
   importer.import_csv("path/to/165_data.csv", column_mapping=COLUMN_MAPPING)
   ```

5. **驗證匯入結果**

   匯入完成後，確認資料筆數與格式是否正確：

   ```bash
   # 檢查匯入後的資料筆數
   python -c "import pandas as pd; df = pd.read_csv('data/sample_scam_cases.csv'); print(f'共 {len(df)} 筆資料')"
   ```

### 注意事項

- 匯入真實資料前，務必確認已取得合法授權
- 所有含個人資訊的欄位必須先完成去識別化處理
- 建議定期（每月）更新資料以保持模型準確性
- 資料更新後需重新執行模型訓練流程

---

## 資料授權

本目錄中的示範資料（`sample_scam_cases.csv`）為虛構示範資料，僅供系統開發與測試使用，不代表真實案例。
