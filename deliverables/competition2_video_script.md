

# ScamOracle — AI 詐騙進化預測系統

## AI 應用技術與架構設計大賽 影片腳本

> **影片總長度：2 分鐘（120 秒） ｜ 分鏡數：7**
>
> **敘事主軸：** 專案概述 → 系統架構 → 程式碼品質 → AI 輔助開發
>
> **AI 模型：** Meta Llama 3（透過 Ollama 本地部署）、Google Gemini

---

## 影片結構總覽

| 分鏡 | 時間碼 | 內容摘要 | 技術重點 |
|------|--------|---------|---------|
| 1 | 0:00–0:20 | 專案概述與技術定位 | 四層架構、10 模組、410 測試 |
| 2 | 0:20–0:50 | 四層系統架構動畫流程 | Input → Engine → Analysis → Output |
| 3 | 0:50–1:10 | 程式碼片段展示 | LangChain Prompt + S-BERT 384 維 |
| 4 | 1:10–1:25 | 自動化測試執行畫面 | 410 測試全數通過 |
| 5 | 1:25–1:40 | Docker Compose + API Swagger UI | PostgreSQL、Redis、Qdrant + 7 端點 |
| 6 | 1:40–1:50 | AI 輔助開發工具 | GitHub Copilot |
| 7 | 1:50–2:00 | 結尾：技術棧總覽與團隊 | 完整技術棧 |

---

## 分鏡腳本

---

### 分鏡 1 ｜ 開場：專案概述與技術定位

| 項目 | 內容 |
|------|------|
| **分鏡編號** | Scene 1 |
| **時間碼** | 0:00 – 0:20（20 秒） |
| **技術標註** | 四層架構、10 核心模組、410 自動化測試 |

**🎬 畫面描述：**

畫面以深藍色科技風格背景開場。ScamOracle 的品牌 Logo 以粒子匯聚效果成形於畫面中央，下方浮現副標題「AI 詐騙進化預測系統」。Logo 定位後，畫面右側以動態數據卡片依序浮現系統規模指標：「10 核心模組」「12 功能頁面」「7 API 端點」「410 自動化測試」。畫面底部以技術標籤列展示核心技術棧：Meta Llama 3（透過 Ollama 本地部署） ｜ Google Gemini ｜ paraphrase-multilingual-MiniLM-L12-v2 ｜ Isolation Forest ｜ K-Means。最後畫面過渡至四層架構的縮略圖預覽，為下一個分鏡做鋪墊。

**🎙️ 旁白文字：**

「ScamOracle — AI 詐騙進化預測系統。這是一套以四層架構設計的 AI 詐騙預測系統，包含 10 個核心模組、12 個互動式功能頁面、7 個標準化 REST API 端點，並以 410 個自動化測試確保系統品質。接下來，讓我們深入系統架構。」

**📝 技術標註：**

- `Architecture: 4-Layer (Input → Engine → Analysis → Output)`
- `Modules: 10 core packages`
- `Tests: 410 (Unit + PBT + Integration)`
- `AI: Meta Llama 3（透過 Ollama 本地部署）, Google Gemini`

---

### 分鏡 2 ｜ 四層系統架構動畫流程

| 項目 | 內容 |
|------|------|
| **分鏡編號** | Scene 2 |
| **時間碼** | 0:20 – 0:50（30 秒） |
| **技術標註** | Input → Engine → Analysis → Output、S-BERT 384 維、Isolation Forest |

**🎬 畫面描述：**

畫面展開為全螢幕的系統架構動畫。四個架構層以水平方塊從左到右依序浮現，每層以不同顏色區分：Input Layer（綠色）→ Engine Layer（藍色）→ Analysis Layer（橙色）→ Output Layer（紫色）。

資料流動畫以發光粒子從左側 Input Layer 出發，流經每一層時觸發該層的技術元件動畫：Engine Layer 中 LangChain Prompt 模板與 S-BERT 384 維嵌入的處理動畫；Analysis Layer 中 Isolation Forest 異常偵測與 K-Means 分群的分析動畫；最終到達 Output Layer 的 Streamlit Dashboard 與 REST API 輸出。

每層方塊內部展示該層包含的核心模組名稱：Engine Layer 顯示 scam_engine + pattern_analyzer；Analysis Layer 顯示 prediction_layer；Output Layer 顯示 dashboard + api_gateway。底部以三個圖示展示基礎設施：PostgreSQL ｜ Redis ｜ Qdrant。

**🎙️ 旁白文字：**

