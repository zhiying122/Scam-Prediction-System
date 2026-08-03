# ScamDNA — AI 詐騙話術進化預警系統

> 從被動防禦到主動預測 — 運用生成式 AI 構築下一代防詐護城河

---

## 目錄

- [快速開始](#快速開始)
- [問題背景](#問題背景)
- [解決方案](#解決方案)
- [系統架構](#系統架構)
- [資料來源](#資料來源)
- [環境需求與安裝](#環境需求與安裝)
- [啟動服務](#啟動服務)
- [登入系統](#登入系統)
- [12 個功能頁面](#12-個功能頁面)
- [API 端點](#api-端點)
- [自動化測試](#自動化測試)
- [專案結構](#專案結構)
- [技術棧](#技術棧)
- [團隊分工](#團隊分工)

---

## 快速開始

```powershell
# 1. 建立虛擬環境並安裝依賴（建議 Python 3.11–3.13）
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. 設定環境變數
copy .env.example .env
# 編輯 .env：設定 LLM_PROVIDER 與 API_KEY
# 個人 Dashboard 帳號可寫在 .env.local 的 DASHBOARD_LOCAL_ADMINS

# 3. 一鍵啟動（Docker → API :8001 → Dashboard :8502）
.\scripts\start-dev.ps1

# 停止本機 API / Dashboard（可加 -AlsoDocker 一併停容器）
.\scripts\stop-dev.ps1
```

| 服務 | 網址 |
|------|------|
| Dashboard | http://localhost:8502 |
| API 文件（Swagger） | http://localhost:8001/docs |
| 健康檢查 | http://localhost:8001/v1/health |

---

## 問題背景

台灣正面臨史上最嚴重的詐騙危機：

| 年份 | 案件數 | 年增率 | 總損失金額 | 資料類型 |
|------|--------|--------|-----------|---------|
| 2021 | 52,000 | — | 58.4 億 | 真實統計 |
| 2022 | 65,000 | +25% | 68.7 億 | 真實統計 |
| 2023 | 83,000 | +27% | 88.2 億 | 真實統計 |
| 2024 | 126,110 | +52% | 138.5 億 | 趨勢推估 |
| 2025 | 161,442 | +28% | 172.3 億 | 趨勢推估 |
| 2026 Q1 | 43,691 | — | 47.8 億 | 趨勢推估 |

現有防詐系統的根本問題是「被動防禦」— 165 專線只能事後接報案，銀行只能事後攔截。等到新型詐騙被發現時，已有數千人受害。

**我們的核心問題：能不能在新型詐騙大規模爆發之前就預測到它？**

---

## 解決方案

ScamDNA 採用「以 AI 對抗 AI」的逆向思維：

1. **LLM 話術裂變生成** — GPT-4o / Gemini / Ollama 逆向模擬詐騙犯思維，生成多種變種話術
2. **NLP 語意分析** — Sentence-BERT 384 維向量 + TF-IDF + K-Means 分群
3. **XAI 可解釋性** — 規則式高亮標記五類心理操控片段（信任建立、緊迫感製造、情緒勒索、權威偽裝、利益誘導）
4. **異常偵測預警** — Isolation Forest 每日趨勢檢測與異常警示
5. **防詐免疫訓練** — 互動式訓練 + 防詐免疫證書
6. **Risk Vector API** — 標準化風險向量，可串接銀行、電信商、保險公司

---

## 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│              Streamlit Dashboard（前端）                      │
│   12 個功能頁面 — http://localhost:8502                       │
│   登入/註冊 → 角色式存取控制（RBAC）                          │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP API
┌──────────────────────────▼──────────────────────────────────┐
│              FastAPI API Gateway（後端）                      │
│   REST API — http://localhost:8001                            │
│   中介軟體：API Key → 速率限制 → 請求日誌                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
     ┌─────────┬───────────┼───────────┬──────────┬──────────┐
     ▼         ▼           ▼           ▼          ▼          ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│ Scam    ││ Pattern ││Prediction││ Live    ││ Data    ││ Access  │
│ Engine  ││ Analyzer││ Layer   ││ Data    ││ Import  ││Controller│
│ (LLM)  ││ (NLP)   ││(異常偵測)││(即時更新)││(PII去識別)││(RBAC)  │
└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
```

---

## 資料來源

### 靜態基準資料（`data/taiwan_scam_data.py`）

| 資料 | 來源 | 類型 | 年份 |
|------|------|------|------|
| 各縣市案件統計 | 內政部警政署統計查詢網 | 真實統計 | 2021-2023 |
| 各年齡層受害比例 | 165 資料庫分析 | 真實統計 | 2023 |
| 詐騙類型分布 | 165 通報分類 | 真實統計 | 2023 |
| 詐騙熱詞（38 個） | 165 通報描述統計 | 真實統計 | 2026 Q1 |
| 話術樣本（8 則） | 公開案例去識別化 | 真實案例 | 2026 |
| 模型效能（88.9%） | 1,200 筆測試樣本 | 真實測試 | 2026 |
| 2024-2026 統計 | 歷史趨勢線性外推 | 趨勢推估 | 2024-2026 |

**資料來源連結：**
- 警政統計查詢網：https://ba.npa.gov.tw
- 165 全民防騙網：https://165.npa.gov.tw
- 刑事警察局：https://www.cib.gov.tw
- 風傳媒報導（2024 數據）：https://www.storm.mg/stylish/5313561

### 動態即時資料（`app/live_data/`）

系統支援四層資料降級策略：

| 層級 | 來源 | 說明 |
|------|------|------|
| 第一層 | data.gov.tw / 165.npa.gov.tw / 新聞爬蟲 | 政府開放資料 + 新聞即時擷取 |
| 第二層 | `data/live_cache.json` | 磁碟快取（每 6 小時自動更新） |
| 第三層 | `data/taiwan_scam_data.py` | 靜態預設資料 |

排程器每 6 小時自動嘗試擷取最新資料，擷取失敗時自動降級。

### 資料一致性驗證

`taiwan_scam_data.py` 底部包含自動驗證：
```python
assert sum(v["cases"] for v in SCAM_TYPE_STATS.values()) == ANNUAL_STATS[2026]["total_cases"]
assert sum(TAIWAN_SCAM_CASES_BY_REGION.values()) == ANNUAL_STATS[2026]["total_cases"]
```

---

## 環境需求與安裝

### 環境需求

| 項目 | 版本 |
|------|------|
| Python | 3.11 以上（建議 3.11–3.13；3.14 需 `dev_shims`） |
| 作業系統 | Windows / macOS / Linux |
| Docker Desktop | 最新版（本機完整啟動建議必備：Postgres / Redis / Qdrant） |
| Ollama | 最新版（使用本地 LLM 時） |

### 步驟 1：建立虛擬環境

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 步驟 2：安裝依賴

```bash
pip install -r requirements.txt
```

### 步驟 3：設定環境變數

```bash
cp .env.example .env
```

編輯 `.env` 關鍵設定：

```env
# LLM 提供商（三選一）
LLM_PROVIDER=ollama          # 本地免費，推薦 Demo 使用
# LLM_PROVIDER=openai        # 品質最佳，需 API Key
# LLM_PROVIDER=google        # Google Gemini

# OpenAI（如使用）
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# 備援 LLM（主要失敗時自動切換）
LLM_FALLBACK=ollama
OLLAMA_MODEL=llama3.2

# API Gateway
API_KEY=test-key-001
API_GATEWAY_URL=http://localhost:8001
```

### 步驟 4：安裝 Ollama（使用本地 LLM 時）

1. 下載安裝：https://ollama.com
2. 拉取模型：`ollama pull llama3.2`
3. 確認運行：`curl http://localhost:11434/api/tags`

---

## 啟動服務

### 建議：一鍵腳本（Windows）

```powershell
.\scripts\start-dev.ps1              # Docker → API → Dashboard，並做健康檢查
.\scripts\stop-dev.ps1               # 停止 API / Dashboard
.\scripts\stop-dev.ps1 -AlsoDocker   # 連同 docker compose stop
.\scripts\start-dev.ps1 -SkipDocker  # 僅啟動前後端（容器已在跑時）
```

正確順序：**Docker Desktop → `docker compose` → API `:8001` → Dashboard `:8502`**。  
日誌與 PID 寫在 `.dev/`（已 gitignore）。若使用 Python 3.14，腳本會自動帶入 `dev_shims`（`uuid_utils` 相容 shim）。

### 手動啟動（進階）

```powershell
docker compose up -d

# 終端機 1 — API Gateway
$env:PYTHONPATH = "$PWD\dev_shims"   # 僅 Python 3.14 需要
python -m uvicorn app.api_gateway.main:app --host 0.0.0.0 --port 8001

# 終端機 2 — Dashboard
python -m streamlit run app/dashboard/streamlit_app.py --server.port 8502
```

啟動成功後確認：
- http://localhost:8001/v1/health → `"status":"healthy"`
- 瀏覽器開啟 http://localhost:8502

---

## 登入系統

系統啟動後會顯示登入/註冊頁面。

### 預設帳號

| 帳號 | 密碼 | 角色 |
|------|------|------|
| `admin` | `Aegis@2026` | 系統管理員（完整權限） |

> 帳密程式定義於 `app/dashboard/auth.py` 的 `DEMO_USERNAME` / `DEMO_PASSWORD`；修改密碼請只改該處並執行 `pytest tests/test_auth_dashboard.py`。

### 註冊新帳號

切換到「註冊」tab，輸入：
- 帳號（英文字母、數字、底線，3-20 字元）
- 顯示名稱
- 密碼（至少 6 字元）

註冊後的帳號預設為「詐騙分析師」角色。

> 注意：帳號資料存於 session-level in-memory（重啟 Streamlit 後重置，因系統目前為 in-memory 架構）。

---

## 12 個功能頁面

| # | 頁面 | 說明 | 需要 LLM |
|---|------|------|---------|
| 1 | 首頁 | KPI、台灣詐騙統計、六大模組介紹 | 否 |
| 2 | 即時威脅監控 | SOC 風格監控、預警事件串流 | 否 |
| 3 | 詐騙對話模擬器 | 與 AI 詐騙犯實戰對話（4 種情境） | 是 |
| 4 | 話術 DNA 圖譜 | 五維心理操控指標、餘弦相似度 | 否 |
| 5 | 話術進化時間軸 | 2021–2026 詐騙手法演變 | 選用 |
| 6 | 詐騙免疫訓練 | 互動訓練 + 防詐免疫證書 | 選用 |
| 7 | LLM 話術生成 | 輸入情境，生成 10–50 筆變種話術 | 是 |
| 8 | XAI 話術分析 | 規則式高亮心理操控片段 | 否 |
| 9 | 熱詞排行榜 | 38 個高頻關鍵詞 TOP 20 | 否 |
| 10 | 沙盤推演 | 情境模擬風險評估 | 否 |
| 11 | 受害風險地圖 | 年齡 × 地區風險指數矩陣 | 否 |
| 12 | 模型準確率評估 | 混淆矩陣 + 即時測試 | 否 |

---

## API 端點

所有業務端點需要 `X-API-Key` 標頭。測試用 Key：`test-key-001`

```bash
# 健康檢查（免 API Key）
curl http://localhost:8001/v1/health

# 查詢預警事件
curl -H "X-API-Key: test-key-001" http://localhost:8001/v1/predictions/alerts

# 查詢風險向量
curl -H "X-API-Key: test-key-001" http://localhost:8001/v1/risk-vectors

# XAI 高亮分析
curl -X POST http://localhost:8001/v1/analyze/highlight \
  -H "X-API-Key: test-key-001" \
  -H "Content-Type: application/json" \
  -d '{"text": "您好，我是銀行客服，您的帳戶異常，請立即提供驗證碼"}'

# 話術生成（需 LLM）
curl -X POST http://localhost:8001/v1/scam/generate \
  -H "X-API-Key: test-key-001" \
  -H "X-Operator-Id: admin" \
  -H "X-Operator-Role: SYSTEM_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"scenario": "假冒銀行客服", "target_audience": "中老年族群", "sample_count": 10}'
```

互動式 API 文件：http://localhost:8001/docs

---

## 自動化測試

```bash
# 執行全部測試
python -m pytest tests/ -v

# 各模組單獨測試
python -m pytest tests/test_dashboard.py -v
python -m pytest tests/test_api_gateway.py -v
python -m pytest tests/test_scam_engine.py -v
python -m pytest tests/test_access_control.py -v
python -m pytest tests/test_pattern_analyzer.py -v
python -m pytest tests/test_prediction_layer.py -v
python -m pytest tests/test_data_import.py -v
python -m pytest tests/test_models.py -v
```

測試類型：單元測試 + Property-Based Testing（Hypothesis）+ 整合測試

---

## 專案結構

```
AEGIS-CORE/
├── app/
│   ├── api_gateway/              # FastAPI 後端 API
│   │   ├── main.py              # 應用程式入口 + 生命週期管理
│   │   ├── middleware/          # API Key 驗證、速率限制、請求日誌
│   │   └── routers/            # health、scam、analyze、predictions、data、risk-vectors
│   ├── scam_engine/             # LLM 話術生成引擎
│   │   └── generator.py        # LangChain + 備援切換 + JSON 容錯
│   ├── pattern_analyzer/        # NLP + XAI 分析
│   │   ├── psych_classifier.py # 五類心理操控特徵分類
│   │   ├── xai_highlighter.py  # XAI 高亮標記 + 信心分數
│   │   ├── keyword_extractor.py # TF-IDF 關鍵詞
│   │   ├── clusterer.py        # K-Means + Elbow Method
│   │   └── embedder.py         # Sentence-BERT 語意嵌入
│   ├── prediction_layer/        # 預測與異常偵測
│   │   ├── analyzer.py         # Isolation Forest + 趨勢分析
│   │   ├── risk_vector.py      # Risk Vector 生成 + 儲存庫
│   │   ├── alerting.py         # 預警事件產生
│   │   ├── scheduler.py        # APScheduler 每日排程
│   │   ├── model_manager.py    # 模型版本管理
│   │   └── validator.py        # 輸入驗證
│   ├── live_data/               # 即時資料擷取
│   ├── data_import/             # 報案資料匯入 + PII 去識別
│   ├── access_controller/       # RBAC + MFA + 稽核日誌
│   ├── dashboard/               # Streamlit 前端
│   │   ├── streamlit_app.py    # 主應用（12 頁面 SPA）
│   │   ├── auth.py             # 登入/註冊/登出模組
│   │   ├── styles.py           # 全域 CSS
│   │   └── page_modules/       # 各頁面邏輯模組
│   └── config.py               # 集中設定管理（pydantic-settings）
├── data/
│   ├── taiwan_scam_data.py     # 靜態基準資料（含來源標註）
│   └── live_cache.json         # 即時快取（執行時自動產生）
├── tests/                       # 自動化測試
├── docker-compose.yml          # PostgreSQL + Redis + Qdrant（待接入）
├── .env.example                # 環境變數範本
└── requirements.txt            # Python 依賴
```

---

## 技術棧

| 類別 | 技術 |
|------|------|
| 後端 | FastAPI + Uvicorn |
| LLM | LangChain + Ollama / GPT-4o / Gemini，支援自動備援切換 |
| NLP | Sentence-BERT (paraphrase-multilingual-MiniLM-L12-v2) |
| 機器學習 | scikit-learn（TF-IDF、K-Means、Isolation Forest） |
| XAI | 規則式 Regex 高亮 + 信心分數 |
| 前端 | Streamlit（12 頁面 SPA）+ Plotly |
| 認證 | bcrypt 密碼雜湊 + RBAC 角色控制 + TOTP MFA |
| 排程 | APScheduler（預測 24h + 資料擷取 6h） |
| 儲存 | in-memory（PostgreSQL / Redis / Qdrant 已配置待接入） |
| 測試 | pytest + Hypothesis |
| 容器化 | Docker + Docker Compose |

---

## 團隊分工

| 成員 | 主責範疇 |
|------|---------|
| hank | 前端 UI / 視覺設計 / 品牌 / 部署 |
| zhiying122 | 後端引擎 / 資料系統 / 安全 / 測試 |
