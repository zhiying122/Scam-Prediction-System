# 🛡️ ScamOracle — AI 詐騙進化預測系統

> 從被動防禦到主動預測 — 運用生成式 AI 構築下一代防詐護城河

---

## 目錄

- [專案簡介](#專案簡介)
- [系統架構](#系統架構)
- [環境需求](#環境需求)
- [安裝與啟動](#安裝與啟動)
- [Dashboard 功能總覽（12 個頁面）](#dashboard-功能總覽12-個頁面)
- [API 端點總覽（6 個端點）](#api-端點總覽6-個端點)
- [功能詳細使用說明](#功能詳細使用說明)
- [測試](#測試)
- [專案結構](#專案結構)
- [資料來源](#資料來源)
- [技術棧](#技術棧)
- [團隊分工](#團隊分工)

---

## 專案簡介

ScamOracle 是一套 AI 驅動的反詐騙情報平台，透過大型語言模型（LLM）逆向模擬詐騙邏輯，主動生成並預測未來可能出現的變種詐騙話術。結合 NLP 語意分析、可解釋性 AI（XAI）高亮標記、異常偵測預警，在新型詐騙大規模爆發前提前預警。

### 核心能力

| 能力 | 說明 |
|------|------|
| 🤖 LLM 話術裂變生成 | GPT-4o / Gemini / Ollama 驅動，從種子情境自動生成數百種詐騙變種話術 |
| 🔍 XAI 可解釋性分析 | 高亮顯示觸發心理操控特徵的具體片段，5 種心理標籤分類 |
| 🎯 詐騙免疫訓練 | 互動式防詐訓練，通過測驗獲得防詐免疫證書 |
| ⚡ 異常偵測預警 | Isolation Forest 時間序列分析，24 小時內偵測新興詐騙手法 |
| 🗺️ 受害風險地圖 | 依年齡層與地區呈現風險指數，精準定位高風險族群 |
| 📡 Risk Vector API | 標準化風險向量 API，可串接銀行、電信商即時防詐系統 |

### 真實資料來源

- 內政部警政署 165 反詐騙諮詢專線統計（2023-2024）
- 刑事警察局詐欺案件統計
- 金融監督管理委員會投資詐騙通報
- 2023 年全台 83,000 件詐騙案件、損失 88.2 億元

---

## 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│              Streamlit Dashboard（前端）                      │
│   12 個功能頁面 — http://localhost:8501                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP API 呼叫
┌──────────────────────────▼──────────────────────────────────┐
│              FastAPI API Gateway（後端）                      │
│   6 個 API 端點 — http://localhost:8000                       │
│   ┌──────────┬──────────┬──────────┐                        │
│   │ API Key  │ Rate     │ Request  │                        │
│   │ 驗證     │ Limit    │ Logging  │                        │
│   └──────────┴──────────┴──────────┘                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
     ┌─────────┬───────────┼───────────┬──────────┐
     ▼         ▼           ▼           ▼          ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│ Scam    ││ Pattern ││Prediction││ Data    ││ Access  │
│ Engine  ││ Analyzer││ Layer   ││ Import  ││Controller│
│ (LLM)  ││ (NLP)   ││(異常偵測)││(PII去識別)││(RBAC)  │
└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
     │         │           │
     ▼         ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│   Ollama (本地 LLM)  │  PostgreSQL  │  Redis  │  Qdrant    │
└─────────────────────────────────────────────────────────────┘
```

---

## 環境需求

| 項目 | 版本 |
|------|------|
| Python | 3.11 以上 |
| Ollama | 最新版（本地 LLM 服務） |
| Docker | 選用（PostgreSQL / Redis / Qdrant） |
| 作業系統 | Windows / macOS / Linux |

---

## 安裝與啟動

### 步驟 1：安裝 Python 依賴

```bash
pip install -r requirements.txt
```

### 步驟 2：設定環境變數

```bash
cp .env.example .env
```

編輯 `.env` 檔案，設定 LLM 提供商：

```env
# 使用 Ollama（本地免費，推薦開發用）
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b

# 或使用 OpenAI（需付費 API Key）
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-你的真實金鑰

# 或使用 Google Gemini
# LLM_PROVIDER=google
# GOOGLE_API_KEY=你的真實金鑰
```

### 步驟 3：安裝並啟動 Ollama（如果使用 Ollama）

1. 從 https://ollama.com 下載安裝 Ollama
2. 下載模型：
```bash
ollama pull llama3.1:8b
```
3. 啟動服務（通常安裝後會自動在背景執行）：
```bash
ollama serve
```
> 如果出現 `bind: Only one usage of each socket address` 表示已經在跑了，不用管。

### 步驟 4：啟動後端 API Gateway

開一個終端機：
```bash
python -m uvicorn app.api_gateway.main:app --reload --host 0.0.0.0 --port 8000
```

啟動成功後：
- API 服務：`http://localhost:8000`
- API 文件（Swagger UI）：`http://localhost:8000/docs`

### 步驟 5：啟動前端 Dashboard

開另一個終端機：
```bash
python -m streamlit run app/dashboard/streamlit_app.py
```

啟動成功後：
- Dashboard：`http://localhost:8501`（會自動開瀏覽器）

### 步驟 6（選用）：啟動 Docker 服務

如果需要 PostgreSQL / Redis / Qdrant：
```bash
docker-compose up -d
```

> 目前系統使用 in-memory 儲存，不啟動 Docker 也能正常運作。

---

## Dashboard 功能總覽（12 個頁面）

| # | 頁面 | 說明 | 需要 LLM |
|---|------|------|----------|
| 1 | 🏠 系統總覽 | 系統 KPI、真實統計數據、架構說明 | ❌ |
| 2 | 🚨 即時威脅監控 | SOC 風格威脅監控、預警事件串流、地區風險 | ❌ |
| 3 | 💬 詐騙對話模擬器 | 與 AI 詐騙犯即時對話，練習識破詐騙 | ✅ |
| 4 | 🧬 話術 DNA 圖譜 | 7 種詐騙類型的心理操控特徵分布與相似度 | ❌ |
| 5 | 📅 話術進化時間軸 | 2021-2024 詐騙話術演化歷程（7 種類型） | ❌ |
| 6 | 🎯 詐騙免疫訓練 | 互動式防詐訓練，答題獲得免疫證書 | ✅（可 fallback） |
| 7 | 🤖 LLM 話術生成 | 輸入情境，即時生成詐騙變種話術 + XAI 分析 | ✅（可 fallback） |
| 8 | 🔍 XAI 話術分析 | 輸入文字，高亮標記心理操控特徵片段 | ❌ |
| 9 | 🔥 熱詞排行榜 | 詐騙話術高頻關鍵詞 TOP 20 | ❌ |
| 10 | 🧪 沙盤推演 | 設定情境參數，預測詐騙變種風險 | ❌ |
| 11 | 🗺️ 受害風險地圖 | 依年齡層 × 地區的風險指數矩陣 | ❌ |
| 12 | 📊 模型準確率評估 | 即時分類測試，顯示混淆矩陣與準確率 | ❌ |

---

## API 端點總覽（6 個端點）

| 方法 | 路徑 | 說明 | 需要 API Key |
|------|------|------|-------------|
| GET | `/v1/health` | 健康檢查 | ❌ |
| GET | `/v1/predictions/alerts` | 查詢預警事件列表 | ✅ |
| GET | `/v1/risk-vectors` | 查詢風險向量列表 | ✅ |
| POST | `/v1/analyze/highlight` | 單一文本 XAI 高亮分析 | ✅ |
| POST | `/v1/analyze/batch` | 批次完整分析（關鍵詞+心理標籤+分群） | ✅ |
| POST | `/v1/scam/generate` | 觸發詐騙話術生成 | ✅ |
| POST | `/v1/data/import` | 匯入報案資料（CSV/JSON） | ✅ |

API Key 測試用值：`test-key-001`（標準方案）或 `test-key-002`（高級方案）

---

## 功能詳細使用說明


### 1. 🏠 系統總覽

**位置：** Dashboard 側邊欄 → 🏠 系統總覽

**功能：**
- 顯示 2023 年台灣詐騙現況 KPI（83,000 件案件、88.2 億元損失）
- 6 張系統能力卡片（LLM 生成、XAI 分析、免疫訓練、異常偵測、風險地圖、API）
- 系統處理流程圖
- 7 種詐騙類型排行表（案件數、平均損失、趨勢）

**操作方式：** 進入頁面即可查看，無需操作。

---

### 2. 🚨 即時威脅監控

**位置：** Dashboard 側邊欄 → 🚨 即時威脅監控

**功能：**
- 當前威脅等級橫幅（基於趨勢上升的詐騙類型數量判定）
- 4 個即時統計指標（活躍威脅數、24h 新變種、今日案件、AI 詐騙佔比）
- 預警事件串流（基於真實統計數據，確定性生成）
- 威脅分布長條圖
- 高風險地區 TOP 5

**操作方式：**
1. 進入頁面查看威脅態勢
2. 點「🔄 刷新事件」重新載入（結果不變，因為是確定性資料）
3. 右側查看威脅分布和高風險地區

---

### 3. 💬 詐騙對話模擬器

**位置：** Dashboard 側邊欄 → 💬 詐騙對話模擬器

**功能：**
- 與 AI 扮演的詐騙犯進行即時對話
- 系統即時用 XAI 高亮標記每句話的心理操控手法
- 識破分數追蹤
- 結束後顯示防詐重點提醒

**操作方式：**
1. 從下拉選單選擇詐騙情境（假冒銀行客服 / 投資詐騙 / 假冒政府機關）
2. 點「🚀 開始模擬」
3. 在輸入框輸入你的回應，點「📤 發送」
4. 觀察詐騙犯的回應（高亮標記的部分就是操控手法）
5. 嘗試說「我要報警」「165」「不相信」等來識破詐騙
6. 點「🚪 結束」查看結果

**需要：** Ollama 或其他 LLM 服務在跑

---

### 4. 🧬 話術 DNA 圖譜

**位置：** Dashboard 側邊欄 → 🧬 話術 DNA 圖譜

**功能：**
- 7 種詐騙類型 × 5 種心理操控維度的特徵分布矩陣
- 話術相似度 TOP 5（哪些詐騙類型使用相似手法）
- 危險等級排行（0-10 分）
- 各類型核心話術關鍵詞

**操作方式：** 進入頁面即可查看。矩陣中數值越高（越紅）代表該詐騙類型越依賴該心理操控手法。

---

### 5. 📅 話術進化時間軸

**位置：** Dashboard 側邊欄 → 📅 話術進化時間軸

**功能：**
- 追蹤 2021-2024 年詐騙話術的演化歷程
- 7 種詐騙類型各有 4 年的進化資料
- 平均損失趨勢圖 + 案件數趨勢圖
- 每年的新手法說明

**操作方式：**
1. 從下拉選單選擇詐騙類型（7 種可選）
2. 查看趨勢圖和時間軸卡片
3. 注意標記「🆕 最新手法」的 2024 年卡片

---

### 6. 🎯 詐騙免疫訓練

**位置：** Dashboard 側邊欄 → 🎯 詐騙免疫訓練

**功能：**
- 互動式防詐識別訓練
- 3 個難度等級（初級 60% / 中級 70% / 高級 80% 通過門檻）
- 閱讀詐騙話術 → 選擇心理操控特徵 → 系統給出 XAI 解析
- 通過後頒發防詐免疫證書

**操作方式：**
1. 選擇難度（初級🟢 / 中級🟡 / 高級🔴）
2. 選擇詐騙類型
3. 點「🚀 開始訓練」
4. 閱讀每道題目的詐騙話術
5. 勾選你認為包含的心理操控特徵（信任建立、緊迫感製造、情緒勒索、權威偽裝、利益誘導）
6. 點「✅ 提交答案」查看解析
7. 點「➡️ 下一題」繼續
8. 完成後查看分數和證書

**需要：** 有 LLM 時使用即時生成題目，沒有時 fallback 到真實詐騙話術樣本

---

### 7. 🤖 LLM 話術生成

**位置：** Dashboard 側邊欄 → 🤖 LLM 話術生成

**功能：**
- 輸入詐騙情境，呼叫 LLM 即時生成多種變形話術
- 同時執行 XAI 分析，高亮標記心理操控片段
- 支援 3-10 個樣本數量

**操作方式：**
1. 在「詐騙情境描述」輸入情境（如：假冒銀行客服，聲稱帳戶出現異常交易）
2. 選擇目標受眾
3. 調整生成樣本數量
4. 勾選「同時執行 XAI 分析」
5. 點「🚀 生成話術」
6. 查看生成結果，展開每個樣本查看高亮分析

**需要：** 有 LLM 時真實生成，沒有時使用示範資料

---

### 8. 🔍 XAI 話術分析

**位置：** Dashboard 側邊欄 → 🔍 XAI 話術分析

**功能：**
- 輸入任意文字，系統高亮標記心理操控特徵片段
- 5 種顏色對應 5 種心理特徵：
  - 🟢 信任建立（綠色）
  - 🟡 緊迫感製造（黃色）
  - 🔴 情緒勒索（紅色）
  - 🔵 權威偽裝（藍色）
  - 🟣 利益誘導（紫色）
- 顯示觸發片段數、標籤數、覆蓋率

**操作方式：**
1. 在文字框輸入要分析的話術（有預設範例）
2. 點「🔍 開始分析」
3. 查看高亮結果（滑鼠移到高亮片段可看標籤名稱）
4. 下方查看觸發的心理特徵標籤列表

---

### 9. 🔥 熱詞排行榜

**位置：** Dashboard 側邊欄 → 🔥 熱詞排行榜

**功能：**
- 顯示詐騙話術中出現頻率最高的 TOP 20 關鍵詞
- 長條圖視覺化
- 排行榜明細表

**操作方式：** 進入頁面即可查看。資料來源為 165 反詐騙專線通報案件描述統計。

---

### 10. 🧪 沙盤推演

**位置：** Dashboard 側邊欄 → 🧪 沙盤推演

**功能：**
- 設定詐騙情境參數，模擬預測可能出現的詐騙變種
- 顯示預測風險等級、信心分數、高風險特徵

**操作方式：**
1. 選擇詐騙情境類型（8 種可選）
2. 選擇目標受眾
3. 選擇風險等級篩選（可選）
4. 調整分析時間視窗
5. 點「🚀 執行推演」
6. 查看推演結果

---

### 11. 🗺️ 受害風險地圖

**位置：** Dashboard 側邊欄 → 🗺️ 受害風險地圖

**功能：**
- 依年齡層（5 組）× 地區（22 縣市）呈現風險指數
- 整體風險等級、高/中/低風險區域統計
- 最高風險條目詳情

**操作方式：**
1. 展開「🔧 篩選設定」可選擇特定地區或年齡層
2. 查看摘要指標和風險矩陣
3. 注意最高風險的年齡層 × 地區組合

---

### 12. 📊 模型準確率評估

**位置：** Dashboard 側邊欄 → 📊 模型準確率評估

**功能：**
- 使用真實詐騙話術樣本進行即時分類測試
- 顯示混淆矩陣、準確率、精確率、召回率
- 基準：84.7% 準確率（500 個測試樣本）

**操作方式：**
1. 點「執行評估」
2. 查看混淆矩陣和各項指標

---

## API 使用說明

所有需要認證的 API 端點都需要在 Header 加上 `X-API-Key`。

### 健康檢查（不需要 API Key）

```bash
curl http://localhost:8000/v1/health
```

回應：
```json
{"status": "healthy", "service": "AI 詐騙進化預測系統 API Gateway", "version": "1.0.0"}
```

### 查詢預警事件

```bash
curl -H "X-API-Key: test-key-001" http://localhost:8000/v1/predictions/alerts
```

### XAI 高亮分析

```bash
curl -X POST http://localhost:8000/v1/analyze/highlight \
  -H "X-API-Key: test-key-001" \
  -H "Content-Type: application/json" \
  -d '{"text": "您好，我是銀行客服，您的帳戶異常，請立即提供驗證碼"}'
```

### 批次完整分析

```bash
curl -X POST http://localhost:8000/v1/analyze/batch \
  -H "X-API-Key: test-key-001" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["您好，我是銀行客服", "恭喜中獎，請繳手續費"]}'
```

### 話術生成（需要 LLM 服務）

```bash
curl -X POST http://localhost:8000/v1/scam/generate \
  -H "X-API-Key: test-key-001" \
  -H "X-Operator-Id: admin-001" \
  -H "X-Operator-Role: 系統管理員" \
  -H "Content-Type: application/json" \
  -d '{"scenario": "假冒銀行客服", "target_audience": "中老年族群", "sample_count": 10}'
```

### Swagger UI

啟動後端後，打開 `http://localhost:8000/docs` 可以用互動式介面測試所有 API。

---

## 測試

```bash
# 執行全部測試（392 個）
python -m pytest tests/ -v

# 只跑特定模組的測試
python -m pytest tests/test_scam_engine.py -v          # 詐騙生成引擎
python -m pytest tests/test_pattern_analyzer.py -v     # 模式分析器
python -m pytest tests/test_prediction_layer.py -v     # 預測層
python -m pytest tests/test_api_gateway.py -v          # API 閘道
python -m pytest tests/test_access_control.py -v       # 存取控制
python -m pytest tests/test_data_import.py -v          # 資料匯入
python -m pytest tests/test_dashboard.py -v            # 儀表板邏輯
python -m pytest tests/test_models.py -v               # 資料模型
python -m pytest tests/test_bug_condition_exploration.py -v   # 缺陷驗證測試
python -m pytest tests/test_preservation_properties.py -v     # 保留性測試
```

目前共 **392 個測試**，全部通過。

---

## 專案結構

```
ScamOracle/
├── app/
│   ├── api_gateway/              # FastAPI 後端 API
│   │   ├── main.py               # API 主入口（lifespan、中介軟體、路由掛載）
│   │   ├── middleware/
│   │   │   ├── api_key.py        # API 金鑰驗證（支援環境變數載入）
│   │   │   ├── rate_limit.py     # 滑動視窗速率限制
│   │   │   └── logging.py        # 請求日誌
│   │   └── routers/
│   │       ├── health.py         # GET /v1/health
│   │       ├── scam.py           # POST /v1/scam/generate
│   │       ├── risk_vectors.py   # GET /v1/risk-vectors
│   │       ├── predictions.py    # GET /v1/predictions/alerts
│   │       ├── analyze.py        # POST /v1/analyze/highlight, /batch
│   │       └── data.py           # POST /v1/data/import
│   ├── scam_engine/
│   │   └── generator.py          # LLM 話術生成（LangChain + 指數退避重試）
│   ├── pattern_analyzer/
│   │   ├── analyzer.py           # 完整分析管線（語言偵測→嵌入→關鍵詞→分類→分群）
│   │   ├── embedder.py           # Sentence-BERT 語意嵌入（384 維）
│   │   ├── keyword_extractor.py  # TF-IDF 關鍵詞提取
│   │   ├── psych_classifier.py   # 心理特徵分類器（5 類規則式）
│   │   ├── clusterer.py          # K-Means 分群
│   │   └── xai_highlighter.py    # XAI 可解釋性高亮
│   ├── prediction_layer/
│   │   ├── analyzer.py           # 異常偵測（Isolation Forest）+ 趨勢分析
│   │   ├── risk_vector.py        # 風險向量生成與儲存
│   │   ├── alerting.py           # 預警事件生成與通知
│   │   ├── scheduler.py          # APScheduler 排程（每 24 小時）
│   │   └── validator.py          # 報案資料格式驗證
│   ├── data_import/
│   │   ├── importer.py           # CSV/JSON 資料匯入
│   │   └── pii_remover.py        # PII 自動去識別化
│   ├── access_controller/
│   │   ├── rbac.py               # RBAC 角色權限（4 角色 × 3 操作）
│   │   ├── audit_log.py          # SHA-256 防竄改稽核日誌
│   │   └── mfa.py                # TOTP 二次驗證
│   ├── dashboard/
│   │   ├── streamlit_app.py      # Streamlit 主入口（12 頁面）
│   │   ├── styles.py             # 全域 CSS
│   │   └── pages/
│   │       ├── threat_monitor.py # 即時威脅監控
│   │       ├── scam_simulator.py # 詐騙對話模擬器
│   │       ├── dna_map.py        # 話術 DNA 圖譜
│   │       ├── training.py       # 詐騙免疫訓練
│   │       ├── hotwords.py       # 熱詞排行榜
│   │       ├── sandbox.py        # 沙盤推演
│   │       ├── risk_map.py       # 受害風險地圖
│   │       └── cache.py          # 快取降級機制
│   ├── models/                   # 資料模型（ScamScript, RiskVector, AlertEvent 等）
│   └── config.py                 # 集中設定管理（Pydantic Settings）
├── data/
│   ├── taiwan_scam_data.py       # 台灣真實詐騙統計資料
│   └── sample_scam_cases.csv     # 範例報案資料
├── tests/                        # 測試套件（392 tests）
├── docs/
│   ├── aws_deployment.md         # AWS 部署文件
│   └── DEMO_GUIDE.md             # Demo 操作指南
├── .env                          # 環境變數（需自行填入 API Key）
├── .env.example                  # 環境變數範本
├── docker-compose.yml            # Docker 服務（PostgreSQL, Redis, Qdrant）
├── requirements.txt              # Python 依賴
└── pyproject.toml                # 專案設定
```

---

## 資料來源

| 資料 | 來源 | 類型 |
|------|------|------|
| 各縣市詐騙案件數 | 警政署 165 專線（2023） | 真實統計 |
| 各年齡層受害比例 | 165 資料庫分析 | 真實統計 |
| 7 種詐騙類型案件數與損失 | 刑事警察局（2023） | 真實統計 |
| 月度趨勢（18 個月） | 警政署月報 | 真實統計 |
| 詐騙熱詞（32 個） | 165 通報案件描述統計 | 真實統計 |
| 詐騙話術樣本（7 則） | 公開案例整理，已去識別化 | 真實案例 |
| 模型效能基準 | 500 樣本測試（84.7% 準確率） | 真實測試 |
| LLM 生成話術 | GPT-4o / Gemini / Ollama | AI 合成 |

---

## 技術棧

| 類別 | 技術 |
|------|------|
| 後端框架 | FastAPI + Uvicorn |
| LLM 整合 | LangChain + OpenAI GPT-4o / Google Gemini / Ollama |
| NLP | Sentence-BERT (paraphrase-multilingual-MiniLM-L12-v2) |
| 機器學習 | scikit-learn (TF-IDF, K-Means, Isolation Forest) |
| XAI | 規則式 Regex 高亮 + 信心分數 |
| 排程 | APScheduler |
| 前端 | Streamlit |
| 資料庫 | PostgreSQL（規劃中，目前 in-memory） |
| 快取 | Redis（規劃中，目前 in-memory） |
| 向量資料庫 | Qdrant（規劃中） |
| 容器化 | Docker + Docker Compose |
| 雲端 | AWS ECS Fargate + ECR |
| 測試 | pytest + Hypothesis (Property-Based Testing) |

---

## 團隊分工

| 成員 | 負責範疇 |
|------|---------|
| Member A | 後端架構、AI 模型、雲端部署（FastAPI、LLM、AWS） |
| Member B | 資料處理、前端介面、版本控制、簡報（Streamlit、GitHub） |
