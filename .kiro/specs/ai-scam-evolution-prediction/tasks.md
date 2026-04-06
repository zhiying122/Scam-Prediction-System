# 實作計畫：AI 詐騙進化預測系統

## 概覽

本計畫將設計文件拆解為一系列可由程式碼生成代理逐步執行的實作任務。每個任務皆建立在前一任務的基礎上，最終將所有元件串接為完整系統。技術棧為 Python + FastAPI + LangChain + sentence-transformers + Qdrant + PostgreSQL + Redis + APScheduler + Streamlit。

---

## 任務清單

- [x] 1. 建立專案基礎結構與核心資料模型
  - 建立目錄結構：`app/`（各模組子目錄）、`tests/`、`docker/`
  - 建立 `app/models/` 下的所有資料類別：`ScamScript`、`SemanticVector`、`RiskVector`、`AlertEvent`、`AccessLog`、`CaseReport`、`ModelVersion`
  - 建立 `pyproject.toml` 或 `requirements.txt`，列出所有依賴套件
  - 建立 `docker-compose.yml`，定義 PostgreSQL、Redis、Qdrant 服務
  - 建立 `app/config.py`，集中管理環境變數（資料庫連線、API 金鑰、LLM 設定）
  - 建立 `tests/conftest.py`，定義共用 fixtures（測試資料庫、mock LLM client）
  - _需求：1.1、2.1、3.6、6.2_

- [x] 2. 實作 Access_Controller（存取管制模組）
  - [x] 2.1 實作 RBAC 角色驗證核心邏輯
    - 建立 `app/access_controller/rbac.py`，定義角色枚舉與權限矩陣
    - 實作 `check_permission(operator_id, role, action)` 函數，驗證操作人員是否具備指定操作權限
    - 實作 `require_role(roles)` FastAPI 依賴注入裝飾器
    - _需求：6.1_

  - [x]* 2.2 撰寫屬性測試：角色存取控制
    - **屬性 18：角色存取控制**
    - **驗證需求：6.1**

  - [x] 2.3 實作存取日誌防竄改雜湊鏈
    - 建立 `app/access_controller/audit_log.py`
    - 實作 `append_log(operator_id, action, resource_id, resource_type)` 函數，計算並儲存 `prev_hash` 與 `current_hash`（SHA-256）
    - 實作 `verify_chain()` 函數，驗證整條日誌鏈的雜湊完整性
    - 使用 PostgreSQL append-only 資料表儲存日誌
    - _需求：6.2、6.5_

  - [x]* 2.4 撰寫屬性測試：存取日誌記錄完整性（Round-Trip）
    - **屬性 19：存取日誌記錄完整性（Round-Trip）**
    - **驗證需求：6.2**

  - [x]* 2.5 撰寫屬性測試：日誌防竄改雜湊鏈完整性
    - **屬性 21：日誌防竄改雜湊鏈完整性**
    - **驗證需求：6.5**

  - [x] 2.6 實作批量匯出二次驗證（TOTP）
    - 建立 `app/access_controller/mfa.py`，整合 `pyotp` 實作 TOTP 驗證流程
    - 實作 `require_2fa_for_bulk_export(count)` 函數，當匯出數量 > 100 時觸發 TOTP 驗證
    - _需求：6.4_

  - [x]* 2.7 撰寫屬性測試：批量匯出二次驗證閾值
    - **屬性 20：批量匯出二次驗證閾值**
    - **驗證需求：6.4**

- [x] 3. 實作 API_Gateway 中介軟體與路由骨架
  - [x] 3.1 實作 API 金鑰驗證中介軟體
    - 建立 `app/api_gateway/middleware/api_key.py`，實作 `APIKeyMiddleware`
    - 從 PostgreSQL 查詢 API 金鑰有效性，無效時回傳 HTTP 401
    - _需求：5.3_

  - [x]* 3.2 撰寫屬性測試：API 金鑰驗證拒絕無效請求
    - **屬性 15：API 金鑰驗證拒絕無效請求**
    - **驗證需求：5.3**

  - [x] 3.3 實作速率限制中介軟體
    - 建立 `app/api_gateway/middleware/rate_limit.py`，實作 `RateLimitMiddleware`
    - 使用 Redis 滑動視窗計數（60 秒視窗），超限回傳 HTTP 429 含 `Retry-After` 標頭
    - _需求：5.4_

  - [x]* 3.4 撰寫屬性測試：速率限制觸發 HTTP 429
    - **屬性 16：速率限制觸發 HTTP 429**
    - **驗證需求：5.4**

  - [x] 3.5 建立 FastAPI 應用程式與路由骨架
    - 建立 `app/api_gateway/main.py`，掛載所有中介軟體
    - 建立 `app/api_gateway/routers/` 下各路由模組骨架（scam、risk_vectors、data、predictions、health）
    - 實作 `GET /v1/health` 健康檢查端點
    - 實作請求日誌中介軟體 `RequestLoggingMiddleware`
    - _需求：5.1、5.2_

