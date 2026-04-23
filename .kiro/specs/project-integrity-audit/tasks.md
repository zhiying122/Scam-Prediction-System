    # Implementation Plan

- [x] 1. 撰寫 Bug Condition 探索性測試（修復前執行）
  - **Property 1: Bug Condition** - 專案完整性 14 項缺陷驗證
  - **CRITICAL**: 此測試必須在實施修復前撰寫並執行 — 測試失敗代表缺陷確實存在
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: 此測試編碼了預期正確行為 — 修復後測試通過即代表缺陷已修復
  - **GOAL**: 產生反例（counterexamples）以證明缺陷存在
  - **Scoped PBT Approach**: 針對每個缺陷的具體觸發條件撰寫確定性測試案例
  - 測試檔案：`tests/test_bug_condition_exploration.py`
  - 使用 Hypothesis 撰寫 property-based tests，涵蓋以下缺陷條件：
    - **1.1 `.env` 金鑰洩露**: 讀取 `.env` 檔案，斷言不包含 `sk-proj-` 開頭的真實 OpenAI 金鑰，不包含 `AIzaSy` 開頭的真實 Google 金鑰
    - **1.2 威脅監控隨機性**: 連續呼叫 `generate_live_alerts()` 兩次，斷言結果應相同（確定性）；呼叫 `get_current_threat_summary()`，斷言數據來自真實統計而非硬編碼
    - **1.4 API 金鑰硬編碼**: 檢查 `_VALID_API_KEYS` 是否支援從環境變數載入，而非僅有硬編碼值
    - **1.8 進化時間軸不完整**: 斷言 `EVOLUTION_TIMELINE` 包含所有 7 種詐騙類型
    - **1.9 年齡層匹配失敗**: 使用 Hypothesis 生成風險向量資料，斷言 `compute_risk_index()` 能正確匹配「中老年族群」與「45-59歲」、「60歲以上」
    - **1.10 預警 API 空列表**: 斷言 `AlertingService` 初始化後 `get_alerts()` 回傳非空列表（含種子資料）
    - **1.12 排程器未啟動**: 檢查 `lifespan` 函數是否呼叫 `get_scheduler().start()`
    - **1.13 匯入資料未持久化**: 斷言 `data.py` 在 PII 去識別化後將資料存入儲存
    - **1.14 RBAC 信任請求 body**: 斷言 `scam.py` 從 HTTP 標頭取得操作人員身份
  - 在未修復程式碼上執行測試
  - **EXPECTED OUTCOME**: 測試 FAIL（這是正確的 — 證明缺陷存在）
  - 記錄發現的反例（counterexamples）以理解根因
  - 當測試撰寫完成、執行完畢、且失敗已記錄後，標記任務完成
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.12, 1.13, 1.14_

- [x] 2. 撰寫 Preservation 保留性測試（修復前執行）
  - **Property 2: Preservation** - 現有正確行為保留驗證
  - **IMPORTANT**: 遵循觀察優先方法論（observation-first methodology）
  - 測試檔案：`tests/test_preservation_properties.py`
  - 使用 Hypothesis 撰寫 property-based tests，確保以下行為在修復前後不變：
  - **觀察步驟**（在未修復程式碼上執行）：
    - 觀察：`SCAM_TYPE_STATS` 資料結構與內容在 Dashboard 總覽頁面正確顯示
    - 觀察：`XAIHighlighter.highlight()` 對任意文字輸入產生一致的高亮結果
    - 觀察：`GET /v1/health` 回傳正確格式且不需要 API 金鑰
    - 觀察：`PiiRemover.remove_from_batch()` 對相同輸入產生相同的去識別化結果
    - 觀察：缺少 `X-API-Key` 標頭的請求回傳 HTTP 401
    - 觀察：`REAL_HOTWORDS` 資料在熱詞排行榜正確顯示
    - 觀察：`PatternAnalyzer` 完整分析流程正常運作
  - **Property-based tests**：
    - 對任意字串輸入，`XAIHighlighter.highlight()` 回傳的 spans 位置在文字範圍內，coverage_ratio 在 0.0~1.0 之間
    - 對任意風險向量資料，`compute_risk_index()` 回傳值在 0.0~1.0 之間
    - 對任意缺少 `X-API-Key` 的 API 請求，回傳 HTTP 401
    - 對任意 PII 資料，`PiiRemover` 去識別化行為一致
  - 在未修復程式碼上執行測試
  - **EXPECTED OUTCOME**: 測試 PASS（確認基準行為可被保留）
  - 當測試撰寫完成、執行完畢、且在未修復程式碼上通過後，標記任務完成
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_

