# ScamDNA 啟動與測驗指南

> 這份文件告訴你如何從零啟動整個系統、驗證所有功能、以及如何跑自動化測試。

---

## 一、前置準備（只需做一次）

```powershell
# 1. 進入專案目錄
cd e:\GitHub\Scam-Prediction-System

# 2. 建立虛擬環境（如果還沒建）
python -m venv .venv

# 3. 啟動虛擬環境
.venv\Scripts\activate

# 4. 安裝所有依賴
pip install -r requirements.txt

# 5. 設定環境變數
copy .env.example .env
```

### 編輯 `.env` 關鍵設定

最簡單的方式是用 **Ollama（免費、本地、免 API Key）**：

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
LLM_FALLBACK=ollama
API_KEY=test-key-001
API_GATEWAY_URL=http://localhost:8001
```

如果要用 OpenAI GPT-4o（品質最佳）：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-你的key
OPENAI_MODEL=gpt-4o
LLM_FALLBACK=ollama
API_KEY=test-key-001
API_GATEWAY_URL=http://localhost:8001
```

### 安裝 Ollama（使用本地 LLM 時）

1. 下載安裝：https://ollama.com
2. 拉取模型：`ollama pull llama3.2`
3. 確認運行：`curl http://localhost:11434/api/tags`

---

## 二、啟動系統

系統由三個部分組成：Docker 基礎設施 → API Gateway（後端）→ Dashboard（前端）

### 方式 A：一鍵腳本（推薦）

```powershell
.\scripts\start-dev.ps1
```

這會自動啟動 Docker 容器 → API Gateway → Dashboard，並做健康檢查。

停止：
```powershell
.\scripts\stop-dev.ps1               # 停止 API / Dashboard
.\scripts\stop-dev.ps1 -AlsoDocker   # 連同 Docker 容器一起停
```

### 方式 B：手動啟動（開三個終端機）

**終端機 1 — Docker 基礎設施**（可選，不開不影響 Demo）

```powershell
docker compose up -d
```

**終端機 2 — API Gateway（後端 :8001）**

```powershell
cd e:\GitHub\Scam-Prediction-System
.venv\Scripts\activate
python -m uvicorn app.api_gateway.main:app --host 0.0.0.0 --port 8001
```

看到 `Uvicorn running on http://0.0.0.0:8001` 表示成功。

**終端機 3 — Dashboard（前端 :8502）**

```powershell
cd e:\GitHub\Scam-Prediction-System
.venv\Scripts\activate
python -m streamlit run app/dashboard/streamlit_app.py --server.port 8502
```

瀏覽器會自動打開 `http://localhost:8502`。

### 啟動確認

| 服務 | 網址 | 驗證方式 |
|------|------|---------|
| Dashboard | http://localhost:8502 | 看到登入頁面 |
| API 文件（Swagger） | http://localhost:8001/docs | 看到 API 文件 |
| 健康檢查 | http://localhost:8001/v1/health | 回傳 `"status":"healthy"` |

---

## 三、登入系統

| 帳號 | 密碼 | 角色 |
|------|------|------|
| `admin` | `Aegis@2026` | 系統管理員（完整權限） |

也可以在登入頁切換到「註冊」Tab 建立新帳號（新帳號預設為「詐騙分析師」角色）。

---

## 四、測驗 12 個功能頁面

登入後依照導覽列逐一點擊，驗證各頁面功能：

| # | 頁面 | 怎麼測 | 需要 LLM？ |
|---|------|--------|-----------|
| 1 | **首頁** | 登入後直接看到 KPI 卡片（案件數、損失金額等）和六大模組介紹 | 否 |
| 2 | **威脅監控** | 點「威脅監控」→ 看 SOC 風格面板、預警事件串流 | 否 |
| 3 | **對話模擬器** | 選情境（假冒銀行客服/投資詐騙/愛情詐騙/假冒政府機關）→ 和 AI 詐騙犯對話，觀察即時操控手法標記 | **是** |
| 4 | **DNA 圖譜** | 看各詐騙類型的五維心理操控雷達圖 + 餘弦相似度 | 否 |
| 5 | **進化時間軸** | 觀看 2021–2026 詐騙手法演化歷程 | 否 |
| 6 | **免疫訓練** | 選難度 → 做題 → 累積達標後頒發防詐免疫證書 | 選用 |
| 7 | **LLM 生成** | 輸入情境描述（如「假冒銀行客服」）→ 設定樣本數 → 點生成 → 等待 LLM 回傳 10-50 筆話術 | **是** |
| 8 | **XAI 分析** | 貼入一段話術文字 → 看高亮標記（五類心理操控片段 + 信心分數） | 否 |
| 9 | **熱詞排行** | 直接看 TOP 20 詐騙高頻關鍵詞統計圖 | 否 |
| 10 | **沙盤推演** | 選擇情境模擬風險評估 | 否 |
| 11 | **風險地圖** | 年齡層 × 地區風險指數矩陣 | 否 |
| 12 | **模型評估** | 混淆矩陣 + 各類型準確率（88.9%） | 否 |