「ScamOracle 採用四層架構設計。Input Layer 接收使用者輸入的詐騙情境，經由 FastAPI API Gateway 進行參數驗證與路由。Engine Layer 是系統核心 — LangChain 整合 Meta Llama 3（透過 Ollama 本地部署） 與 Google Gemini 進行話術裂變生成，同時 Sentence-BERT 產生 384 維語意向量。Analysis Layer 使用 Isolation Forest 進行異常偵測，K-Means 進行語意分群，在 24 小時內發出預警。最終 Output Layer 透過 12 個 Streamlit 頁面與 7 個 REST API 端點輸出結果。底層由 PostgreSQL、Redis、Qdrant 三項 Docker 服務支撐。」

**📝 技術標註：**

- `Input: FastAPI + Uvicorn, API Key Auth, Rate Limiting`
- `Engine: LangChain + Ollama, S-BERT 384d, TF-IDF, Regex Classifier`
- `Analysis: Isolation Forest, K-Means, Risk Vector, APScheduler`
- `Output: Streamlit (12 pages), REST API (7 endpoints)`
- `Infra: PostgreSQL, Redis, Qdrant (Docker Compose)`

---

### 分鏡 3 ｜ 程式碼片段展示

| 項目 | 內容 |
|------|------|
| **分鏡編號** | Scene 3 |
| **時間碼** | 0:50 – 1:10（20 秒） |
| **技術標註** | LangChain Prompt Template、S-BERT Embedding Pipeline |

**🎬 畫面描述：**

畫面分割為左右兩個程式碼編輯器視窗，模擬 VS Code 深色主題。

**左側程式碼片段 — `scam_engine/generator.py`（LangChain Prompt 設計）：**

```python
# scam_engine/generator.py — LangChain Prompt 模板
_SYSTEM_PROMPT = """你是一個專業的詐騙話術分析研究員，
協助防詐機構研究詐騙手法。
請嚴格按照 JSON 格式輸出：
{
  "samples": [{
    "content": "詐騙話術文本",
    "psychological_tags": ["心理操控類別"],
    "target_audience": "目標受眾"
  }]
}
心理操控類別：
- 信任建立
- 緊迫感製造
- 情緒勒索
- 權威偽裝
- 利益誘導
"""

SCAM_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessage(content=_SYSTEM_PROMPT),
    HumanMessage(content=_HUMAN_PROMPT),
])
```

**右側程式碼片段 — `pattern_analyzer/embedder.py`（S-BERT 嵌入流程）：**

```python
# pattern_analyzer/embedder.py — S-BERT 語意嵌入
EMBEDDING_DIM: int = 384

class LanguageEmbedder:
    def __init__(self, model_name: str =
            "paraphrase-multilingual-MiniLM-L12-v2"):
        self._model_name = model_name
        self._model = None  # 延遲載入

    def embed(self, text: str) -> EmbeddingResult:
        lang = detect_language(text)
        if not is_supported_language(lang):
            return EmbeddingResult(
                language="unsupported",
                embedding=None, is_supported=False)
        model = self._load_model()
        raw = model.encode(text, convert_to_numpy=True)
        embedding = raw.tolist()
        _validate_embedding(embedding)
        return EmbeddingResult(
            language=lang, embedding=embedding,
            is_supported=True)
```

畫面中央以動畫箭頭連接兩個程式碼片段，標示資料流方向：Scam Engine 生成話術 → Pattern Analyzer 進行語意嵌入。程式碼中的關鍵技術詞彙以高亮色標記：`ChatPromptTemplate`（藍色）、`384`（金色）、`paraphrase-multilingual-MiniLM-L12-v2`（綠色）。

**🎙️ 旁白文字：**

「讓我們看看核心程式碼。左側是 Scam Engine 的 LangChain Prompt 模板設計 — 我們精心設計了 System Prompt，將 LLM 定位為詐騙話術分析研究員，並要求以結構化 JSON 格式輸出，確保程式可解析。右側是 Pattern Analyzer 的 Sentence-BERT 嵌入流程 — 使用 paraphrase-multilingual-MiniLM-L12-v2 模型，將每段話術轉換為 384 維語意向量，支援中英文雙語偵測，並內建 NaN/Inf 驗證確保向量品質。」

**📝 技術標註：**

- `Left: scam_engine/generator.py — LangChain ChatPromptTemplate`
- `Right: pattern_analyzer/embedder.py — S-BERT 384d embedding`
- `Model: paraphrase-multilingual-MiniLM-L12-v2`
- `Output: JSON structured response with psychological_tags`

---

### 分鏡 4 ｜ 自動化測試執行畫面