- [x] 3. 修復 A 類：安全漏洞修復（Fix 1.1, 1.4, 1.14）

  - [x] 3.1 Fix 1.1 — `.env` 金鑰洩露修復
    - 將 `.env` 中 `OPENAI_API_KEY=sk-proj-VzxfS...` 替換為 `OPENAI_API_KEY=sk-your-openai-api-key-here`
    - 將 `GOOGLE_API_KEY=AIzaSyAkJytIV3DHG4OwM14VYP2VzcpbGsr8MKc` 替換為 `GOOGLE_API_KEY=your-google-api-key-here`
    - 在 `.env` 檔案頂部加入註解提醒已洩露金鑰應立即撤銷
    - _Bug_Condition: containsRealApiKeys(input.envFile) — `.env` 包含 `sk-proj-` 或 `AIzaSy` 開頭的真實金鑰_
    - _Expected_Behavior: `.env` 僅包含佔位符值_
    - _Preservation: `.env.example` 格式不變_
    - _Requirements: 2.1_

  - [x] 3.2 Fix 1.4 — API 金鑰驗證改進
    - 在 `app/api_gateway/middleware/api_key.py` 新增 `_load_api_keys_from_env()` 函數
    - 從環境變數 `API_KEYS` 載入 JSON 格式的金鑰配置
    - 保留 fallback 機制：若環境變數未設定，在 development 環境 fallback 到現有硬編碼金鑰
    - 在 production 環境中使用硬編碼金鑰時記錄警告日誌
    - _Bug_Condition: usesHardcodedKeys(input.apiKeyValidation) — 僅使用硬編碼 `_VALID_API_KEYS`_
    - _Expected_Behavior: 支援從環境變數載入金鑰，development 環境可 fallback_
    - _Preservation: `lookup_api_key()` 介面不變，現有測試通過_
    - _Requirements: 2.4_

  - [x] 3.3 Fix 1.14 — RBAC 認證來源修復
    - 修改 `app/api_gateway/routers/scam.py` 的 `generate_scam_scripts_endpoint()`
    - 使用 `rbac.py` 已有的 `require_role()` 依賴注入從 HTTP 標頭取得 `X-Operator-Id` 和 `X-Operator-Role`
    - `ScamGenerateRequest` 中的 `operator_id` 和 `operator_role` 改為 `Optional`，優先使用標頭值
    - _Bug_Condition: trustsRequestBody(input.authSource) — 從請求 body 取得角色_
    - _Expected_Behavior: 從 HTTP 標頭取得操作人員身份，使用 `require_role()` 驗證_
    - _Preservation: API 回應格式不變_
    - _Requirements: 2.14_

- [x] 4. 修復 B 類：假資料 / 隨機資料修復（Fix 1.2, 1.3, 1.10）

  - [x] 4.1 Fix 1.2 — 威脅監控假資料修復
    - 重寫 `app/dashboard/pages/threat_monitor.py` 的 `generate_live_alerts()`
    - 移除 `random.choice()` 和 `random.randint()`，改為基於 `taiwan_scam_data.py` 的 `SCAM_TYPE_STATS` 生成確定性預警事件
    - 重寫 `get_current_threat_summary()`，基於 `SCAM_TYPE_STATS`、`MONTHLY_TREND` 等真實資料動態計算
    - 移除 `import random`
    - _Bug_Condition: usesRandomData(input.alertGeneration) — 使用 `random` 生成假預警_
    - _Expected_Behavior: 基於真實統計數據生成確定性預警_
    - _Preservation: `THREAT_LEVELS` 字典結構不變，`EVOLUTION_TIMELINE` 現有兩種類型資料不變_
    - _Requirements: 2.2_

  - [x] 4.2 Fix 1.3 — 風險向量變數名稱與計算邏輯修復
    - 在 `app/dashboard/streamlit_app.py` 中將 `MOCK_RISK_VECTORS` 重命名為 `COMPUTED_RISK_VECTORS`
    - 改進風險分數計算公式，考慮案件數佔比、平均損失佔比、趨勢權重等多維度因素
    - 加入資料來源註解，明確標註來源為 `taiwan_scam_data.py`
    - 更新所有引用 `MOCK_RISK_VECTORS` 的位置
    - _Bug_Condition: usesMislabeledMockData(input.dataSource) — 使用誤導性變數名稱_
    - _Expected_Behavior: 變數名稱反映真實來源，計算邏輯更精確_
    - _Preservation: 風險向量資料結構（dict keys）不變_
    - _Requirements: 2.3_

  - [x] 4.3 Fix 1.10 — 預警 API 資料填充
    - 修改 `app/api_gateway/routers/predictions.py`
    - 在 `_alerting_service` 初始化後，基於 `taiwan_scam_data.py` 的真實統計生成初始種子預警事件
    - 使用 `AlertingService.create_alert_from_params()` 填充基準預警
    - _Bug_Condition: alertStoreEmpty(input.alertingService) — `get_alerts()` 永遠回傳空列表_
    - _Expected_Behavior: 系統啟動時即有基於真實統計的基準預警_
    - _Preservation: `AlertEventResponse` 回應格式不變_
    - _Requirements: 2.10_

