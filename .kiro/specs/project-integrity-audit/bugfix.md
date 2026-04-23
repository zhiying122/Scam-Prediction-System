# Bugfix Requirements Document

## Introduction

本文件記錄對「AI 詐騙進化預測系統（ScamOracle）」進行全面完整性審查後發現的所有問題。這些問題涵蓋安全漏洞、假資料使用、模組串接斷裂、架構違規等多個面向。系統雖然所有 348 個單元測試通過，但缺乏端對端整合測試，導致多個模組之間的串接問題未被發現。

**影響範圍：** 整個專案的功能完整性、資料真實性、安全性與架構一致性。

---

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN `.env` 檔案被提交至版本控制 THEN 系統暴露了真實的 OpenAI API Key（`sk-proj-VzxfS...`）和 Google API Key（`AIzaSyAkJytIV3DHG4OwM14VYP2VzcpbGsr8MKc`），造成嚴重安全漏洞（注意：`.gitignore` 已包含 `.env` 規則，但 `.env` 檔案中仍包含真實金鑰值而非佔位符）

1.2 WHEN 使用者進入「即時威脅監控」頁面 THEN `threat_monitor.py` 的 `generate_live_alerts()` 使用 `random.choice()` 和 `random.randint()` 生成完全隨機的假預警事件，`get_current_threat_summary()` 回傳硬編碼的假統計數據（如 `active_threats: 23`, `new_variants_24h: 7`），不是來自真實資料或 Prediction Layer 的分析結果

1.3 WHEN `streamlit_app.py` 計算風險向量資料 THEN 使用名為 `MOCK_RISK_VECTORS` 的變數，且計算邏輯為簡化的近似公式（`risk_score = min(0.95, stats["cases"] / 20000 + stats["avg_loss_ntd"] / 2000000)`），不是來自 Prediction Layer 的真實分析結果

1.4 WHEN API Gateway 收到帶有 `X-API-Key` 標頭的請求 THEN `api_key.py` 的 `_VALID_API_KEYS` 使用硬編碼的測試金鑰（`test-key-001`, `test-key-002`）進行驗證，而非從資料庫查詢，在生產環境中不安全

1.5 WHEN 系統需要持久化儲存資料 THEN 所有資料儲存都是 in-memory 實作（`_scam_scripts_store: list = []`、in-memory `RiskVectorRepository`、in-memory `SlidingWindowCounter`、`self._alert_store: list = []`、in-memory audit log），雖然 `docker-compose.yml` 定義了 PostgreSQL、Redis、Qdrant 服務，但程式碼中沒有任何模組真正連接這些服務

1.6 WHEN 使用者在「詐騙對話模擬器」頁面發送訊息 THEN `streamlit_app.py` 直接 import 並呼叫 `_build_llm_client` 和 `_call_llm_with_retry`（以底線開頭的私有函數），繞過 API Gateway 端點，違反架構分層原則

1.7 WHEN 使用者在「LLM 話術生成」頁面或「詐騙免疫訓練」頁面點擊生成按鈕 THEN 程式碼使用 `asyncio.run()` 呼叫非同步函數，在 Streamlit 環境中可能與 Streamlit 自身的事件迴圈衝突，導致 `RuntimeError: This event loop is already running`

1.8 WHEN 使用者在「話術進化時間軸」頁面選擇詐騙類型 THEN `EVOLUTION_TIMELINE` 字典只包含「假冒銀行客服」和「投資詐騙」兩種類型的進化時間軸資料，其他 5 種詐騙類型（假冒政府機關、愛情詐騙、購物詐騙、中獎詐騙、工作詐騙）沒有時間軸資料，無法選擇

1.9 WHEN `risk_map.py` 的 `compute_risk_index()` 嘗試匹配風險向量與年齡層 THEN 使用字串包含檢查（`age_group in target`），但 `MOCK_RISK_VECTORS` 中的 `target_audience` 欄位值（如「中老年族群」）與 `VALID_AGE_GROUPS`（如「45-59歲」）完全不匹配，導致風險指數計算不準確