| 項目 | 內容 |
|------|------|
| **分鏡編號** | Scene 4 |
| **時間碼** | 1:10 – 1:25（15 秒） |
| **技術標註** | pytest + Hypothesis、410 測試、三種測試類型 |

**🎬 畫面描述：**

畫面切換為全螢幕終端機視窗，模擬 pytest 測試執行過程。終端機以深色背景 + 綠色文字呈現，上方顯示執行命令：

```
$ python -m pytest tests/ -v --tb=short
```

畫面以加速播放方式展示測試執行過程，綠色 `PASSED` 標記快速滾動。測試檔案名稱依序閃過：`test_scam_engine.py`、`test_pattern_analyzer.py`、`test_prediction_layer.py`、`test_api_gateway.py`、`test_access_control.py`、`test_data_import.py`、`test_dashboard.py`、`test_models.py`。

最終畫面停留在測試結果摘要：

```
========================= test session starts ==========================
collected 410 items

tests/test_scam_engine.py ......................................... PASSED
tests/test_pattern_analyzer.py ................................... PASSED
tests/test_prediction_layer.py ................................... PASSED
tests/test_api_gateway.py ........................................ PASSED
tests/test_access_control.py ..................................... PASSED
tests/test_data_import.py ........................................ PASSED
tests/test_dashboard.py .......................................... PASSED
tests/test_models.py ............................................. PASSED

=============== 410 passed in 45.2s ================
```

畫面右側以浮動卡片展示測試類型分布：單元測試、Property-Based Testing（Hypothesis）、整合測試。

**🎙️ 旁白文字：**

「系統品質由 410 個自動化測試保障。我們採用三種測試策略：單元測試驗證各模組核心函數的正確性；Property-Based Testing 使用 Hypothesis 框架，透過隨機生成輸入驗證系統屬性的普遍性；整合測試驗證模組間的協作正確性。全部 410 個測試，全數通過。」

**📝 技術標註：**

- `Framework: pytest + Hypothesis`
- `Total: 410 tests (Unit + PBT + Integration)`
- `Coverage: scam_engine, pattern_analyzer, prediction_layer, api_gateway, access_controller, data_import, dashboard, models`

---

### 分鏡 5 ｜ Docker Compose + API Swagger UI

| 項目 | 內容 |
|------|------|
| **分鏡編號** | Scene 5 |
| **時間碼** | 1:25 – 1:40（15 秒） |
| **技術標註** | Docker Compose 3 服務、FastAPI Swagger UI |

**🎬 畫面描述：**

畫面分割為上下兩部分。

**上半部 — Docker Compose 服務啟動：**

終端機視窗展示 Docker Compose 啟動過程：

```
$ docker compose up -d
[+] Running 3/3
 ✔ Container scam_prediction_postgresql  Started
 ✔ Container scam_prediction_redis  Started
 ✔ Container scam_prediction_qdrant  Started

$ docker compose ps
NAME                          STATUS
scam_prediction_postgresql     running (healthy)
scam_prediction_redis     running (healthy)
scam_prediction_qdrant     running (healthy)
```

**下半部 — FastAPI Swagger UI：**

瀏覽器視窗展示 `http://localhost:8000/docs` 的 Swagger UI 介面，顯示 7 個 API 端點列表。滑鼠點擊展開 `/v1/analyze/highlight` 端點，展示請求參數與回應格式。

**🎙️ 旁白文字：**

「基礎設施方面，ScamOracle 使用 Docker Compose 管理 PostgreSQL、Redis、Qdrant 三項服務，一鍵啟動完整開發環境。後端 API 基於 FastAPI 框架，提供 7 個標準化 REST API 端點，內建 Swagger UI 互動式文件，支援即時測試。」

**📝 技術標註：**

- `Docker: PostgreSQL, Redis, Qdrant`
- `API: FastAPI 7 endpoints`
- `Docs: Swagger UI at /docs`

---

### 分鏡 6 ｜ AI 輔助開發工具

| 項目 | 內容 |
|------|------|
| **分鏡編號** | Scene 6 |
| **時間碼** | 1:40 – 1:50（10 秒） |
| **技術標註** | GitHub Copilot、Prompt Engineering |

**🎬 畫面描述：**

畫面展示 VS Code 編輯器介面，右下角顯示 GitHub Copilot 圖示（已啟用狀態）。編輯器中開啟 `pattern_analyzer/psych_classifier.py`，游標停在一個新函數定義處。Copilot 以灰色文字建議程式碼補全 — 自動建議心理特徵分類器的 Regex 模式。開發者按下 Tab 鍵接受建議，程式碼以動畫效果填入。

