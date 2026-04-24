# 需求文件：即時資料自動更新 (Live Data Auto-Update)

## 簡介

本功能將系統從硬編碼的靜態詐騙統計資料（`data/taiwan_scam_data.py`）轉換為可自動從外部來源抓取最新台灣詐騙統計資料的動態架構。系統將透過排程任務定期從政府公開資料平台（如 data.gov.tw、警政署開放資料）擷取最新數據，並在 Dashboard 上顯示資料最後更新時間，讓使用者了解資料的新鮮度。當外部資料來源不可用時，系統將自動降級至最近一次成功快取的資料。

## 詞彙表

- **Data_Fetcher**：負責從外部資料來源擷取最新詐騙統計資料的模組
- **Data_Source_Registry**：管理與註冊所有外部資料來源端點的元件，包含 URL、解析器對應與優先順序
- **Fetch_Scheduler**：基於 APScheduler 的排程元件，負責定期觸發資料擷取任務
- **Data_Normalizer**：將不同來源的原始資料轉換為系統內部統一格式的元件
- **Cache_Manager**：管理資料快取的元件，負責儲存最近一次成功擷取的資料與其時間戳記
- **Freshness_Indicator**：Dashboard 上顯示資料最後更新時間與新鮮度狀態的 UI 元件
- **Fallback_Provider**：當所有外部來源皆不可用時，提供快取資料或靜態預設資料的元件
- **Normalized_Data**：經過 Data_Normalizer 轉換後的統一格式資料結構
- **Fetch_Result**：單次資料擷取操作的結果，包含資料內容、來源識別、擷取時間與成功/失敗狀態
- **TTL**：Time-To-Live，快取資料的有效存活時間（秒）

## 需求

### 需求 1：外部資料來源擷取

**使用者故事：** 身為系統管理員，我希望系統能自動從政府公開資料平台擷取最新的詐騙統計資料，以便 Dashboard 顯示的數據能反映最新狀況。

#### 驗收條件

1. WHEN 排程觸發資料擷取任務，THE Data_Fetcher SHALL 向 Data_Source_Registry 中已註冊的資料來源發送 HTTP GET 請求以取得最新資料
2. WHEN Data_Fetcher 收到外部來源的 HTTP 回應，THE Data_Fetcher SHALL 在 30 秒內完成單一來源的請求與回應處理
3. WHEN 外部來源回傳 HTTP 狀態碼 200 且回應內容為有效格式，THE Data_Fetcher SHALL 將原始回應傳遞給 Data_Normalizer 進行格式轉換
4. IF 外部來源回傳非 200 狀態碼或連線逾時，THEN THE Data_Fetcher SHALL 記錄錯誤訊息（包含來源名稱、狀態碼、錯誤描述）並嘗試下一個已註冊的資料來源
5. IF 所有已註冊的資料來源皆擷取失敗，THEN THE Data_Fetcher SHALL 記錄警告等級日誌並通知 Fallback_Provider 啟動降級機制

### 需求 2：資料來源註冊與管理

**使用者故事：** 身為開發者，我希望能透過設定檔管理外部資料來源清單，以便在來源 URL 變更或新增來源時無需修改程式碼。

#### 驗收條件

1. THE Data_Source_Registry SHALL 支援透過設定檔（環境變數或設定模組）註冊至少 3 個外部資料來源端點
2. THE Data_Source_Registry SHALL 為每個已註冊的資料來源儲存以下屬性：名稱、URL、資料格式（JSON 或 CSV）、優先順序（整數，數值越小優先順序越高）、啟用狀態（布林值）
3. WHEN Data_Fetcher 請求資料來源清單，THE Data_Source_Registry SHALL 依優先順序由高至低回傳所有啟用狀態為 True 的資料來源
4. WHEN 某資料來源連續失敗 3 次，THE Data_Source_Registry SHALL 將該來源標記為暫時停用，並在 1 小時後自動恢復啟用狀態

### 需求 3：資料格式正規化

**使用者故事：** 身為開發者，我希望不同來源的資料能被轉換為統一格式，以便 Dashboard 和分析模組能一致地使用這些資料。

#### 驗收條件

1. WHEN Data_Normalizer 收到來自外部來源的原始資料，THE Data_Normalizer SHALL 將原始資料轉換為 Normalized_Data 格式
2. THE Normalized_Data SHALL 包含以下欄位：各縣市詐騙案件數（字典）、各詐騙類型統計（字典）、月度趨勢資料（列表）、各年齡層受害比例（字典）、年度總損失統計（字典）、資料來源名稱（字串）、資料擷取時間（ISO 8601 時間戳記）
3. IF 原始資料缺少 Normalized_Data 所需的某些欄位，THEN THE Data_Normalizer SHALL 以最近一次成功快取中對應欄位的值填補缺失欄位，並在日誌中記錄已填補的欄位名稱
4. WHEN Data_Normalizer 完成轉換，THE Data_Normalizer SHALL 驗證 Normalized_Data 中所有數值欄位為非負數，且所有比例欄位的總和介於 0.99 至 1.01 之間（含容差）
5. FOR ALL 有效的 Normalized_Data 物件，將 Normalized_Data 序列化為 JSON 再反序列化回 Normalized_Data SHALL 產生與原始物件等價的結果（往返屬性）

