# 需求文件

## 簡介

AI 詐騙進化預測系統（AI Scam Evolution Prediction System）是一套主動式防詐情報平台。有別於傳統依賴已知黑名單的被動防禦機制，本系統透過生成式 AI 逆向工程詐騙邏輯，主動預測並生成未來可能出現的詐騙話術變種，結合 NLP 心理特徵萃取與時間序列異常偵測，輸出高風險語意特徵向量，並透過視覺化儀表板提供決策支援。系統服務對象涵蓋金融機構、電商平台、社群媒體業者及政府反詐機構。

---

## 詞彙表

- **System**：AI 詐騙進化預測系統整體
- **Scam_Generation_Engine**：詐騙生成引擎，負責驅動 LLM 產生詐騙話術變種樣本
- **Pattern_Analyzer**：模式分析與特徵萃取模組，負責語意嵌入、關鍵字提取與分群
- **Prediction_Layer**：預測與預警模型，負責時間序列分析與異常偵測
- **Dashboard**：視覺化決策儀表板，負責呈現分析結果與風險指數
- **API_Gateway**：對外提供 B2B/B2G 整合的 API 閘道
- **Access_Controller**：存取控制模組，負責管控詐騙腳本的存取權限
- **Risk_Vector**：高風險語意特徵向量，為系統對外輸出的核心資料結構
- **Scam_Script**：系統內部生成的詐騙對話樣本，屬於受管制資料
- **Operator**：具備授權的系統操作人員（如防詐分析師、政府機構人員）
- **External_Client**：透過 API 串接的外部系統（如銀行數位客服、電商平台）

---

## 需求

### 需求 1：詐騙話術變種生成

**使用者故事：** 身為防詐分析師，我希望系統能根據基礎詐騙情境自動生成多種話術變種，以便提前掌握未知攻擊手法。

#### 驗收標準

1. WHEN 操作人員提供基礎詐騙情境與目標受眾特徵，THE Scam_Generation_Engine SHALL 呼叫 LLM 並生成至少 10 種具備不同語氣與手法的詐騙對話樣本。
2. WHEN Scam_Generation_Engine 完成生成，THE Scam_Generation_Engine SHALL 在 60 秒內回傳所有樣本至系統內部儲存區。
3. IF LLM 服務回應逾時或發生錯誤，THEN THE Scam_Generation_Engine SHALL 記錄錯誤事件並回傳包含錯誤代碼與描述的結構化錯誤訊息。
4. THE Scam_Generation_Engine SHALL 僅接受來自 Access_Controller 已授權的操作人員請求。
5. WHEN 生成任務完成，THE Scam_Generation_Engine SHALL 將 Scam_Script 標記為受管制資料並限制直接存取。

---

### 需求 2：語意模式分析與心理特徵萃取

**使用者故事：** 身為防詐分析師，我希望系統能自動分析詐騙話術的語意結構與心理操控特徵，以便建立可量化的風險特徵模型。

#### 驗收標準

1. WHEN 新的 Scam_Script 進入分析佇列，THE Pattern_Analyzer SHALL 使用 Sentence-BERT 語意嵌入對每份樣本產生語意向量。
2. WHEN 語意向量生成完成，THE Pattern_Analyzer SHALL 使用 TF-IDF 演算法提取每份樣本的前 20 個關鍵詞。
3. THE Pattern_Analyzer SHALL 針對每份樣本識別並標記以下心理操控特徵類別：信任建立、緊迫感製造、情緒勒索、權威偽裝、利益誘導。
4. WHEN 分析完成，THE Pattern_Analyzer SHALL 使用分群演算法將語意向量歸類至對應的詐騙手法類群。
5. IF 輸入樣本的語言非繁體中文或英文，THEN THE Pattern_Analyzer SHALL 標記該樣本為「語言不支援」並跳過分析流程。

---

### 需求 3：詐騙趨勢預測與異常預警

**使用者故事：** 身為防詐分析師，我希望系統能比對歷史報案資料與生成樣本，預測高風險詐騙手法的出現時機，以便提前部署防禦措施。

#### 驗收標準