1.10 WHEN 外部客戶端呼叫 `GET /v1/predictions/alerts` THEN `_alerting_service = AlertingService()` 建立了一個空的服務實例，沒有任何預警事件資料，永遠回傳空列表

1.11 WHEN 系統需要對 ScamScript 執行完整的 Pattern Analysis 流程 THEN `PatternAnalyzer.analyze()` 提供了完整的分析管線（語言偵測→嵌入→關鍵詞→心理標籤→分群），但 API Gateway 中沒有對應的端點來觸發完整分析流程，只有 XAI highlight 端點被整合

1.12 WHEN API Gateway 啟動 THEN `main.py` 的 lifespan 函數中沒有呼叫 `get_scheduler().start()`，`PredictionScheduler` 永遠不會被啟動，每 24 小時的時間序列分析與異常偵測排程不會執行

1.13 WHEN 使用者透過 `POST /v1/data/import` 匯入報案資料 THEN `data.py` 執行了 PII 去識別化（`_pii_remover.remove_from_batch(result.records)`），但清理後的資料 `cleaned_records` 沒有被儲存到任何持久化儲存，只是回傳了計數

1.14 WHEN 使用者透過 `POST /v1/scam/generate` 觸發話術生成 THEN `scam.py` 從請求 body 中取得 `operator_id` 和 `operator_role` 進行 RBAC 驗證，而非從認證 token 或 session 中取得，任何人都可以聲稱自己是管理員角色

### Expected Behavior (Correct)

2.1 WHEN `.env` 檔案存在於專案中 THEN 系統 SHALL 確保 `.env` 檔案只包含佔位符值（如 `sk-your-openai-api-key-here`），真實金鑰不應出現在版本控制中，且已洩露的金鑰應立即撤銷並重新生成

2.2 WHEN 使用者進入「即時威脅監控」頁面 THEN 系統 SHALL 從 Prediction Layer 的 `AlertingService` 取得真實的預警事件資料，或至少基於 `taiwan_scam_data.py` 中的真實統計數據計算威脅摘要，而非使用 `random` 生成假資料

2.3 WHEN `streamlit_app.py` 計算風險向量資料 THEN 系統 SHALL 透過 API Gateway 的 `/v1/risk-vectors` 端點取得風險向量資料，或至少將變數名稱從 `MOCK_RISK_VECTORS` 改為反映其真實來源的名稱，並使用更精確的計算邏輯

2.4 WHEN API Gateway 收到帶有 `X-API-Key` 標頭的請求 THEN 系統 SHALL 從 PostgreSQL 資料庫查詢 API 金鑰的有效性，或至少從環境變數載入金鑰，而非使用硬編碼的測試金鑰

2.5 WHEN 系統需要持久化儲存資料 THEN 系統 SHALL 連接 `docker-compose.yml` 中定義的 PostgreSQL、Redis、Qdrant 服務進行資料持久化，或至少提供明確的抽象層與切換機制，使 in-memory 實作僅用於測試環境

2.6 WHEN 使用者在「詐騙對話模擬器」頁面發送訊息 THEN 系統 SHALL 透過 API Gateway 的端點（如 `/v1/scam/generate`）呼叫 LLM 服務，而非直接 import 私有函數，以遵守架構分層原則

2.7 WHEN Dashboard 頁面需要呼叫非同步函數 THEN 系統 SHALL 使用 `asyncio.get_event_loop().run_until_complete()` 或 `nest_asyncio` 等方式安全地在 Streamlit 環境中執行非同步程式碼，避免事件迴圈衝突

2.8 WHEN 使用者在「話術進化時間軸」頁面選擇詐騙類型 THEN 系統 SHALL 提供所有 7 種詐騙類型（假冒銀行客服、投資詐騙、假冒政府機關、愛情詐騙、購物詐騙、中獎詐騙、工作詐騙）的進化時間軸資料