- [x] 4. 實作 Scam_Generation_Engine（詐騙話術生成引擎）
  - [x] 4.1 實作 LLM 呼叫核心邏輯與 Prompt 模板
    - 建立 `app/scam_engine/generator.py`
    - 使用 LangChain 定義 prompt template，要求 LLM 輸出 JSON 結構化的 10+ 詐騙對話樣本
    - 每個樣本包含：話術文本、心理操控類別標籤、目標受眾描述
    - 實作指數退避重試邏輯（最多 3 次，初始延遲 1 秒，倍數 2）
    - _需求：1.1、1.2_

  - [x]* 4.2 撰寫屬性測試：生成樣本數量下限
    - **屬性 1：生成樣本數量下限**
    - **驗證需求：1.1**

  - [x] 4.3 實作 LLM 錯誤處理與結構化錯誤回應
    - 實作 LLM 逾時（> 60s）與 API 錯誤的捕捉邏輯
    - 回傳包含 `error_code`、`description`、`timestamp`、`request_id` 的結構化錯誤訊息
    - _需求：1.3_

  - [x]* 4.4 撰寫屬性測試：LLM 錯誤回應結構完整性
    - **屬性 2：LLM 錯誤回應結構完整性**
    - **驗證需求：1.3**

  - [x] 4.5 整合 Access_Controller 授權驗證與 Scam_Script 受管制標記
    - 在生成流程入口呼叫 `check_permission`，未授權時拒絕請求
    - 生成完成後將 Scam_Script 儲存至 PostgreSQL，`is_regulated` 恆設為 `True`
    - 實作 `POST /v1/scam/generate` 端點，回傳 202 Accepted + `task_id`
    - _需求：1.4、1.5_

  - [x]* 4.6 撰寫屬性測試：未授權請求一律拒絕
    - **屬性 3：未授權請求一律拒絕**
    - **驗證需求：1.4**

  - [x]* 4.7 撰寫屬性測試：Scam_Script 受管制標記不變量
    - **屬性 4：Scam_Script 受管制標記不變量**
    - **驗證需求：1.5**

- [x] 5. 檢查點：確認所有測試通過，如有問題請向使用者提問

- [x] 6. 實作 Pattern_Analyzer（語意分析與特徵萃取模組）
  - [x] 6.1 實作語言偵測與 Sentence-BERT 語意嵌入
    - 建立 `app/pattern_analyzer/embedder.py`
    - 使用 `langdetect` 或 `lingua` 偵測輸入語言，非中文/英文時標記 `language: unsupported` 並跳過
    - 載入 `paraphrase-multilingual-MiniLM-L12-v2` 模型，對合法樣本產生 384 維語意向量
    - 驗證向量不含 NaN 或 Inf 值
    - _需求：2.1、2.5_

  - [x]* 6.2 撰寫屬性測試：語意向量維度正確性
    - **屬性 5：語意向量維度正確性**
    - **驗證需求：2.1**

  - [x]* 6.3 撰寫屬性測試：不支援語言的跳過行為
    - **屬性 9：不支援語言的跳過行為**
    - **驗證需求：2.5**

  - [x] 6.4 實作 TF-IDF 關鍵詞提取
    - 建立 `app/pattern_analyzer/keyword_extractor.py`
    - 使用 `scikit-learn` TF-IDF 提取前 20 個關鍵詞，確保無重複詞彙
    - _需求：2.2_

  - [x]* 6.5 撰寫屬性測試：TF-IDF 關鍵詞數量上限
    - **屬性 6：TF-IDF 關鍵詞數量上限**
    - **驗證需求：2.2**

  - [x] 6.6 實作心理特徵分類器
    - 建立 `app/pattern_analyzer/psych_classifier.py`
    - 實作規則式 + 輕量分類模型混合方式，識別五類特徵：信任建立、緊迫感製造、情緒勒索、權威偽裝、利益誘導
    - 每份樣本可標記多個特徵類別，輸出標籤必須屬於合法集合
    - _需求：2.3_

  - [x]* 6.7 撰寫屬性測試：心理特徵標籤合法性
    - **屬性 7：心理特徵標籤合法性**
    - **驗證需求：2.3**

  - [x] 6.8 實作分群演算法與向量儲存
    - 建立 `app/pattern_analyzer/clusterer.py`，整合 K-Means / HDBSCAN（自動決定群數）
    - 將 `SemanticVector`（含 `cluster_label`）儲存至 Qdrant 向量資料庫
    - 確保 `cluster_label` 為非空字串
    - _需求：2.4_

  - [x]* 6.9 撰寫屬性測試：分群標籤完整性
    - **屬性 8：分群標籤完整性**
    - **驗證需求：2.4**

  - [x] 6.10 串接 Pattern_Analyzer 完整分析流程並觸發 Prediction_Layer 更新
    - 建立 `app/pattern_analyzer/analyzer.py`，串接語言偵測 → 嵌入 → 關鍵詞 → 心理特徵 → 分群 → 儲存
    - 分析完成後發送事件通知 Prediction_Layer
    - 實作 `POST /v1/analyze`（內部端點）
    - _需求：2.1、2.2、2.3、2.4_