### 需求 4：排程自動擷取

**使用者故事：** 身為系統管理員，我希望系統能定期自動擷取最新資料，以便使用者每次開啟 Dashboard 時都能看到相對新鮮的數據。

#### 驗收條件

1. WHEN 系統啟動時，THE Fetch_Scheduler SHALL 立即觸發一次資料擷取任務
2. WHILE 系統運行中，THE Fetch_Scheduler SHALL 每隔可設定的間隔時間（預設 6 小時）自動觸發一次資料擷取任務
3. THE Fetch_Scheduler SHALL 透過環境變數 `DATA_FETCH_INTERVAL_HOURS` 讀取排程間隔，接受 1 至 168 之間的整數值
4. IF Fetch_Scheduler 的排程間隔設定值超出 1 至 168 的範圍，THEN THE Fetch_Scheduler SHALL 記錄警告日誌並使用預設值 6 小時
5. WHEN 排程任務正在執行中且下一次排程時間到達，THE Fetch_Scheduler SHALL 跳過本次觸發並記錄資訊等級日誌

### 需求 5：快取與降級機制

**使用者故事：** 身為使用者，我希望即使外部資料來源暫時不可用，Dashboard 仍能顯示資料，以便我不會看到空白頁面或錯誤訊息。

#### 驗收條件

1. WHEN Data_Fetcher 成功擷取並正規化資料，THE Cache_Manager SHALL 將 Normalized_Data 連同擷取時間戳記儲存至快取
2. WHEN Dashboard 請求詐騙統計資料，THE Cache_Manager SHALL 優先回傳快取中最新的 Normalized_Data
3. IF 快取中無任何資料且所有外部來源皆不可用，THEN THE Fallback_Provider SHALL 回傳 `data/taiwan_scam_data.py` 中的靜態預設資料，並將資料來源標記為「靜態預設資料」
4. WHEN Cache_Manager 回傳快取資料，THE Cache_Manager SHALL 在回傳結果中包含資料的擷取時間戳記與資料來源名稱
5. THE Cache_Manager SHALL 將快取資料持久化至磁碟檔案，以確保系統重啟後快取資料不會遺失

### 需求 6：Dashboard 資料新鮮度顯示

**使用者故事：** 身為使用者，我希望在 Dashboard 上看到資料的最後更新時間，以便我能判斷目前顯示的資料是否足夠新鮮。

#### 驗收條件

1. THE Freshness_Indicator SHALL 在 Dashboard 頁面頂部顯示「資料最後更新時間」標籤
2. WHEN 資料來自最新擷取（非快取），THE Freshness_Indicator SHALL 以綠色樣式顯示更新時間，格式為「✅ 資料已更新：YYYY-MM-DD HH:MM（來源：{來源名稱}）」
3. WHEN 資料來自快取且快取年齡小於 24 小時，THE Freshness_Indicator SHALL 以黃色樣式顯示更新時間，格式為「⚠️ 快取資料：YYYY-MM-DD HH:MM（{N} 小時前更新）」
4. WHEN 資料來自快取且快取年齡大於或等於 24 小時，THE Freshness_Indicator SHALL 以紅色樣式顯示更新時間，格式為「🔴 資料可能過時：YYYY-MM-DD HH:MM（{N} 天前更新）」
5. WHEN 資料來自靜態預設資料，THE Freshness_Indicator SHALL 以灰色樣式顯示「📋 顯示靜態預設資料（2023-2024）」
6. WHEN 使用者點擊 Freshness_Indicator 旁的「立即更新」按鈕，THE Fetch_Scheduler SHALL 觸發一次手動資料擷取任務

### 需求 7：資料擷取結果日誌與監控

**使用者故事：** 身為系統管理員，我希望能追蹤每次資料擷取的結果，以便在資料來源異常時能及時發現並處理。

#### 驗收條件

1. WHEN Data_Fetcher 完成一次資料擷取（無論成功或失敗），THE Data_Fetcher SHALL 記錄一筆 Fetch_Result，包含：來源名稱、擷取時間、成功/失敗狀態、HTTP 狀態碼（若適用）、錯誤訊息（若適用）、資料筆數（若成功）
2. THE Data_Fetcher SHALL 保留最近 100 筆 Fetch_Result 紀錄供查詢
3. WHEN 連續 3 次排程擷取皆失敗，THE Data_Fetcher SHALL 記錄 ERROR 等級日誌，訊息包含「連續擷取失敗」字樣與失敗次數

### 需求 8：資料來源解析器擴充性

**使用者故事：** 身為開發者，我希望能輕鬆新增對新資料來源的解析支援，以便未來政府開放新的資料端點時能快速整合。

#### 驗收條件

1. THE Data_Normalizer SHALL 透過解析器註冊機制支援新增資料來源解析器，每個解析器對應一種資料來源格式
2. WHEN 新增一個資料來源解析器，THE Data_Normalizer SHALL 僅需實作一個接受原始資料並回傳 Normalized_Data 的函數，無需修改 Data_Normalizer 的核心邏輯
3. THE Data_Normalizer SHALL 提供至少 2 個內建解析器：一個用於 JSON 格式的政府開放資料 API 回應，一個用於 CSV 格式的統計報表檔案
