# AEGIS CORE — AI 詐騙話術進化預警系統

> 從被動防禦到主動預測 — 運用生成式 AI 構築下一代防詐護城河

---

## 目錄

- [快速開始](#快速開始)
- [我們在解決什麼問題](#我們在解決什麼問題)
- [我們如何解決](#我們如何解決)
- [與市面現有方案的差距](#與市面現有方案的差距)
- [系統架構](#系統架構)
- [環境需求與安裝](#環境需求與安裝)
- [啟動服務](#啟動服務)
- [12 個功能頁面](#12-個功能頁面)
- [API 端點](#api-端點)
- [常見問題排解](#常見問題排解)
- [自動化測試](#自動化測試)
- [專案結構](#專案結構)
- [資料來源與真實性](#資料來源與真實性)
- [技術棧](#技術棧)
- [團隊分工](#團隊分工)

---

## 快速開始

```bash
# 1. 安裝依賴
python -m venv .venv
.venv/Scripts/activate          # Windows
pip install -r requirements.txt

# 2. 設定環境變數
cp .env.example .env
# 編輯 .env：至少設定 LLM_PROVIDER 與 API_KEY

# 3. 啟動後端（port 8001）
python -m uvicorn app.api_gateway.main:app --host 0.0.0.0 --port 8001

# 4. 啟動前端（port 8502，另開終端機）
python -m streamlit run app/dashboard/streamlit_app.py --server.port 8502
```

| 服務 | 網址 |
|------|------|
| Dashboard | http://localhost:8502 |
| API 文件 | http://localhost:8001/docs |
| 健康檢查 | http://localhost:8001/v1/health |

使用本地 LLM 時，請先安裝 [Ollama](https://ollama.com) 並執行 `ollama pull llama3.2`。

---

## 我們在解決什麼問題

台灣正面臨史上最嚴重的詐騙危機：

- 2023 年全台詐騙案件 **83,000 件**，年增 27%，損失金額 **88.2 億元**
- 2024 年案件數暴增至 **126,110 件**，損失 **138.5 億元**
- 2025 年持續攀升至 **161,442 件**，損失 **172.3 億元**
- 投資詐騙平均每案損失 **112 萬元**，AI 深偽詐騙 **75 萬元**
- 詐騙手法每 6–12 個月進化一次：電話詐騙 → 簡訊釣魚 → LINE 假客服 → AI 深偽語音 → 全自動 AI 詐騙

現有防詐系統的根本問題是「被動防禦」— 165 反詐騙專線只能在民眾被騙後接報案，銀行只能在交易完成後攔截。等到新型詐騙手法被發現時，已有數千人受害。

**核心問題：能不能在新型詐騙大規模爆發之前就預測到它？**

---

## 我們如何解決

AEGIS CORE 採用「以 AI 對抗 AI」的逆向思維：

1. **LLM 話術裂變生成** — 用 GPT-4o / Gemini / Ollama 逆向模擬詐騙犯思維，從一個種子情境自動生成多種詐騙變種話術；主要 LLM 失敗時自動切換備援
2. **NLP 語意分析** — Sentence-BERT 384 維向量、TF-IDF 關鍵詞、K-Means 分群，找出詐騙手法家族關係
3. **XAI 可解釋性分析** — 高亮標記心理操控片段：信任建立、緊迫感製造、情緒勒索、權威偽裝、利益誘導
4. **異常偵測預警** — Isolation Forest 時間序列分析，24 小時內偵測新興詐騙趨勢
5. **防詐免疫訓練** — 互動式訓練與防詐免疫證書
6. **Risk Vector API** — 標準化風險向量，可串接銀行、電信商、保險公司

---

## 與市面現有方案的差距

| 比較項目 | 165 反詐騙專線 | 銀行交易監控 | Whoscall 來電辨識 | AEGIS CORE |
|---------|--------------|------------|-----------------|-----------|
| 防禦模式 | 被動接報案 | 被動攔截交易 | 被動辨識號碼 | **主動預測未來詐騙** |
| AI 應用 | 無 | 規則式 | 資料庫比對 | **LLM 生成 + NLP + XAI** |
| 可解釋性 | 人工判斷 | 無 | 無 | **XAI 高亮標記操控手法** |
| 預警時間 | 事後 | 事後 | 事後 | **提前 24 小時** |
| 教育功能 | 宣導海報 | 無 | 無 | **互動式免疫訓練 + 證書** |
| API 串接 | 無 | 內部系統 | 付費 API | **開放 Risk Vector API** |

---

## 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│              Streamlit Dashboard（前端）                      │
│   12 個功能頁面 — http://localhost:8502                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP API（含逾時與錯誤詳情回傳）
┌──────────────────────────▼──────────────────────────────────┐
│              FastAPI API Gateway（後端）                      │
│   REST API — http://localhost:8001                            │
│   中介軟體：API Key 驗證 → 速率限制 → 請求日誌               │
└──────────────────────────┬──────────────────────────────────┘
                           │
     ┌─────────┬───────────┼───────────┬──────────┬──────────┐
     ▼         ▼           ▼           ▼          ▼          ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│ Scam    ││ Pattern ││Prediction││ Live    ││ Data    ││ Access  │
│ Engine  ││ Analyzer││ Layer   ││ Data    ││ Import  ││Controller│
│ (LLM)  ││ (NLP)   ││(異常偵測)││(自動更新)││(PII去識別)││(RBAC)  │
└────┬────┘└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│   主要：OpenAI GPT-4o / Google Gemini / Ollama（本地）       │
│   備援：LLM_FALLBACK 自動切換（預設 ollama）                  │
└─────────────────────────────────────────────────────────────┘
```

處理流程：情境種子 → LLM 話術裂變 → NLP 特徵萃取 → XAI 高亮 → 異常偵測 → Risk Vector → API 串接

---

## 環境需求與安裝

### 環境需求

| 項目 | 版本 |
|------|------|
| Python | 3.11 以上 |
| Docker Desktop | 最新版（可選） |
| Ollama | 最新版（本地 LLM，可選） |
| 作業系統 | Windows / macOS / Linux |

### 步驟 1：基礎設施（Docker，可選）

> PostgreSQL / Redis / Qdrant 已透過 `docker-compose.yml` 配置，但**應用程式尚未接入**——執行時仍使用 in-memory 儲存。本地開發可直接跳過。

```bash
docker compose up -d
```

### 步驟 2：虛擬環境與依賴

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt
```

### 步驟 3：環境變數

```bash
cp .env.example .env
```

`.env` 關鍵設定：

```env
# LLM（主要 provider，失敗時自動切換備援）
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
LLM_FALLBACK=ollama
OLLAMA_MODEL=llama3.2
LLM_TIMEOUT_SECONDS=300

# Dashboard 呼叫 API 逾時（話術生成預設 LLM_TIMEOUT_SECONDS * 2 + 60 = 660 秒）
# DASHBOARD_LLM_GENERATE_TIMEOUT_SECONDS=660

# API Gateway
API_KEY=test-key-001
API_GATEWAY_URL=http://localhost:8001
```

**LLM 選項：**

| 模式 | 設定 | 說明 |
|------|------|------|
| 本地 Ollama | `LLM_PROVIDER=ollama` | 免費、資料不外洩，生成較慢 |
| OpenAI | `LLM_PROVIDER=openai` | 需 API Key，品質最佳 |
| Google Gemini | `LLM_PROVIDER=google` | 需 `GOOGLE_API_KEY` |
| 自動備援 | `LLM_FALLBACK=ollama` | 主要 LLM 失敗時切換本地模型 |

### 步驟 4：安裝 Ollama（使用本地 LLM 時）

1. 從 https://ollama.com 下載安裝
2. `ollama pull llama3.2`
3. 確認服務運行：`curl http://localhost:11434/api/tags`

---

## 啟動服務

開兩個終端機：

**終端機 1 — API Gateway（port 8001）：**
```bash
python -m uvicorn app.api_gateway.main:app --host 0.0.0.0 --port 8001
```

**終端機 2 — Dashboard（port 8502）：**
```bash
python -m streamlit run app/dashboard/streamlit_app.py --server.port 8502
```

> port 8501 可能被其他 Streamlit 專案佔用，建議使用 8502。

---

## 12 個功能頁面

| # | 頁面 | 說明 | 需要 LLM |
|---|------|------|---------|
| 1 | 首頁 | KPI、台灣詐騙統計、六大模組介紹 | 否 |
| 2 | 即時威脅監控 | SOC 風格監控、預警事件串流、威脅分布 | 否 |
| 3 | 詐騙對話模擬器 | 三種情境與 AI 詐騙犯實戰對話 | 是 |
| 4 | 話術 DNA 圖譜 | 五維心理操控指標、餘弦相似度分析 | 否 |
| 5 | 話術進化時間軸 | 2021–2026 七大類型演變，可 LLM 補全未來年份 | 選用 |
| 6 | 詐騙免疫訓練 | 三難度互動訓練、防詐免疫證書 | 選用 |
| 7 | LLM 話術生成 | 輸入情境，生成 10–50 筆變種話術 + XAI 分析 | 是 |
| 8 | XAI 話術分析 | 規則式高亮五類心理操控片段 | 否 |
| 9 | 熱詞排行榜 | 38 個高頻關鍵詞 TOP 20 | 否 |
| 10 | 沙盤推演 | 自定義情境與受眾，模擬詐騙變種風險 | 否 |
| 11 | 受害風險地圖 | 年齡 × 地區雙維度風險指數 | 否 |
| 12 | 模型準確率評估 | 靜態基準 88.9% + 即時小樣本測試 | 否 |

### LLM 話術生成（重點功能）

- 透過 API Gateway 呼叫後端，遵守架構分層
- 支援 GPT-4o / Gemini / Ollama，失敗自動切換 `LLM_FALLBACK`
- 生成 10–50 筆樣本，可同步執行 XAI 高亮
- Ollama 回應格式容錯：自動剝除 markdown 程式碼區塊、修正欄位錯置、解析失敗自動重試
- 無 LLM 時 fallback 到示範資料

---

## API 端點

所有業務端點需要 `X-API-Key` 標頭。測試用 Key：`test-key-001`

### 健康檢查（免 API Key）
```bash
curl http://localhost:8001/v1/health
```

### 查詢預警事件
```bash
curl -H "X-API-Key: test-key-001" http://localhost:8001/v1/predictions/alerts
```

### 查詢風險向量
```bash
curl -H "X-API-Key: test-key-001" http://localhost:8001/v1/risk-vectors
```

### XAI 高亮分析
```bash
curl -X POST http://localhost:8001/v1/analyze/highlight \
  -H "X-API-Key: test-key-001" \
  -H "Content-Type: application/json" \
  -d '{"text": "您好，我是銀行客服，您的帳戶異常，請立即提供驗證碼"}'
```

### 話術生成（需要 LLM，需操作人員標頭）
```bash
curl -X POST http://localhost:8001/v1/scam/generate \
  -H "X-API-Key: test-key-001" \
  -H "X-Operator-Id: dashboard-user" \
  -H "X-Operator-Role: SCAM_ANALYST" \
  -H "Content-Type: application/json" \
  -d '{"scenario": "假冒銀行客服", "target_audience": "中老年族群", "sample_count": 10}'
```

> `X-Operator-Role` 支援中文（`詐騙分析師`）或枚舉名稱（`SCAM_ANALYST`）。

### 觸發即時資料擷取
```bash
curl -X POST http://localhost:8001/v1/data/refresh \
  -H "X-API-Key: test-key-001"
```

### 資料匯入（CSV / JSON）
```bash
curl -X POST http://localhost:8001/v1/data/import \
  -H "X-API-Key: test-key-001" \
  -F "file=@data/sample_scam_cases.csv"
```

互動式測試：http://localhost:8001/docs

---

## 常見問題排解

### LLM 話術生成失敗

| 錯誤訊息 | 原因 | 解法 |
|---------|------|------|
| `Read timed out` | Dashboard 等待時間不足 | 已預設 660 秒；可調高 `DASHBOARD_LLM_GENERATE_TIMEOUT_SECONDS` |
| `503 Service Unavailable` | 後端 LLM 解析或 API 失敗 | 查看 API Gateway 日誌；確認 Ollama 運行中或 OpenAI Key 有效 |
| `LLM_PARSE_ERROR` | Ollama 回傳非標準 JSON | 已內建容錯與重試；仍失敗請減少 `sample_count` 或換用 GPT-4o |
| `Connection refused :8001` | API Gateway 未啟動 | 執行 uvicorn 啟動後端 |

### 檢查清單

```bash
# 1. 後端是否運行
curl http://localhost:8001/v1/health

# 2. Ollama 是否運行（使用本地 LLM 時）
curl http://localhost:11434/api/tags

# 3. 環境變數是否正確
# 確認 .env 中 LLM_PROVIDER、API_KEY、API_GATEWAY_URL=http://localhost:8001
```

---

## 自動化測試

```bash
# 全部測試（411 個）
python -m pytest tests/ -v

# 各模組
python -m pytest tests/test_scam_engine.py -v
python -m pytest tests/test_api_gateway.py -v
python -m pytest tests/test_access_controller.py -v
python -m pytest tests/test_dashboard.py -v
python -m pytest tests/test_models.py -v
```

測試類型：單元測試 + Property-Based Testing（Hypothesis）+ 整合測試

---

## 專案結構

```
AEGIS-CORE/
├── app/
│   ├── api_gateway/              # FastAPI 後端
│   │   ├── main.py
│   │   ├── middleware/           # API Key、速率限制、日誌
│   │   └── routers/              # health、scam、analyze、predictions、data、risk-vectors
│   ├── scam_engine/              # LLM 話術生成（含備援切換與 JSON 容錯）
│   ├── pattern_analyzer/         # NLP + XAI 高亮
│   ├── prediction_layer/         # 異常偵測、Risk Vector、排程
│   ├── live_data/                # 即時擷取、爬蟲、快取、時間軸生成
│   ├── data_import/              # 報案匯入 + PII 去識別
│   ├── access_controller/        # RBAC + 稽核日誌
│   ├── dashboard/                # Streamlit 前端（12 頁面）
│   └── models/                   # 資料模型（ScamScript、RiskVector、AlertEvent 等）
├── data/
│   ├── taiwan_scam_data.py       # 靜態基準資料
│   └── live_cache.json           # 即時快取（gitignore，執行時自動產生）
├── tests/                        # 411 個自動化測試
├── docker-compose.yml
├── Dockerfile / Dockerfile.streamlit
├── .env.example
└── requirements.txt
```

---

## 資料來源與真實性

### 即時資料（四層降級）

| 層級 | 來源 | 說明 |
|------|------|------|
| 第一層 | data.gov.tw / 165.npa.gov.tw / LTN 新聞 | 政府開放資料與新聞爬蟲 |
| 第二層 | 磁碟快取 | `data/live_cache.json` |
| 第三層 | 靜態預設 | `data/taiwan_scam_data.py` |

### 靜態基準資料

| 資料 | 來源 | 類型 |
|------|------|------|
| 2021–2023 各縣市 / 年齡層 / 類型統計 | 165 專線公開統計 | 真實統計 |
| 詐騙熱詞（38 個）| 165 通報描述統計 | 真實統計 |
| 話術樣本（8 則）| 公開案例去識別化 | 真實案例 |
| 模型效能（88.9%）| 1,200 筆測試樣本 | 真實測試 |
| 2024–2026 統計 | 歷史趨勢外推 | 趨勢推估 |
| LLM 生成話術 | Ollama / GPT-4o / Gemini | AI 合成 |

---

## 技術棧

| 類別 | 技術 |
|------|------|
| 後端 | FastAPI + Uvicorn（port 8001） |
| LLM | LangChain + Ollama / GPT-4o / Gemini，支援 `LLM_FALLBACK` 自動切換 |
| NLP | Sentence-BERT (paraphrase-multilingual-MiniLM-L12-v2) |
| 機器學習 | scikit-learn（TF-IDF、K-Means、Isolation Forest） |
| XAI | 規則式 Regex 高亮 + 信心分數 |
| 前端 | Streamlit（12 頁面，port 8502）+ Plotly |
| 排程 | APScheduler（預測 24h + 資料擷取 6h） |
| 儲存 | in-memory（PostgreSQL / Redis / Qdrant 已配置待接入） |
| 測試 | pytest + Hypothesis，411 個測試 |
| 容器化 | Docker + Docker Compose |

---

## 團隊分工

| 成員 | 主責範疇 | 代表貢獻 |
|------|---------|---------|
| hank | 前端 UI / 視覺設計 / 品牌 / 部署 | AEGIS CORE 品牌識別、Dashboard 主體、AWS ECS 部署 |
| zhiying122 | 後端引擎 / 資料系統 / 安全 / 測試 | LLM 生成引擎、即時爬蟲、RBAC 安全、測試維護 |
