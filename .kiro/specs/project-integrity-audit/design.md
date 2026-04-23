# 專案完整性審查 Bugfix 設計文件

## Overview

本設計文件針對「AI 詐騙進化預測系統（ScamOracle）」完整性審查中發現的 14 個缺陷，制定系統性的修復方案。這些缺陷涵蓋安全漏洞（API 金鑰洩露、RBAC 繞過）、假資料使用（隨機生成預警、硬編碼統計）、模組串接斷裂（排程器未啟動、資料未持久化、缺少 API 端點）、架構違規（直接呼叫私有函數、事件迴圈衝突）以及資料不完整（進化時間軸缺少類型、年齡層匹配失敗）等面向。

修復策略遵循最小變更原則：優先修復安全漏洞與資料完整性問題，同時確保現有 348 個單元測試全部通過。

## Glossary

- **Bug_Condition (C)**: 觸發缺陷的條件 — 系統在特定輸入或狀態下產生不正確行為
- **Property (P)**: 修復後的預期正確行為
- **Preservation**: 修復不應影響的現有正確行為（348 個單元測試、Dashboard 頁面顯示、API 端點回應格式）
- **`_VALID_API_KEYS`**: `api_key.py` 中硬編碼的測試用 API 金鑰字典
- **`MOCK_RISK_VECTORS`**: `streamlit_app.py` 中基於真實統計計算的風險向量資料（變數名稱具誤導性）
- **`EVOLUTION_TIMELINE`**: `threat_monitor.py` 中的詐騙話術進化時間軸資料字典
- **`AlertingService`**: `alerting.py` 中的預警服務類別，使用 in-memory 儲存
- **`PredictionScheduler`**: `scheduler.py` 中的排程器，負責每 24 小時執行分析
- **`PatternAnalyzer`**: `analyzer.py` 中的完整分析流程串接類別

## Bug Details

### Bug Condition

系統在以下 14 種條件下表現出缺陷行為，可歸類為五大類：

**A. 安全漏洞（1.1, 1.4, 1.14）**
- `.env` 包含真實 API 金鑰
- API 金鑰驗證使用硬編碼測試值
- RBAC 驗證信任請求 body 中的自我聲明角色

**B. 假資料 / 隨機資料（1.2, 1.3, 1.10）**
- 威脅監控使用 `random` 生成假預警
- 風險向量使用誤導性變數名稱與簡化公式
- 預警 API 永遠回傳空列表

**C. 模組串接斷裂（1.5, 1.11, 1.12, 1.13）**
- 所有儲存為 in-memory，未連接外部服務
- 缺少完整分析流程的 API 端點
- 排程器未在啟動時啟動
- 匯入資料未持久化

**D. 架構違規（1.6, 1.7）**
- Dashboard 直接 import 私有函數繞過 API Gateway
- `asyncio.run()` 在 Streamlit 環境中可能衝突

**E. 資料不完整（1.8, 1.9）**
- 進化時間軸僅有 2 種詐騙類型
- 年齡層匹配邏輯不一致

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type SystemOperation
  OUTPUT: boolean

  RETURN (input.type == "env_file_access" AND containsRealApiKeys(input.envFile))
         OR (input.type == "api_request" AND usesHardcodedKeys(input.apiKeyValidation))
         OR (input.type == "threat_monitor_access" AND usesRandomData(input.alertGeneration))
         OR (input.type == "risk_vector_display" AND usesMislabeledMockData(input.dataSource))
         OR (input.type == "data_persistence" AND isInMemoryOnly(input.storage))
         OR (input.type == "dashboard_llm_call" AND importsPrivateFunction(input.importPath))
         OR (input.type == "async_call" AND usesAsyncioRun(input.eventLoopHandling))
         OR (input.type == "evolution_timeline" AND missingScamTypes(input.timelineData))
         OR (input.type == "risk_map_compute" AND ageGroupMismatch(input.matchingLogic))
         OR (input.type == "alerts_api" AND alertStoreEmpty(input.alertingService))
         OR (input.type == "pattern_analysis" AND missingApiEndpoint(input.apiRoutes))
         OR (input.type == "scheduler_start" AND schedulerNotStarted(input.lifespan))
         OR (input.type == "data_import" AND cleanedDataNotPersisted(input.importFlow))
         OR (input.type == "rbac_check" AND trustsRequestBody(input.authSource))