> 💡 **不需要 LLM 的頁面（10 個）可以完全離線使用**，只有對話模擬器和 LLM 生成需要 Ollama 或 OpenAI。

---

## 五、測試 API 端點

另開一個終端機，用 curl 或 PowerShell 測試：

```powershell
# 健康檢查（免 API Key）
curl http://localhost:8001/v1/health

# XAI 高亮分析
curl -X POST http://localhost:8001/v1/analyze/highlight `
  -H "X-API-Key: test-key-001" `
  -H "Content-Type: application/json" `
  -d '{\"text\": \"您好，我是銀行客服，您的帳戶異常，請立即提供驗證碼\"}'

# 查詢風險向量
curl -H "X-API-Key: test-key-001" http://localhost:8001/v1/risk-vectors

# 查詢預警事件
curl -H "X-API-Key: test-key-001" http://localhost:8001/v1/predictions/alerts
```

互動式 API 文件（瀏覽器）：http://localhost:8001/docs

---

## 六、執行自動化測試

```powershell
# 啟動虛擬環境
.venv\Scripts\activate

# 全部測試（394+ 筆，約 2 分鐘）
python -m pytest tests/ -v

# 快速執行（只看結果）
python -m pytest tests/ -q --tb=short

# 各模組單獨測試
python -m pytest tests/test_dashboard.py -v          # Dashboard 邏輯
python -m pytest tests/test_api_gateway.py -v        # API Gateway
python -m pytest tests/test_scam_engine.py -v        # LLM 話術生成
python -m pytest tests/test_access_control.py -v     # RBAC + MFA + 稽核日誌
python -m pytest tests/test_pattern_analyzer.py -v   # NLP + XAI
python -m pytest tests/test_prediction_layer.py -v   # 異常偵測 + Risk Vector
python -m pytest tests/test_data_import.py -v        # 資料匯入 + PII
python -m pytest tests/test_models.py -v             # 資料模型
python -m pytest tests/test_auth_dashboard.py -v     # 登入認證
python -m pytest tests/test_scam_simulator.py -v     # 對話模擬器

# 測試覆蓋率報告
python -m pytest tests/ --cov=app --cov-report=term-missing
```

---

## 七、常見問題

### Q: LLM 生成頁面顯示逾時？
Ollama 首次載入模型較慢（1-2 分鐘），等它載完再試。或把樣本數量減少為 5 筆。

### Q: Docker 沒裝可以跑嗎？
可以。系統使用 in-memory 儲存，不啟動 Docker 只是沒有 PostgreSQL/Redis/Qdrant 持久化，所有 Demo 功能完全不受影響。

### Q: 不用 Ollama 可以嗎？
可以。在 `.env` 設定 `LLM_PROVIDER=openai` 並填入 `OPENAI_API_KEY`，就會用 GPT-4o。不過需要 LLM 的頁面只有第 3、7 頁，其他 10 頁全部可以離線運作。

### Q: 如何修改 Demo 帳號密碼？
修改 `app/dashboard/auth.py` 中的 `DEMO_PASSWORD` 常數，然後跑 `pytest tests/test_auth_dashboard.py` 確認通過。

### Q: API 回傳 401 Unauthorized？
確認請求帶有 `X-API-Key: test-key-001` 標頭（Key 值須與 `.env` 中的 `API_KEY` 一致）。

### Q: Streamlit 啟動後白畫面？
確認 API Gateway 已經在 :8001 跑起來。Dashboard 需要呼叫後端 API。

---

## 八、正確啟動順序總結

```
1. Docker Desktop（啟動）        ← 可選
2. docker compose up -d          ← 可選
3. uvicorn（API Gateway :8001）  ← 必要
4. streamlit（Dashboard :8502）  ← 必要
5. 瀏覽器開 http://localhost:8502
6. 登入 admin / Aegis@2026
7. 逐頁測試功能
```

---

*最後更新：2026-08-03*