畫面右側以浮動卡片展示 AI 輔助開發的應用場景：程式碼自動補全、測試程式碼生成、文件字串生成、正則表達式輔助。

**🎙️ 旁白文字：**

「開發過程中，我們使用 GitHub Copilot 作為 AI 程式碼輔助工具，加速日常編碼、測試撰寫與文件生成。搭配精心設計的 Prompt Engineering，透過 Ollama 本地部署的 Meta Llama 3 模型，實現高品質的話術裂變生成。」

**📝 技術標註：**

- `AI Dev Tools: GitHub Copilot`
- `Prompt Engineering: Ollama + Meta Llama 3`
- `Use Cases: Code completion, Test generation, Docstring, Regex patterns`

---

### 分鏡 7 ｜ 結尾：技術棧總覽與團隊

| 項目 | 內容 |
|------|------|
| **分鏡編號** | Scene 7 |
| **時間碼** | 1:50 – 2:00（10 秒） |
| **技術標註** | 完整技術棧、團隊分工 |

**🎬 畫面描述：**

畫面以優雅動畫收束。ScamOracle 品牌 Logo 居中，下方以圖示列展示完整技術棧：FastAPI + Uvicorn ｜ LangChain + Ollama（主要）/ GPT-4o / Gemini（備用） ｜ Sentence-BERT (paraphrase-multilingual-MiniLM-L12-v2) ｜ scikit-learn (TF-IDF, K-Means, Isolation Forest) ｜ 規則式 Regex 高亮 + 信心分數 ｜ APScheduler（預測分析 24h + 資料擷取 6h） ｜ Streamlit（12 頁面） ｜ pytest + Hypothesis (Property-Based Testing) ｜ Docker + Docker Compose。

技術棧圖示列下方，以兩欄卡片展示團隊分工：Member A（後端架構、AI 模型、雲端部署）；Member B（資料處理、前端介面、版本控制、簡報）。

畫面底部以醒目徽章展示 AI 模型：Meta Llama 3（透過 Ollama 本地部署） ｜ Google Gemini。最後一行文字：「本專案未使用任何中國大陸開發之 AI 工具」。

**🎙️ 旁白文字：**

「ScamOracle — AI 詐騙進化預測系統。10 個核心模組、410 個自動化測試、四層系統架構。感謝您的觀看。」

**📝 技術標註：**

- `Stack: FastAPI + Uvicorn, LangChain + Ollama（主要）/ GPT-4o / Gemini（備用）, Sentence-BERT (paraphrase-multilingual-MiniLM-L12-v2), scikit-learn (TF-IDF, K-Means, Isolation Forest), 規則式 Regex 高亮 + 信心分數, APScheduler（預測分析 24h + 資料擷取 6h）, Streamlit（12 頁面）, pytest + Hypothesis (Property-Based Testing), Docker + Docker Compose`
- `AI: Meta Llama 3（透過 Ollama 本地部署）, Google Gemini`
- `No Chinese AI tools used`

---

## 附錄：技術參數速查

| 參數 | 數值 | 出現分鏡 |
|------|------|---------|
| 專案名稱 | ScamOracle | 全部 |
| 核心模組數 | 10 | 1, 7 |
| 功能頁面數 | 12 | 1, 2 |
| API 端點數 | 7 | 1, 2, 5 |
| 自動化測試數 | 410 | 1, 4, 7 |
| 語意向量維度 | 384 維 | 2, 3 |
| 預警提前時間 | 24 小時 | 2 |
| Docker 服務 | PostgreSQL、Redis、Qdrant | 2, 5 |
| AI 模型 | Meta Llama 3（透過 Ollama 本地部署）、Google Gemini | 1, 2, 7 |
| 嵌入模型 | paraphrase-multilingual-MiniLM-L12-v2 | 1, 3 |

---

## 附錄：影片時長檢核表

| 分鏡 | 起始 | 結束 | 秒數 | 累計 |
|------|------|------|------|------|
| 1 | 0:00 | 0:20 | 20 | 20 |
| 2 | 0:20 | 0:50 | 30 | 50 |
| 3 | 0:50 | 1:10 | 20 | 70 |
| 4 | 1:10 | 1:25 | 15 | 85 |
| 5 | 1:25 | 1:40 | 15 | 100 |
| 6 | 1:40 | 1:50 | 10 | 110 |
| 7 | 1:50 | 2:00 | 10 | 120 |
| **合計** | | | **120 秒** | **2 分鐘** ✅ |
