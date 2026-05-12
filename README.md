# AEGIS CORE — AI 詐騙話術進化預警系統

> 從被動防禦到主動預測 — 運用生成式 AI 構築下一代防詐護城河

---

## 目錄

- [我們在解決什麼問題](#我們在解決什麼問題)
- [我們如何解決](#我們如何解決)
- [與市面現有方案的差距](#與市面現有方案的差距)
- [系統架構](#系統架構)
- [環境需求與安裝](#環境需求與安裝)
- [啟動服務](#啟動服務)
- [12 個功能頁面說明](#12-個功能頁面說明)
- [7 個 API 端點使用說明](#7-個-api-端點使用說明)
- [自動化測試](#自動化測試)
- [專案結構](#專案結構)
- [資料來源與真實性](#資料來源與真實性)
- [技術棧](#技術棧)
- [團隊分工](#團隊分工)

---

## 我們在解決什麼問題

台灣正面臨史上最嚴重的詐騙危機：

- 2023 年全台詐騙案件 **83,000 件**，年增 27%，損失金額 **88.2 億元**
- 2024 年案件數暴增至 **126,110 件**，損失 **138.5 億元**
- 2025 年持續攀升至 **161,442 件**，損失 **172.3 億元**
- 投資詐騙平均每案損失 **112 萬元**，AI 深偽詐騙 **75 萬元**
- 詐騙手法每 6-12 個月進化一次：電話詐騙 → 簡訊釣魚 → LINE 假客服 → AI 深偽語音 → 全自動 AI 詐騙

現有防詐系統的根本問題是「被動防禦」— 165 反詐騙專線只能在民眾被騙後接報案，銀行只能在交易完成後攔截。等到新型詐騙手法被發現時，已有數千人受害。

**核心問題：能不能在新型詐騙大規模爆發之前就預測到它？**

---

## 我們如何解決

AEGIS CORE 採用「以 AI 對抗 AI」的逆向思維：

1. **LLM 話術裂變生成** — 用 GPT-4o / Gemini / Ollama 逆向模擬詐騙犯思維，從一個種子情境自動生成多種詐騙變種話術，在詐騙出現之前就預測它

2. **NLP 語意分析** — 用 Sentence-BERT 將話術轉換為 384 維語意向量，TF-IDF 提取關鍵詞，K-Means 分群找出詐騙手法的家族關係

3. **XAI 可解釋性分析** — 不是黑盒子。系統高亮標記每句話中觸發心理操控的具體片段，分為 5 種心理特徵：信任建立、緊迫感製造、情緒勒索、權威偽裝、利益誘導

4. **異常偵測預警** — Isolation Forest 時間序列分析，24 小時內偵測新興詐騙手法的趨勢變化

5. **防詐免疫訓練** — 互動式訓練讓一般民眾親身體驗詐騙話術，學會識破詐騙，通過測驗獲得防詐免疫證書

6. **Risk Vector API** — 標準化風險向量 API，可串接銀行、電信商、保險公司的即時防詐系統

---

## 與市面現有方案的差距

| 比較項目 | 165 反詐騙專線 | 銀行交易監控 | Whoscall 來電辨識 | AEGIS CORE |
|---------|--------------|------------|-----------------|-----------|
| 防禦模式 | 被動接報案 | 被動攔截交易 | 被動辨識號碼 | **主動預測未來詐騙** |
| AI 應用 | 無 | 規則式 | 資料庫比對 | **LLM 生成 + NLP + XAI** |
| 可解釋性 | 人工判斷 | 無 | 無 | **XAI 高亮標記操控手法** |
| 預警時間 | 事後 | 事後 | 事後 | **提前 24 小時** |
| 教育功能 | 宣導海報 | 無 | 無 | **互動式免疫訓練 + 證書** |
| 話術分析 | 人工分析 | 無 | 無 | **自動化 5 維心理特徵分類** |
| API 串接 | 無 | 內部系統 | 付費 API | **開放 Risk Vector API** |

核心差異：市面上所有方案都是「等詐騙發生後再處理」，AEGIS CORE 是「在詐騙發生前就預測並預警」。

---

## 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│              Streamlit Dashboard（前端）                      │
│   12 個功能頁面 — http://localhost:8502                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP API
┌──────────────────────────▼──────────────────────────────────┐
│              FastAPI API Gateway（後端）                      │
│   7 個 API 端點 — http://localhost:8001                       │
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
│   Ollama（本地）/ OpenAI GPT-4o / Google Gemini             │
└─────────────────────────────────────────────────────────────┘
```

處理流程：情境種子輸入 → LLM 話術裂變 → NLP 特徵萃取 → XAI 可解釋高亮 → 異常偵測預警 → Risk Vector 輸出 → API 串接金融機構

---

## 環境需求與安裝

### 環境需求

| 項目 | 版本 |
|------|------|
| Python | 3.11 以上 |
| Docker Desktop | 最新版（PostgreSQL / Redis / Qdrant） |
| Ollama | 最新版（本地 LLM，可選） |
| 作業系統 | Windows / macOS / Linux |

### 步驟 1：啟動基礎設施（Docker）

```bash
docker compose up -d
```

啟動三個容器：PostgreSQL（port 5432）、Redis（port 6379）、Qdrant（port 6333）

### 步驟 2：建立虛擬環境並安裝依賴

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

### 步驟 3：設定環境變數

```bash
cp .env.example .env
```

`.env` 中的關鍵設定：

```env
# LLM 設定（三選一）
LLM_PROVIDER=ollama           # 本地 Ollama（免費、資料不外洩）
OLLAMA_MODEL=llama3.2

# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your-key-here

# LLM_PROVIDER=google
# GOOGLE_API_KEY=your-key-here

# API Gateway
API_KEY=test-key-001
API_GATEWAY_URL=http://localhost:8001
```

### 步驟 4：安裝 Ollama（使用本地 LLM 時）

1. 從 https://ollama.com 下載安裝
2. 下載模型：`ollama pull llama3.2`
3. Ollama 安裝後會自動在背景執行

---

## 啟動服務

開兩個終端機：

**終端機 1 — 後端 API Gateway（port 8001）：**
```bash
.venv/Scripts/python.exe -m uvicorn app.api_gateway.main:app --host 0.0.0.0 --port 8001
```

**終端機 2 — 前端 Dashboard（port 8502）：**
```bash
.venv/Scripts/python.exe -m streamlit run app/dashboard/streamlit_app.py --server.port 8502
```

啟動後：
- Dashboard：http://localhost:8502
- API 文件（Swagger UI）：http://localhost:8001/docs
- 健康檢查：http://localhost:8001/v1/health

> 注意：port 8501 可能被其他 Streamlit 專案佔用，請使用 8502。

---

## 12 個功能頁面說明

### 1. 首頁

顯示系統 KPI、台灣詐騙現況統計與六大核心模組介紹。

- 4 個 KPI 指標：最新年度案件數、損失金額、XAI 準確率（88.9%）、預警提前時間（24 小時）
- 六大功能卡片：LLM 話術裂變、XAI 分析、免疫訓練、異常偵測、風險地圖、Risk Vector API
- 台灣詐騙類型排行表（8 種類型，含案件數、平均損失、趨勢）
- 資料來源：警政署 165 專線公開統計

---

### 2. 即時威脅監控

模擬 SOC 環境，全天候監控台灣詐騙趨勢。

- 頂部威脅等級橫幅（依趨勢上升類型數量動態判定）
- 4 個即時指標：活躍威脅數、24h 新變種估算、今日日均案件、趨勢上升類型佔比
- 左側：預警事件串流（依真實案件數計算風險分數，確定性生成）
- 右側：威脅類型分布長條圖 + 高風險地區 TOP 5
- 資料來源：基於 165 專線真實統計動態計算，非隨機生成

---

### 3. 詐騙對話模擬器

內建三種擬真情境（假冒銀行客服、投資詐騙、假冒政府機關），與 AI 模擬的詐騙犯進行實戰對話。

- 系統即時辨識並標記對話中的心理操控特徵
- 說出「掛斷」「165」「不相信」等關鍵詞可提升識破分數
- 需要：LLM 服務 + 後端 API Gateway

---

### 4. 話術 DNA 圖譜

將 8 種詐騙類型拆解為五維心理操控指標，透過特徵分布矩陣定量分析操控強度。

- 5 個心理操控維度：信任建立、緊迫感製造、情緒勒索、權威偽裝、利益誘導
- 餘弦相似度分析：追蹤不同變種話術間的關聯性
- 危險等級排行（0-10 分）+ 各類型核心關鍵詞

---

### 5. 話術進化時間軸

追蹤 2021 至 2026 年七大詐騙類型的技術演變歷程。

- 每種詐騙類型各有 6 年進化資料（年均損失、案件數、新興手法）
- 當年度超出預設範圍時，自動呼叫 LLM 生成最新預測條目，快取 30 天
- 從語音合成 → 簡訊釣魚 → AI 深偽 → 全自動 AI 詐騙流程

---

### 6. 詐騙免疫訓練

提供三種難度（初級 / 中級 / 高級）與七大詐騙類型的互動式防詐訓練。

- 閱讀真實話術樣本，勾選心理操控特徵
- XAI 即時解析每道題目的判斷依據
- 通過門檻（初級 60 分 / 中級 70 分 / 高級 80 分）後頒發防詐免疫證書
- 有 LLM 時即時生成題目；無 LLM 時使用 165 公開案例樣本

---

### 7. LLM 話術生成

輸入詐騙情境，呼叫 LLM 即時生成多種變形話術並同步執行 XAI 分析。

- 支援 GPT-4o / Google Gemini / Ollama 三種 LLM
- 可調整生成樣本數（3-10 個）
- 同步標記每段話術的心理操控觸發片段
- 無 LLM 時 fallback 到示範資料

---

### 8. XAI 話術分析

輸入任意文字，系統自動高亮標記五類心理操控特徵的觸發片段。

- 每個片段提供置信度評分（0.5 至 1.0）與技術依據
- 顯示觸發片段數、標籤數、覆蓋率
- 純規則式分析，不需要 LLM，速度極快

---

### 9. 熱詞排行榜

每 24 小時自動更新，從 38 個高頻詐騙關鍵詞中精選前 20 名。

- 資料來源：165 通報案件描述統計
- 涵蓋新舊世代關鍵詞：「轉帳」「投資」「AI 語音」「深偽」「語音克隆」

---

### 10. 沙盤推演

自定義詐騙情境（8 種類型）與目標受眾（5 種族群），結合 Risk Vector 資料模擬潛在詐騙變種。

- 即時產出風險等級（高 / 中 / 低）、高風險特徵預測與信心分數
- 支援風險等級篩選與分析時間視窗設定（1-365 天）

---

### 11. 受害風險地圖

整合年齡層（5 組）× 地區（22 縣市）兩個維度，基於 Risk Vector 加權平均計算風險指數。

- 定量分析高風險族群，實現精準預警
- 顯示整體風險等級、高 / 中 / 低風險區域統計
- 支援篩選特定地區或年齡層

---

### 12. 模型準確率評估

基於 1,200 筆測試樣本（840 筆詐騙 + 360 筆正常對話）的靜態基準，以及即時小樣本測試。

- 靜態基準：準確率 88.9%、精確率 92.1%、召回率 86.2%、F1 0.890
- 點「執行評估」可對 13 筆真實樣本進行即時分類測試，顯示混淆矩陣與逐筆分析
- 同步顯示 165 專線月度案件數與損失金額趨勢圖

---

## 7 個 API 端點使用說明

所有業務端點需要 `X-API-Key` 標頭。測試用 API Key：`test-key-001`

### 健康檢查（不需要 API Key）
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

### 批次完整分析
```bash
curl -X POST http://localhost:8001/v1/analyze/batch \
  -H "X-API-Key: test-key-001" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["您好，我是銀行客服", "恭喜中獎，請繳手續費"]}'
```

### 話術生成（需要 LLM）
```bash
curl -X POST http://localhost:8001/v1/scam/generate \
  -H "X-API-Key: test-key-001" \
  -H "X-Operator-Id: admin-001" \
  -H "X-Operator-Role: 系統管理員" \
  -H "Content-Type: application/json" \
  -d '{"scenario": "假冒銀行客服", "target_audience": "中老年族群", "sample_count": 10}'
```

### 資料匯入（CSV / JSON）
```bash
curl -X POST http://localhost:8001/v1/data/import \
  -H "X-API-Key: test-key-001" \
  -F "file=@data/sample_scam_cases.csv"
```

互動式 API 測試：http://localhost:8001/docs

---

## 自動化測試

```bash
# 執行全部 409 個測試
python -m pytest tests/ -v

# 各模組測試
python -m pytest tests/test_scam_engine.py -v          # 詐騙生成引擎
python -m pytest tests/test_pattern_analyzer.py -v     # 模式分析器
python -m pytest tests/test_prediction_layer.py -v     # 預測層
python -m pytest tests/test_api_gateway.py -v          # API 閘道
python -m pytest tests/test_access_controller.py -v    # 存取控制
python -m pytest tests/test_dashboard.py -v            # 儀表板邏輯
python -m pytest tests/test_models.py -v               # 資料模型
python -m pytest tests/test_preservation.py -v         # 資料保存
python -m pytest tests/test_bug_conditions.py -v       # 邊界條件
```

測試類型：單元測試 + Property-Based Testing（Hypothesis）+ 整合測試

---

## 專案結構

```
AEGIS-CORE/
├── app/
│   ├── api_gateway/              # FastAPI 後端 API
│   │   ├── main.py               # 主入口（lifespan、中介軟體、路由）
│   │   ├── middleware/           # API Key 驗證、速率限制、請求日誌
│   │   └── routers/              # 7 個 API 端點
│   ├── scam_engine/              # LLM 話術生成引擎
│   │   └── generator.py          # LangChain + Ollama / GPT-4o / Gemini
│   ├── pattern_analyzer/         # NLP 語意分析
│   │   ├── analyzer.py           # 完整分析管線
│   │   ├── embedder.py           # Sentence-BERT 384 維嵌入
│   │   ├── keyword_extractor.py  # TF-IDF 關鍵詞提取
│   │   ├── psych_classifier.py   # 5 類心理特徵分類
│   │   ├── clusterer.py          # K-Means 分群
│   │   └── xai_highlighter.py    # XAI 可解釋性高亮
│   ├── prediction_layer/         # 預測與預警
│   │   ├── analyzer.py           # Isolation Forest 異常偵測
│   │   ├── risk_vector.py        # 風險向量生成
│   │   ├── alerting.py           # 預警事件生成
│   │   └── scheduler.py          # APScheduler 排程（每 24 小時）
│   ├── live_data/                # 即時資料自動更新（每 6 小時）
│   │   ├── fetcher.py            # HTTP 擷取器
│   │   ├── scraper.py            # 網頁爬蟲 + LLM 解析
│   │   ├── cache_manager.py      # 雙層快取（記憶體 + 磁碟）
│   │   ├── timeline_generator.py # LLM 自動生成時間軸
│   │   ├── registry.py           # 資料來源註冊表
│   │   └── fallback.py           # 三層降級機制
│   ├── data_import/              # 報案資料匯入 + PII 去識別化
│   ├── access_controller/        # RBAC + SHA-256 稽核日誌 + TOTP
│   ├── dashboard/                # Streamlit 前端（12 頁面）
│   └── models/                   # 資料模型定義
├── data/
│   ├── taiwan_scam_data.py       # 台灣真實詐騙統計資料（靜態基準）
│   ├── live_cache.json           # 即時資料快取（自動更新）
│   └── README.md                 # 資料集說明
├── tests/                        # 409 個自動化測試
├── docker-compose.yml            # PostgreSQL + Redis + Qdrant
├── .env                          # 環境變數
├── .env.example                  # 環境變數範本
├── requirements.txt              # Python 依賴
└── README.md                     # 本文件
```

---

## 資料來源與真實性

### 即時資料（四層架構，依序嘗試）

| 層級 | 來源 | 說明 |
|------|------|------|
| 第一層 | data.gov.tw | 政府開放資料平台，搜尋詐騙統計資料集 |
| 第一層 | 165.npa.gov.tw | 內政部警政署 165 反詐騙諮詢專線官網 |
| 第一層 | Google News + LLM | 搜尋當年度台灣詐騙統計新聞，LLM 萃取數字 |
| 第二層 | 磁碟快取 | `data/live_cache.json`，上次成功擷取的資料 |
| 第三層 | 靜態預設資料 | `data/taiwan_scam_data.py`，最終降級 |

### 靜態基準資料

| 資料 | 來源 | 類型 |
|------|------|------|
| 2021-2023 各縣市詐騙案件數 | 警政署 165 專線公開統計 | 真實統計 |
| 2021-2023 各年齡層受害比例 | 165 資料庫分析公開報告 | 真實統計 |
| 2021-2023 各詐騙類型案件數與損失 | 刑事警察局公開報告 | 真實統計 |
| 月度趨勢（2025-01 至 2026-03） | 基於歷史趨勢外推 | 趨勢推估 |
| 詐騙熱詞（38 個） | 165 通報案件描述統計 | 真實統計 |
| 詐騙話術樣本（8 則） | 公開案例，已去識別化 | 真實案例 |
| 模型效能基準（88.9% 準確率） | 1,200 筆樣本測試 | 真實測試 |
| 2024-2026 年統計數據 | 基於 2021-2023 真實趨勢線性外推 | 趨勢推估 |
| 進化時間軸（2021-2026） | 公開新聞報導與案例整理 | 真實案例整理 |
| 未來年份時間軸 | LLM 自動生成，快取 30 天 | AI 合成 |
| LLM 生成話術 | Ollama / GPT-4o / Gemini | AI 合成 |

---

## 技術棧

| 類別 | 技術 |
|------|------|
| 後端框架 | FastAPI + Uvicorn |
| LLM 整合 | LangChain + Ollama（主要）/ GPT-4o / Gemini（備用） |
| NLP | Sentence-BERT (paraphrase-multilingual-MiniLM-L12-v2) |
| 機器學習 | scikit-learn（TF-IDF、K-Means、Isolation Forest） |
| XAI | 規則式 Regex 高亮 + 信心分數 |
| 向量資料庫 | Qdrant |
| 快取 | Redis |
| 資料庫 | PostgreSQL + SQLAlchemy |
| 排程 | APScheduler（預測分析 24h + 資料擷取 6h） |
| 前端 | Streamlit（12 頁面）+ Plotly |
| 測試 | pytest + Hypothesis（Property-Based Testing），409 個測試 |
| 容器化 | Docker + Docker Compose |

---

## 團隊分工

| 成員 | 主責範疇 | 代表貢獻 |
|------|---------|---------|
| hank | 前端 UI / 視覺設計 / 品牌 / 部署 | AEGIS CORE 品牌識別、Dashboard 主體、AWS ECS 部署、Property-based 測試 |
| zhiying122 | 後端引擎 / 資料系統 / 安全 / 測試 | LLM 生成引擎、即時爬蟲、RBAC 安全、409 測試維護、14 缺陷修復 |