- [x] 5. 修復 C 類：模組串接斷裂修復（Fix 1.5, 1.11, 1.12, 1.13）

  - [x] 5.1 Fix 1.5 — 儲存層抽象化
    - 在各 in-memory 儲存模組加入明確註解與環境切換邏輯
    - 標示 in-memory 實作僅用於 development/testing
    - 在 production 環境中記錄警告日誌，提示應切換至真實資料庫
    - 不改變現有 in-memory 實作的介面
    - _Bug_Condition: isInMemoryOnly(input.storage) — 所有儲存為 in-memory_
    - _Expected_Behavior: 提供明確的環境切換機制與警告_
    - _Preservation: 現有 in-memory 介面不變，所有測試通過_
    - _Requirements: 2.5_

  - [x] 5.2 Fix 1.11 — 新增完整分析 API 端點
    - 在 `app/api_gateway/routers/analyze.py` 新增 `POST /v1/analyze/batch` 端點
    - 接受 ScamScript 文本列表，觸發 `PatternAnalyzer.analyze_batch()` 完整分析流程
    - 回傳分析結果摘要（關鍵詞、心理標籤、分群標籤）
    - 確認路由已在 `main.py` 中掛載（已掛載 `analyze.router`）
    - _Bug_Condition: missingApiEndpoint(input.apiRoutes) — 缺少完整分析端點_
    - _Expected_Behavior: 提供 `POST /v1/analyze/batch` 端點觸發完整分析_
    - _Preservation: 現有 `/v1/analyze/highlight` 端點不受影響_
    - _Requirements: 2.11_

  - [x] 5.3 Fix 1.12 — 排程器啟動修復
    - 修改 `app/api_gateway/main.py` 的 `lifespan()` 函數
    - 在 `yield` 之前加入 `get_scheduler().start()`
    - 在 `yield` 之後加入 `get_scheduler().stop()`
    - 包裝排程器啟動，捕獲異常避免排程器失敗導致應用程式無法啟動
    - 加入 `from app.prediction_layer.scheduler import get_scheduler`
    - _Bug_Condition: schedulerNotStarted(input.lifespan) — lifespan 未呼叫 `start()`_
    - _Expected_Behavior: 排程器在應用程式啟動時啟動，關閉時停止_
    - _Preservation: lifespan 的日誌輸出不變_
    - _Requirements: 2.12_

  - [x] 5.4 Fix 1.13 — 匯入資料持久化
    - 修改 `app/api_gateway/routers/data.py`
    - 新增模組層級的 `_imported_records_store: list[dict] = []`
    - 在 PII 去識別化後將 `cleaned_records` 存入 `_imported_records_store`
    - 新增 `get_imported_records_store()` 函數供其他模組存取
    - _Bug_Condition: cleanedDataNotPersisted(input.importFlow) — 清理後資料未儲存_
    - _Expected_Behavior: PII 去識別化後的資料被儲存至 in-memory store_
    - _Preservation: `DataImportResponse` 回應格式不變，PII 去識別化邏輯不變_
    - _Requirements: 2.13_