- [x] 7. 實作 Prediction_Layer（趨勢預測與異常偵測模組）
  - [x] 7.1 實作時間序列分析與異常偵測排程
    - 建立 `app/prediction_layer/scheduler.py`，使用 APScheduler 設定每 24 小時執行一次
    - 建立 `app/prediction_layer/analyzer.py`，載入最新語意向量批次，執行 ARIMA / Prophet 趨勢分析
    - 整合 `pyod` Isolation Forest / LOF 進行異常偵測
    - _需求：3.1_

  - [x] 7.2 實作預警事件生成與通知
    - 建立 `app/prediction_layer/alerting.py`
    - 偵測到異常時生成 `AlertEvent`，包含風險等級（高/中/低）與觸發特徵描述
    - 實作 WebSocket 推播通知已訂閱的 Operator（5 分鐘內送達）
    - _需求：3.2、3.3_

  - [x]* 7.3 撰寫屬性測試：預警事件結構完整性
    - **屬性 10：預警事件結構完整性**
    - **驗證需求：3.2**

  - [x] 7.4 實作 Risk_Vector 生成與儲存
    - 建立 `app/prediction_layer/risk_vector.py`
    - 生成包含高風險語意特徵、詐騙類群標籤、風險分數（0.0~1.0）、風險等級、時間範圍、版本號的 `RiskVector`
    - 儲存至 PostgreSQL，同步更新 Redis 快取
    - _需求：3.6_

  - [x]* 7.5 撰寫屬性測試：Risk_Vector 結構不變量
    - **屬性 13：Risk_Vector 結構不變量**
    - **驗證需求：3.6**

  - [x] 7.6 實作預測準確率計算與真實報案資料比對
    - 實作 `calculate_accuracy(predictions, actuals)` 函數，結果應在 [0.0, 1.0] 閉區間
    - 將比對結果記錄至系統日誌
    - _需求：3.4_

  - [x]* 7.7 撰寫屬性測試：準確率計算範圍不變量
    - **屬性 11：準確率計算範圍不變量**
    - **驗證需求：3.4**

  - [x] 7.8 實作報案資料格式驗證（拒絕不符規範批次）
    - 實作 `validate_case_report_batch(data)` 函數，驗證必要欄位與資料型別
    - 格式不符時拒絕整批資料，回傳包含具體錯誤說明的回應
    - _需求：3.5_

  - [x]* 7.9 撰寫屬性測試：格式不符資料拒絕
    - **屬性 12：格式不符資料拒絕**
    - **驗證需求：3.5**

- [x] 8. 檢查點：確認所有測試通過，如有問題請向使用者提問