END FUNCTION
```

### Examples

- **1.1**: `.env` 檔案包含 `OPENAI_API_KEY=sk-proj-VzxfS...`（真實金鑰），應為佔位符
- **1.2**: `generate_live_alerts()` 呼叫 `random.choice(scam_types)` 生成假預警，每次刷新結果不同
- **1.4**: `_VALID_API_KEYS` 字典包含 `"test-key-001"` 等硬編碼值，生產環境無法動態管理
- **1.6**: `streamlit_app.py` 第 570 行 `from app.scam_engine.generator import _build_llm_client, _call_llm_with_retry`
- **1.8**: `EVOLUTION_TIMELINE` 只有 `"假冒銀行客服"` 和 `"投資詐騙"` 兩個 key
- **1.9**: `compute_risk_index()` 用 `age_group in target` 比對，但 `"45-59歲" in "中老年族群"` 為 False
- **1.12**: `main.py` 的 `lifespan()` 函數中只有 log 訊息，沒有呼叫 `get_scheduler().start()`

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Dashboard「系統總覽」頁面正確顯示 `taiwan_scam_data.py` 的真實統計數據
- XAI 話術分析頁面的 `XAIHighlighter` 高亮功能正常運作
- 熱詞排行榜正確顯示 `REAL_HOTWORDS` 資料
- 沙盤推演頁面的 `run_sandbox_simulation()` 正常執行
- `GET /v1/health` 不需要 API 金鑰驗證
- 所有 348 個現有單元測試全部通過
- 模型準確率評估頁面正常運作
- `PiiRemover.remove_from_batch()` 正確執行 PII 去識別化
- `PatternAnalyzer` 完整分析流程正常運作
- 缺少 `X-API-Key` 標頭的請求回傳 HTTP 401

**Scope:**
所有不涉及上述 14 個缺陷的功能應完全不受修復影響。修復應採用最小變更原則，避免大規模重構。

## Hypothesized Root Cause

基於程式碼分析，各缺陷的根本原因如下：

1. **安全意識不足（1.1）**: `.env` 檔案在開發過程中被填入真實金鑰，雖然 `.gitignore` 已包含規則，但檔案內容未被清理

2. **原型開發殘留（1.2, 1.3, 1.4, 1.5, 1.10）**: 系統處於原型階段，使用 in-memory 儲存和假資料作為佔位符，但未在後續開發中替換為真實實作

3. **架構分層未嚴格執行（1.6）**: Dashboard 為了快速實現功能，直接 import 了 `generator.py` 的私有函數 `_build_llm_client` 和 `_call_llm_with_retry`，繞過了 API Gateway 層

4. **Streamlit 事件迴圈不相容（1.7）**: 開發者使用 `asyncio.run()` 呼叫非同步函數，未考慮 Streamlit 已有自己的事件迴圈

5. **資料不完整（1.8）**: `EVOLUTION_TIMELINE` 只實作了兩種詐騙類型的時間軸資料，其餘五種未補齊

6. **資料模型不一致（1.9）**: `MOCK_RISK_VECTORS` 的 `target_audience` 使用描述性文字（如「中老年族群」），而 `VALID_AGE_GROUPS` 使用年齡範圍格式（如「45-59歲」），兩者無法直接匹配

7. **啟動流程遺漏（1.12）**: `main.py` 的 `lifespan` 函數中忘記呼叫排程器啟動

8. **資料流斷裂（1.13）**: `data.py` 執行了 PII 去識別化但未將結果儲存

9. **認證設計缺陷（1.14）**: RBAC 驗證從請求 body 取得角色資訊，而非從認證 token 中提取

## Correctness Properties

Property 1: Bug Condition - 安全漏洞修復

_For any_ 系統狀態 where `.env` 檔案被存取、API 金鑰被驗證、或 RBAC 權限被檢查，修復後的系統 SHALL 確保 `.env` 不包含真實金鑰、API 金鑰從環境變數或資料庫載入、且操作人員身份從認證中介軟體取得而非信任請求 body。

**Validates: Requirements 2.1, 2.4, 2.14**

Property 2: Bug Condition - 資料真實性修復

_For any_ 使用者存取威脅監控頁面、風險向量資料、或預警 API 時，修復後的系統 SHALL 使用基於真實統計數據或 Prediction Layer 分析結果的資料，而非 `random` 生成的假資料或空列表。

**Validates: Requirements 2.2, 2.3, 2.10**

Property 3: Bug Condition - 模組串接修復

_For any_ 系統啟動、資料匯入、或分析請求時，修復後的系統 SHALL 正確啟動排程器、持久化匯入資料、並提供完整分析流程的 API 端點。

**Validates: Requirements 2.5, 2.11, 2.12, 2.13**

Property 4: Bug Condition - 架構合規修復

_For any_ Dashboard 頁面需要呼叫 LLM 服務時，修復後的系統 SHALL 透過 API Gateway 端點呼叫，而非直接 import 私有函數，且使用安全的事件迴圈處理方式。

**Validates: Requirements 2.6, 2.7**

Property 5: Bug Condition - 資料完整性修復

_For any_ 使用者存取進化時間軸頁面或風險地圖時，修復後的系統 SHALL 提供所有 7 種詐騙類型的時間軸資料，且年齡層匹配邏輯正確運作。

**Validates: Requirements 2.8, 2.9**

Property 6: Preservation - 現有功能不受影響

_For any_ 不涉及上述缺陷的操作（Dashboard 總覽、XAI 分析、熱詞排行、沙盤推演、健康檢查、PII 去識別化、PatternAnalyzer 分析流程），修復後的系統 SHALL 產生與修復前完全相同的行為，所有 348 個現有單元測試全部通過。

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10**

## Fix Implementation

### Changes Required

以下按優先順序列出各缺陷的具體修復方案：

---

### Fix 1.1: `.env` 金鑰洩露修復

**File**: `.env`

**Specific Changes**:
1. **替換真實金鑰為佔位符**: 將 `OPENAI_API_KEY` 值替換為 `sk-your-openai-api-key-here`，將 `GOOGLE_API_KEY` 值替換為 `your-google-api-key-here`
2. **確認 `.gitignore`**: 驗證 `.env` 已在 `.gitignore` 中（已確認存在）
3. **金鑰撤銷提醒**: 在 `.env` 檔案頂部加入註解，提醒已洩露的金鑰應立即撤銷

---

### Fix 1.2: 威脅監控假資料修復

**File**: `app/dashboard/pages/threat_monitor.py`

**Specific Changes**:
1. **重寫 `generate_live_alerts()`**: 移除 `random.choice()` 和 `random.randint()`，改為基於 `taiwan_scam_data.py` 的真實統計數據生成確定性的預警事件。使用 `SCAM_TYPE_STATS` 的案件數和趨勢資料計算風險分數
2. **重寫 `get_current_threat_summary()`**: 移除硬編碼的假統計數據，改為基於 `SCAM_TYPE_STATS`、`MONTHLY_TREND` 等真實資料動態計算威脅摘要
3. **移除 `import random`**: 確保不再使用隨機數生成

---

### Fix 1.3: 風險向量變數名稱與計算邏輯修復

**File**: `app/dashboard/streamlit_app.py`

**Specific Changes**:
1. **重命名變數**: 將 `MOCK_RISK_VECTORS` 重命名為 `COMPUTED_RISK_VECTORS`，反映其基於真實統計計算的本質
2. **改進計算邏輯**: 使用更精確的風險分數計算公式，考慮案件數佔比、平均損失佔比、趨勢權重等多維度因素
3. **加入資料來源註解**: 明確標註資料來源為 `taiwan_scam_data.py` 的真實統計

---

### Fix 1.4: API 金鑰驗證改進

**File**: `app/api_gateway/middleware/api_key.py`

**Specific Changes**:
1. **從環境變數載入金鑰**: 新增 `_load_api_keys_from_env()` 函數，從環境變數 `API_KEYS` 載入 JSON 格式的金鑰配置
2. **保留 fallback 機制**: 若環境變數未設定，fallback 到現有硬編碼金鑰（僅限 development 環境）
3. **加入環境檢查**: 在 production 環境中，若使用硬編碼金鑰則記錄警告日誌

---

### Fix 1.5: 儲存層抽象化

**Files**: 多個檔案

**Specific Changes**:
1. **建立儲存抽象介面**: 在各模組中加入明確的註解與環境切換邏輯，標示 in-memory 實作僅用於 development/testing
2. **加入環境檢查**: 在 production 環境中記錄警告，提示應切換至真實資料庫連線
3. **保持向後相容**: 不改變現有 in-memory 實作的介面，確保測試通過

---

### Fix 1.6: Dashboard LLM 呼叫架構修復

**File**: `app/dashboard/streamlit_app.py`

**Specific Changes**:
1. **建立 API 客戶端函數**: 新增 `_call_api_gateway(endpoint, payload)` 輔助函數，透過 `httpx` 或 `requests` 呼叫 API Gateway
2. **替換私有函數 import**: 在「詐騙對話模擬器」頁面中，將 `from app.scam_engine.generator import _build_llm_client, _call_llm_with_retry` 替換為透過 API Gateway 的 `/v1/scam/generate` 端點呼叫
3. **加入 API Gateway URL 設定**: 從環境變數 `API_GATEWAY_URL` 讀取後端 URL

---

### Fix 1.7: 非同步呼叫修復

**File**: `app/dashboard/streamlit_app.py`

**Specific Changes**:
1. **引入 `nest_asyncio`**: 在檔案頂部加入 `import nest_asyncio; nest_asyncio.apply()`，解決 Streamlit 事件迴圈衝突
2. **替換 `asyncio.run()`**: 將所有 `asyncio.run()` 呼叫替換為安全的事件迴圈處理方式，使用 `asyncio.get_event_loop().run_until_complete()` 搭配 `nest_asyncio`
3. **加入錯誤處理**: 包裝非同步呼叫，捕獲 `RuntimeError` 並提供友善的錯誤訊息

---

### Fix 1.8: 進化時間軸資料補齊

**File**: `app/dashboard/pages/threat_monitor.py`

**Specific Changes**:
1. **補齊 5 種詐騙類型**: 在 `EVOLUTION_TIMELINE` 字典中新增「假冒政府機關」、「愛情詐騙」、「購物詐騙」、「中獎詐騙」、「工作詐騙」的 2021-2024 進化時間軸資料
2. **資料一致性**: 確保新增資料的結構與現有兩種類型一致（year, keywords, method, avg_loss, cases, new_tactic）
3. **數據合理性**: 基於 `SCAM_TYPE_STATS` 的真實統計趨勢推算各年度數據

---

### Fix 1.9: 年齡層匹配邏輯修復

**File**: `app/dashboard/pages/risk_map.py`

**Specific Changes**:
1. **建立年齡層映射表**: 新增 `AGE_GROUP_MAPPING` 字典，將描述性文字（如「中老年族群」）映射到 `VALID_AGE_GROUPS` 的年齡範圍
2. **修改 `compute_risk_index()`**: 使用映射表進行匹配，而非簡單的字串包含檢查
3. **加入映射邏輯**: `"中老年族群" → ["45-59歲", "60歲以上"]`、`"年輕族群" → ["18-29歲", "18歲以下"]`、`"一般民眾" → 所有年齡層`

---

### Fix 1.10: 預警 API 資料填充

**File**: `app/api_gateway/routers/predictions.py`

**Specific Changes**:
1. **啟動時填充種子資料**: 在 `_alerting_service` 初始化後，基於 `taiwan_scam_data.py` 的真實統計生成初始預警事件
2. **連接排程器**: 確保 `PredictionScheduler` 分析完成後，將結果寫入 `AlertingService`
3. **提供 fallback**: 若無分析結果，基於真實統計數據生成基準預警

---

### Fix 1.11: 新增完整分析 API 端點

**File**: 新增 `app/api_gateway/routers/analyze.py`（若不存在則擴充）

**Specific Changes**:
1. **新增 `POST /v1/analyze/batch` 端點**: 接受 ScamScript 列表，觸發 `PatternAnalyzer.analyze_batch()` 完整分析流程
2. **回應格式**: 回傳分析結果摘要（關鍵詞、心理標籤、分群標籤），不暴露原始嵌入向量
3. **掛載路由**: 在 `main.py` 中掛載新路由

---

### Fix 1.12: 排程器啟動修復

**File**: `app/api_gateway/main.py`

**Specific Changes**:
1. **在 lifespan 中啟動排程器**: 在 `yield` 之前加入 `get_scheduler().start()`
2. **在關閉時停止排程器**: 在 `yield` 之後加入 `get_scheduler().stop()`
3. **加入錯誤處理**: 包裝排程器啟動，避免排程器失敗導致整個應用程式無法啟動

---

### Fix 1.13: 匯入資料持久化

**File**: `app/api_gateway/routers/data.py`

**Specific Changes**:
1. **建立 in-memory 儲存**: 新增模組層級的 `_imported_records_store` 列表，儲存清理後的資料
2. **儲存清理後資料**: 在 PII 去識別化後，將 `cleaned_records` 存入儲存
3. **提供查詢介面**: 新增 `get_imported_records_store()` 函數供其他模組存取

---

### Fix 1.14: RBAC 認證來源修復

**File**: `app/api_gateway/routers/scam.py`

**Specific Changes**:
1. **從請求標頭取得身份**: 將 `operator_id` 和 `operator_role` 的來源從請求 body 改為 HTTP 標頭（`X-Operator-Id`、`X-Operator-Role`）
2. **使用 `require_role` 依賴注入**: 利用 `rbac.py` 已有的 `require_role()` 裝飾器進行角色驗證
3. **保留 body 欄位向後相容**: `ScamGenerateRequest` 中的 `operator_id` 和 `operator_role` 改為 Optional，優先使用標頭值

## Testing Strategy

### Validation Approach

測試策略分為三階段：首先在未修復程式碼上執行探索性測試確認缺陷存在，然後實施修復，最後驗證修復正確性並確保現有行為不受影響。

### Exploratory Bug Condition Checking

**Goal**: 在實施修復前，確認所有 14 個缺陷確實存在，並驗證根因分析的正確性。

**Test Plan**: 撰寫針對每個缺陷的測試案例，在未修復程式碼上執行以觀察失敗模式。

**Test Cases**:
1. **`.env` 金鑰檢查**: 讀取 `.env` 檔案，驗證是否包含真實 API 金鑰模式（will fail on unfixed code）
2. **威脅監控隨機性測試**: 連續呼叫 `generate_live_alerts()` 兩次，比較結果是否不同（will fail on unfixed code — 結果會不同因為使用 random）
3. **API 金鑰硬編碼測試**: 檢查 `_VALID_API_KEYS` 是否包含硬編碼值（will fail on unfixed code）
4. **進化時間軸完整性測試**: 檢查 `EVOLUTION_TIMELINE` 是否包含所有 7 種詐騙類型（will fail on unfixed code）
5. **年齡層匹配測試**: 呼叫 `compute_risk_index()` 並驗證「中老年族群」與「45-59歲」能正確匹配（will fail on unfixed code）
6. **排程器啟動測試**: 檢查 lifespan 函數是否呼叫 `get_scheduler().start()`（will fail on unfixed code）

**Expected Counterexamples**:
- `.env` 包含 `sk-proj-` 開頭的真實 OpenAI 金鑰
- `generate_live_alerts()` 每次呼叫產生不同結果
- `EVOLUTION_TIMELINE.keys()` 只有 2 個元素而非 7 個
- `compute_risk_index(vectors, "45-59歲", "台北市")` 回傳 0.0（因為匹配失敗）

### Fix Checking

**Goal**: 驗證修復後，所有 14 個缺陷條件下系統產生正確行為。

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := fixedSystem(input)
  ASSERT expectedBehavior(result)
END FOR
```