2.9 WHEN `risk_map.py` 的 `compute_risk_index()` 匹配風險向量與年齡層 THEN 系統 SHALL 使用一致的年齡層分類標準，確保 `target_audience` 欄位值與 `VALID_AGE_GROUPS` 能正確匹配，或建立明確的映射關係

2.10 WHEN 外部客戶端呼叫 `GET /v1/predictions/alerts` THEN 系統 SHALL 回傳由 Prediction Layer 分析產生的真實預警事件，`AlertingService` 應在系統啟動時或排程分析後被填充資料

2.11 WHEN 系統需要對 ScamScript 執行完整的 Pattern Analysis 流程 THEN 系統 SHALL 在 API Gateway 中提供對應的端點（如 `POST /v1/analyze/full`）來觸發 `PatternAnalyzer.analyze_batch()` 完整分析流程

2.12 WHEN API Gateway 啟動 THEN 系統 SHALL 在 lifespan 函數中呼叫 `get_scheduler().start()` 啟動預測分析排程器，並在關閉時呼叫 `get_scheduler().stop()` 停止排程器

2.13 WHEN 使用者透過 `POST /v1/data/import` 匯入報案資料 THEN 系統 SHALL 將 PII 去識別化後的 `cleaned_records` 儲存至持久化儲存（PostgreSQL），並觸發後續的模型增量微調流程

2.14 WHEN 使用者透過 `POST /v1/scam/generate` 觸發話術生成 THEN 系統 SHALL 從認證 token（如 JWT）或 API Gateway 的認證中介軟體中取得操作人員身份與角色，而非信任請求 body 中的自我聲明

### Unchanged Behavior (Regression Prevention)

3.1 WHEN 使用者存取 Dashboard 的「系統總覽」頁面 THEN 系統 SHALL CONTINUE TO 正確顯示來自 `taiwan_scam_data.py` 的真實統計數據（2023 年 83,000 件、88.2 億元等）

3.2 WHEN 使用者在「XAI 話術分析」頁面輸入文字並點擊分析 THEN 系統 SHALL CONTINUE TO 使用 `XAIHighlighter` 正確高亮顯示心理操控特徵片段並列出對應標籤

3.3 WHEN 使用者在「熱詞排行榜」頁面查看資料 THEN 系統 SHALL CONTINUE TO 正確顯示來自 `REAL_HOTWORDS` 的真實熱詞統計排行

3.4 WHEN 使用者在「沙盤推演」頁面設定參數並執行推演 THEN 系統 SHALL CONTINUE TO 正確執行 `run_sandbox_simulation()` 並顯示推演結果

3.5 WHEN 外部客戶端呼叫 `GET /v1/health` THEN 系統 SHALL CONTINUE TO 回傳健康檢查結果，不需要 API 金鑰驗證

3.6 WHEN 所有 348 個現有單元測試執行 THEN 系統 SHALL CONTINUE TO 全部通過，修復不應破壞現有測試

3.7 WHEN 使用者在「模型準確率評估」頁面點擊「執行評估」THEN 系統 SHALL CONTINUE TO 使用真實詐騙話術樣本進行即時分類測試並顯示混淆矩陣

3.8 WHEN `PiiRemover.remove_from_batch()` 處理報案資料 THEN 系統 SHALL CONTINUE TO 正確執行 PII 去識別化（替換姓名、電話、身分證字號等敏感資訊）

3.9 WHEN `PatternAnalyzer` 對支援語言的文本執行分析 THEN 系統 SHALL CONTINUE TO 正確完成語言偵測→語意嵌入→TF-IDF 關鍵詞提取→心理特徵分類→分群的完整流程

3.10 WHEN API Gateway 收到缺少 `X-API-Key` 標頭的請求 THEN 系統 SHALL CONTINUE TO 回傳 HTTP 401 錯誤，不執行任何業務邏輯