- [x] 9. 實作真實報案資料匯入與模型微調（需求 7）
  - [x] 9.1 實作 CSV / JSON 格式報案資料匯入
    - 建立 `app/data_import/importer.py`，支援 CSV 與 JSON 格式解析
    - 實作 `POST /v1/data/import` 端點，回傳匯入批次 ID
    - _需求：7.1_

  - [x] 9.2 實作 PII 去識別化處理
    - 建立 `app/data_import/pii_remover.py`
    - 在資料進入分析流程前，自動偵測並移除姓名、電話、身分證字號、地址、電子郵件等 PII
    - 設定 `pii_removed: True` 標記
    - _需求：7.3_

  - [x]* 9.3 撰寫屬性測試：PII 去識別化
    - **屬性 22：PII 去識別化**
    - **驗證需求：7.3**

  - [x] 9.4 實作模型增量微調與版本管理
    - 建立 `app/prediction_layer/model_manager.py`
    - 實作 `fine_tune(batch_id)` 函數，使用新資料執行增量微調，記錄 `ModelVersion`（含微調前後準確率）
    - 實作 `rollback(version_id)` 函數，將 `is_active` 切換至指定版本
    - _需求：7.2、7.4_

  - [x]* 9.5 撰寫屬性測試：模型版本回滾（Round-Trip）
    - **屬性 23：模型版本回滾（Round-Trip）**
    - **驗證需求：7.4**

  - [x] 9.6 實作微調完成通知與摘要報告
    - 微調完成後通知 Operator，摘要包含 `training_data_count`、`accuracy_before`、`accuracy_after`、`new_cluster_count`
    - _需求：7.5_

  - [x]* 9.7 撰寫屬性測試：微調摘要報告完整性
    - **屬性 24：微調摘要報告完整性**
    - **驗證需求：7.5**

- [x] 10. 完成 API_Gateway 業務端點實作
  - [x] 10.1 實作 Risk_Vector 查詢端點
    - 實作 `GET /v1/risk-vectors`（支援時間範圍篩選）與 `GET /v1/risk-vectors/{id}`
    - 回應僅包含 `RiskVector` 欄位，不得包含 `ScamScript.content`
    - 目標回應時間 < 500ms（使用 Redis 快取）
    - _需求：5.1、5.2、5.5_

  - [x]* 10.2 撰寫屬性測試：Scam_Script 內容不外洩
    - **屬性 17：Scam_Script 內容不外洩**
    - **驗證需求：5.5、6.3**

  - [x] 10.3 實作預警事件查詢端點
    - 實作 `GET /v1/predictions/alerts`，回傳預警事件列表
    - _需求：3.2、5.1_

- [x] 11. 實作 Dashboard（Streamlit 視覺化儀表板）
  - [x] 11.1 實作熱詞排行榜頁面
    - 建立 `app/dashboard/pages/hotwords.py`
    - 從 Redis 快取讀取前 20 高頻詐騙熱詞，每 24 小時自動更新
    - 實作 `compute_hotword_ranking(keyword_freq)` 函數，按頻率降序排列，長度 <= 20
    - _需求：4.1_

  - [x]* 11.2 撰寫屬性測試：熱詞排行榜排序正確性
    - **屬性 14：熱詞排行榜排序正確性**
    - **驗證需求：4.1**

  - [x] 11.3 實作沙盤推演介面
    - 建立 `app/dashboard/pages/sandbox.py`
    - 提供情境參數輸入表單，呼叫後端 `/v1/scam/generate` 並顯示預測結果
    - _需求：4.2_

  - [x] 11.4 實作受害風險地圖頁面
    - 建立 `app/dashboard/pages/risk_map.py`
    - 依年齡層、地區維度呈現 Risk_Vector 輸出的風險指數
    - _需求：4.3_

  - [x] 11.5 實作快取降級與載入效能
    - 頁面初始載入使用 Redis 快取，目標 < 3 秒
    - 後端不可用時顯示最後一次成功載入的快取資料，並標示資料更新時間
    - _需求：4.4、4.5_

- [x] 12. 最終檢查點：確認所有測試通過，如有問題請向使用者提問

## 備註

- 標記 `*` 的子任務為選填，可在 MVP 階段跳過以加速交付
- 每個任務皆引用具體需求條款以確保可追溯性
- 屬性測試使用 `hypothesis` 框架，每個屬性最少執行 100 次迭代
- 單元測試聚焦於整合點（LLM mock）、具體範例（CSV/JSON 匯入）與邊緣案例
- 所有屬性測試標記格式：`# Feature: ai-scam-evolution-prediction, Property {N}: {property_text}`