- [x] 6. 修復 D 類：架構違規修復（Fix 1.6, 1.7）

  - [x] 6.1 Fix 1.6 — Dashboard LLM 呼叫架構修復
    - 在 `app/dashboard/streamlit_app.py` 新增 `_call_api_gateway(endpoint, payload)` 輔助函數
    - 使用 `httpx` 或 `requests` 透過 API Gateway 呼叫 LLM 服務
    - 從環境變數 `API_GATEWAY_URL` 讀取後端 URL（預設 `http://localhost:8000`）
    - 替換「詐騙對話模擬器」頁面中的 `from app.scam_engine.generator import _build_llm_client, _call_llm_with_retry`
    - 改為透過 `/v1/scam/generate` 端點呼叫
    - _Bug_Condition: importsPrivateFunction(input.importPath) — 直接 import 私有函數_
    - _Expected_Behavior: 透過 API Gateway 端點呼叫 LLM 服務_
    - _Preservation: 詐騙對話模擬器的使用者體驗不變_
    - _Requirements: 2.6_

  - [x] 6.2 Fix 1.7 — 非同步呼叫修復
    - 在 `app/dashboard/streamlit_app.py` 頂部加入 `import nest_asyncio; nest_asyncio.apply()`
    - 將所有 `asyncio.run()` 替換為安全的事件迴圈處理方式
    - 使用 `asyncio.get_event_loop().run_until_complete()` 搭配 `nest_asyncio`
    - 加入 `try/except RuntimeError` 錯誤處理
    - 確認 `nest_asyncio` 已加入 `requirements.txt`
    - _Bug_Condition: usesAsyncioRun(input.eventLoopHandling) — 使用 `asyncio.run()` 可能衝突_
    - _Expected_Behavior: 使用 `nest_asyncio` 安全處理事件迴圈_
    - _Preservation: LLM 話術生成與詐騙免疫訓練頁面功能不變_
    - _Requirements: 2.7_

- [x] 7. 修復 E 類：資料不完整修復（Fix 1.8, 1.9）

  - [x] 7.1 Fix 1.8 — 進化時間軸資料補齊
    - 在 `app/dashboard/pages/threat_monitor.py` 的 `EVOLUTION_TIMELINE` 中新增 5 種詐騙類型
    - 新增：「假冒政府機關」、「愛情詐騙」、「購物詐騙」、「中獎詐騙」、「工作詐騙」
    - 每種類型包含 2021-2024 四年的進化時間軸資料
    - 資料結構與現有兩種類型一致（year, keywords, method, avg_loss, cases, new_tactic）
    - 數據基於 `SCAM_TYPE_STATS` 的真實統計趨勢推算
    - _Bug_Condition: missingScamTypes(input.timelineData) — 只有 2 種類型_
    - _Expected_Behavior: 包含所有 7 種詐騙類型的進化時間軸_
    - _Preservation: 現有「假冒銀行客服」和「投資詐騙」的時間軸資料不變_
    - _Requirements: 2.8_

  - [x] 7.2 Fix 1.9 — 年齡層匹配邏輯修復
    - 在 `app/dashboard/pages/risk_map.py` 新增 `AGE_GROUP_MAPPING` 字典
    - 映射關係：`"中老年族群" → ["45-59歲", "60歲以上"]`、`"年輕族群" → ["18-29歲", "18歲以下"]`、`"一般民眾" → 所有年齡層`
    - 修改 `compute_risk_index()` 使用映射表進行匹配
    - 替換原有的 `age_group in target` 字串包含檢查
    - _Bug_Condition: ageGroupMismatch(input.matchingLogic) — 字串包含檢查無法匹配_
    - _Expected_Behavior: 使用映射表正確匹配年齡層描述與年齡範圍_
    - _Preservation: `VALID_AGE_GROUPS`、`VALID_REGIONS` 不變，`RiskMapEntry` 資料結構不變_
    - _Requirements: 2.9_

- [x] 8. 驗證 Bug Condition 探索性測試通過

  - [x] 8.1 重新執行 Bug Condition 探索性測試
    - **Property 1: Expected Behavior** - 專案完整性 14 項缺陷已修復
    - **IMPORTANT**: 重新執行任務 1 中的同一測試 — 不要撰寫新測試
    - 任務 1 的測試編碼了預期正確行為
    - 當此測試通過時，代表預期行為已滿足
    - 執行 `tests/test_bug_condition_exploration.py`
    - **EXPECTED OUTCOME**: 測試 PASS（確認缺陷已修復）
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12, 2.13, 2.14_

  - [x] 8.2 驗證 Preservation 保留性測試仍然通過
    - **Property 2: Preservation** - 現有正確行為保留驗證
    - **IMPORTANT**: 重新執行任務 2 中的同一測試 — 不要撰寫新測試
    - 執行 `tests/test_preservation_properties.py`
    - **EXPECTED OUTCOME**: 測試 PASS（確認無回歸）
    - 確認所有測試在修復後仍然通過

- [x] 9. Checkpoint — 確保所有測試通過
  - 執行完整測試套件：`pytest tests/ -v`
  - 確認所有 348 個現有單元測試通過
  - 確認 Bug Condition 探索性測試通過
  - 確認 Preservation 保留性測試通過
  - 若有問題，詢問使用者