### Preservation Checking

**Goal**: 驗證修復不影響現有正確行為。

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalSystem(input) = fixedSystem(input)
END FOR
```

**Testing Approach**: Property-based testing 適用於 preservation checking，因為：
- 可自動生成大量測試案例覆蓋非缺陷輸入空間
- 能捕獲手動測試可能遺漏的邊界案例
- 提供強保證確保行為在所有非缺陷輸入下不變

**Test Plan**: 先在未修復程式碼上觀察正常行為，再撰寫 property-based tests 確保修復後行為一致。

**Test Cases**:
1. **Dashboard 總覽 Preservation**: 驗證 `SCAM_TYPE_STATS` 資料在修復前後顯示一致
2. **XAI 分析 Preservation**: 驗證 `XAIHighlighter.highlight()` 在修復前後對相同輸入產生相同結果
3. **健康檢查 Preservation**: 驗證 `GET /v1/health` 在修復前後回傳相同格式
4. **PII 去識別化 Preservation**: 驗證 `PiiRemover.remove_from_batch()` 在修復前後行為一致

### Unit Tests

- 測試 `.env` 檔案不包含真實 API 金鑰模式
- 測試 `generate_live_alerts()` 回傳基於真實資料的確定性結果
- 測試 `get_current_threat_summary()` 回傳基於真實統計的摘要
- 測試 `compute_risk_index()` 正確匹配年齡層描述與年齡範圍
- 測試 `EVOLUTION_TIMELINE` 包含所有 7 種詐騙類型
- 測試 API 金鑰驗證支援環境變數載入
- 測試排程器在 lifespan 中正確啟動與停止
- 測試匯入資料在 PII 去識別化後被儲存
- 測試 RBAC 驗證從標頭取得操作人員身份

### Property-Based Tests

- 生成隨機文本輸入，驗證 `XAIHighlighter.highlight()` 在修復前後行為一致
- 生成隨機風險向量資料，驗證 `compute_risk_index()` 使用映射表後回傳合理的風險指數（0.0 ~ 1.0）
- 生成隨機 API 請求，驗證缺少 `X-API-Key` 標頭時一律回傳 401
- 生成隨機 PII 資料，驗證 `PiiRemover` 在修復前後去識別化行為一致

### Integration Tests

- 測試完整的 API Gateway 啟動流程（lifespan → 排程器啟動 → 路由掛載）
- 測試資料匯入完整流程（上傳 → PII 去識別化 → 儲存 → 可查詢）
- 測試 Dashboard 透過 API Gateway 呼叫 LLM 的完整流程
- 測試預警 API 在排程器執行分析後回傳非空結果
