# 🔮 ScamOracle — 全境式變種詐騙先知系統
### ScamOracle: Omniscient Scam Variant Prediction System

> 從被動防禦到主動預測，運用生成式 AI 構築下一代防詐護城河

---

## 專案簡介

本系統透過大型語言模型（LLM）逆向模擬詐騙邏輯，主動生成並預測未來可能出現的變種詐騙話術。結合 NLP 語意分析與可解釋性 AI（XAI），在新型詐騙大規模爆發前提前預警。

---

## 目前實作進度

### ✅ 已完成模組

| 模組 | 說明 |
|------|------|
| **API Gateway** | FastAPI 主入口、API 金鑰驗證、速率限制（滑動視窗）、請求日誌 |
| **Access Controller** | RBAC 角色權限、稽核日誌（SHA-256 防竄改雜湊鏈）、TOTP 二次驗證 |
| **Scam Generation Engine** | LLM 話術生成（LangChain + GPT-4o/Gemini）、指數退避重試、結構化錯誤處理 |
| **Pattern Analyzer** | Sentence-BERT 語意嵌入（384 維）、TF-IDF 關鍵詞提取、心理特徵分類（5 類）、K-Means 分群 |
| **XAI 可解釋性輸出** | 高亮顯示觸發心理操控特徵的話術片段、字元位置標記、信心分數、`/v1/analyze/highlight` API |
| **Prediction Layer** | 異常偵測（Isolation Forest）、趨勢分析、Risk Vector 生成、預警事件、APScheduler 排程 |
| **Data Import** | CSV/JSON 報案資料匯入、PII 自動去識別化、模型增量微調與版本管理 |
| **Dashboard Logic** | 熱詞排行榜、沙盤推演、受害風險地圖、快取降級機制 |
| **Streamlit 儀表板** | 熱詞排行榜、XAI 高亮分析、沙盤推演、受害風險地圖、資料匯入清洗（5 頁完整 UI） |
| **資料集 Pipeline** | 範例詐騙案例 CSV（10 筆、7 種類型）、上傳清洗流程、統計摘要、清洗後匯出 |
| **AWS 雲端部署** | Dockerfile × 2、ECS Task Definitions、一鍵部署腳本（`deploy.sh`）、基礎設施初始化（`aws/setup.sh`） |



---

## 技術架構

```
Python 3.11+ / FastAPI
├── LLM 整合：LangChain + GPT-4o / Gemini API
├── NLP：Sentence-BERT、scikit-learn（TF-IDF、K-Means）
├── XAI：規則式 Regex 高亮、信心分數計算
├── 異常偵測：pyod（Isolation Forest）
├── 排程：APScheduler
├── 向量資料庫：Qdrant
├── 快取：Redis
├── 資料庫：PostgreSQL
├── 前端：Streamlit（5 頁完整 UI）
└── 雲端：AWS ECS Fargate + ECR
```

---

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

```bash
cp .env.example .env
# 編輯 .env，填入 OpenAI API Key 等設定
```

### 3. 啟動服務（需要 Docker）

```bash
docker-compose up -d
```

### 4. 啟動 API Server

```bash
uvicorn app.api_gateway.main:app --reload
```

API 文件：`http://localhost:8000/docs`

### 5. 啟動 Streamlit 儀表板

```bash
streamlit run streamlit_app/app.py
```

儀表板：`http://localhost:8501`

---

## 測試

```bash
python -m pytest tests/ -v
```

目前共 **309 個測試**，全部通過。

---

## 專案結構

```
app/
├── api_gateway/        # FastAPI 主入口與中介軟體
├── access_controller/  # RBAC、稽核日誌、TOTP
├── scam_engine/        # LLM 話術生成引擎
├── pattern_analyzer/   # 語意分析、特徵萃取、XAI 高亮
├── prediction_layer/   # 趨勢預測與異常偵測
├── data_import/        # 報案資料匯入與 PII 處理
├── dashboard/          # 視覺化儀表板邏輯
└── models/             # 資料模型定義
streamlit_app/
├── app.py              # 儀表板主入口
├── pages/              # 5 個功能頁面
└── utils/              # 共用工具與 mock 資料
data/
└── sample_scam_cases.csv  # 範例詐騙案例資料集
aws/
├── setup.sh            # 基礎設施初始化
└── ecs/                # ECS Task Definitions
tests/                  # 測試套件（309 tests）
deploy.sh               # AWS 一鍵部署腳本
```

---

## 團隊分工

| 成員 | 負責範疇 |
|------|---------|
| Member A | 後端、AI 模型、雲端架構（FastAPI、LLM、AWS） |
| Member B | 資料處理、前端介面、版本控制、簡報（Streamlit、GitHub） |