1. THE Prediction_Layer SHALL 定期（每 24 小時）對累積的語意向量執行時間序列分析，識別新興詐騙手法的趨勢變化。
2. WHEN 時間序列分析偵測到異常模式，THE Prediction_Layer SHALL 生成包含風險等級（高／中／低）與觸發特徵描述的預警事件。
3. WHEN 預警事件生成，THE Prediction_Layer SHALL 在 5 分鐘內通知已訂閱的 Operator。
4. THE Prediction_Layer SHALL 將真實報案資料與系統生成的預測資料進行比對，計算預測準確率並記錄於系統日誌。
5. IF 真實報案資料匯入格式不符合系統規範，THEN THE Prediction_Layer SHALL 拒絕該批資料並回傳格式錯誤說明。
6. THE Prediction_Layer SHALL 輸出 Risk_Vector，其中包含高風險語意特徵、對應詐騙類群標籤及風險分數（0.0 至 1.0）。

---

### 需求 4：視覺化決策儀表板

**使用者故事：** 身為防詐分析師或政府機構人員，我希望透過儀表板即時掌握詐騙趨勢與受害風險分布，以便快速做出決策。

#### 驗收標準

1. THE Dashboard SHALL 呈現當週高頻詐騙熱詞排行（前 20 名），並每 24 小時自動更新。
2. THE Dashboard SHALL 提供新興詐騙變種手法的沙盤推演介面，允許 Operator 輸入情境參數並觀察預測結果。
3. THE Dashboard SHALL 依族群維度（年齡層、地區）呈現受害風險指數，資料來源為 Prediction_Layer 輸出的 Risk_Vector。
4. WHEN Operator 登入 Dashboard，THE Dashboard SHALL 在 3 秒內完成頁面初始載入並顯示最新資料。
5. IF 後端資料服務不可用，THEN THE Dashboard SHALL 顯示最後一次成功載入的快取資料，並標示資料更新時間。

---

### 需求 5：B2B/B2G API 整合

**使用者故事：** 身為金融機構或政府機構的技術整合人員，我希望透過 API 取得風險特徵向量，以便串接至現有系統進行即時風險判斷。

#### 驗收標準

1. THE API_Gateway SHALL 提供 RESTful API，允許 External_Client 查詢指定時間範圍內的 Risk_Vector。
2. WHEN External_Client 發送 API 請求，THE API_Gateway SHALL 在 500 毫秒內回傳結果（不含網路傳輸延遲）。
3. THE API_Gateway SHALL 對所有 API 請求執行 API 金鑰驗證，拒絕未授權請求並回傳 HTTP 401 狀態碼。
4. IF External_Client 在 60 秒內的請求次數超過訂閱方案上限，THEN THE API_Gateway SHALL 回傳 HTTP 429 狀態碼並附上重試等待時間。
5. THE API_Gateway SHALL 僅對外輸出 Risk_Vector 與防禦摘要，不得直接暴露 Scam_Script 內容。

---

### 需求 6：詐騙腳本存取管制

**使用者故事：** 身為系統管理員，我希望確保生成的詐騙腳本受到嚴格存取控制，以防止內容被濫用。

#### 驗收標準

1. THE Access_Controller SHALL 對所有 Scam_Script 的讀取、匯出操作執行角色權限驗證，僅允許具備「詐騙分析師」或「系統管理員」角色的 Operator 存取。
2. WHEN Operator 存取 Scam_Script，THE Access_Controller SHALL 記錄存取事件，包含操作人員識別碼、存取時間與操作類型。
3. THE System SHALL 不透過任何對外介面（包含 API_Gateway 與 Dashboard）直接輸出 Scam_Script 的完整對話內容。
4. IF Operator 嘗試匯出超過 100 份 Scam_Script，THEN THE Access_Controller SHALL 要求二次身份驗證並記錄該異常操作。
5. THE Access_Controller SHALL 對存取日誌執行防竄改保護，確保日誌記錄不可被修改或刪除。

---

### 需求 7：真實報案資料匯入與模型微調

**使用者故事：** 身為系統管理員，我希望能定期匯入警政署或民間防詐組織的真實報案資料，以便持續提升預測模型的準確性。

#### 驗收標準

1. THE System SHALL 支援以 CSV 與 JSON 格式匯入真實報案資料。
2. WHEN 報案資料匯入完成，THE Prediction_Layer SHALL 使用新資料對預測模型執行增量微調，並記錄微調前後的預測準確率變化。
3. IF 匯入的報案資料包含個人識別資訊（PII），THEN THE System SHALL 在資料進入分析流程前自動執行去識別化處理。
4. THE System SHALL 保留每次模型微調的版本記錄，允許 Operator 回滾至前一個穩定版本。
5. WHEN 模型微調完成，THE System SHALL 通知 Operator 並提供微調摘要報告，包含資料筆數、準確率變化與新增詐騙類群數量。
