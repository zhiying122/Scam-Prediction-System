

# ScamOracle — AI 詐騙進化預測系統

## AI 應用技術與架構設計大賽 海報內容

> **海報尺寸：A1（594mm × 841mm）**
>
> **主視覺：四層系統架構流程圖（佔海報面積 45%）**
>
> **AI 模型：** Meta Llama 3（透過 Ollama 本地部署）、Google Gemini
>
> **聲明：** 本專案未使用任何中國大陸開發之 AI 工具

---

## 版面配置總覽（A1: 594mm × 841mm）

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   🛡️ ScamOracle — AI 詐騙進化預測系統                       │  標題區（8%）
│   AI 應用技術與架構設計大賽                                   │
│   10 模組 ｜ 410 測試 ｜ 12 頁面 ｜ 7 API    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │                                                     │  │
│   │          四 層 系 統 架 構 流 程 圖                   │  │
│   │                                                     │  │
│   │  ┌──────────┐                                       │  │
│   │  │  Input   │  FastAPI + API Key + Rate Limit       │  │
│   │  └────┬─────┘                                       │  │  主視覺：架構圖（45%）
│   │       │                                             │  │
│   │  ┌────▼─────┐  ┌──────────────────────┐            │  │
│   │  │  Engine  │  │ S-BERT 384維 ｜ TF-IDF │  │
│   │  │  LLM     │  │ K-Means ｜ Regex 5維  │            │  │
│   │  └────┬─────┘  └──────────────────────┘            │  │
│   │       │                                             │  │
│   │  ┌────▼─────┐                                       │  │
│   │  │ Analysis │  Isolation Forest ｜ Risk Vector      │  │
│   │  └────┬─────┘                                       │  │
│   │       │                                             │  │
│   │  ┌────▼─────┐                                       │  │
│   │  │  Output  │  Streamlit 12p ｜ API 7ep     │  │
│   │  └──────────┘                                       │  │
│   │                                                     │  │
│   │  ┌──────┐  ┌──────┐  ┌──────┐                     │  │
│   │  │ PgSQL│  │Redis │  │Qdrant│  Docker Compose      │  │
│   │  └──────┘  └──────┘  └──────┘                     │  │
│   │                                                     │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
├──────────────────────┬──────────────────────────────────────┤
│                      │                                      │
│  程式碼片段 1         │  程式碼片段 2                         │  程式碼區（20%）
│  generator.py        │  embedder.py                         │
│  LangChain Prompt    │  S-BERT 384維嵌入              │
│                      │                                      │
├──────────────────────┴──────────────────────────────────────┤
│                                                             │
│  🧪 410 測試 ｜ PBT ｜ 三類測試                          │  品質指標（12%）
│                                                             │
│  技術棧：FastAPI ｜ Streamlit ｜ Docker ｜ PostgreSQL        │
│         Redis ｜ Qdrant ｜ Ollama ｜ scikit-learn            │
│                                                             │
│  🏷️ Meta Llama 3 & Google Gemini ｜ ❌ 未使用 DeepSeek      │  徽章與團隊（15%）
│  🤖 AI 輔助：GitHub Copilot ｜ Prompt Engineering           │
│  👥 Member A（後端、AI）｜ Member B（前端、資料）            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 一、標題區（佔海報面積 8%）

### 版面位置
海報最上方，全寬橫幅，高度約 67mm

### 視覺設計
- **背景色**：深藍漸層（#0A1628 → #1A2744）
- **主標題**：「ScamOracle — AI 詐騙進化預測系統」，白色粗體，字級 96pt
- **副標題**：「AI 應用技術與架構設計大賽」，淺灰色，字級 48pt
- **系統規模指標列**：水平排列四個指標徽章

### 系統規模指標

| 指標 | 數值 | 徽章配色 |
|------|------|---------|
| 核心模組 | 10 個 | 藍色 #1565C0 |
| 自動化測試 | 410 個 | 綠色 #2E7D32 |
| 功能頁面 | 12 個 | 紫色 #6A1B9A |
| API 端點 | 7 個 | 橙色 #E65100 |

---

## 二、主視覺：四層系統架構流程圖（佔海報面積 45%）

### 版面位置
標題區下方，全寬，高度約 378mm

### 視覺設計
- **背景色**：深色（#0D1B2A），讓架構圖元素突出
- **架構層方塊**：圓角矩形，每層使用不同主題色
- **資料流箭頭**：發光粒子效果，從上到下流動
- **技術參數標註**：每層方塊旁以小字標註關鍵技術參數

### 架構圖詳細設計

#### Input Layer（輸入層）— 綠色 #4CAF50

```
┌─────────────────────────────────────────────────────────────────┐
│  Input Layer                                                        │
│                                                                 │
│  FastAPI + Uvicorn                                              │
│  ├── API Key 驗證中介軟體                                        │
│  ├── 速率限制（滑動視窗 60s / 100 req）                          │
│  ├── 請求日誌中介軟體                                            │
│  └── 7 個 REST API 端點路由                                    │
│                                                                 │
│  技術標註：Pydantic 參數驗證 ｜ CORS ｜ Lifespan 管理            │
└─────────────────────────────────────────────────────────────────┘
```

#### Engine Layer（引擎層）— 藍色 #2196F3

```
┌─────────────────────────────────────────────────────────────────┐
│  Engine Layer                                                       │
│                                                                 │
│  ┌─── Scam Engine ───────────┐  ┌─── Pattern Analyzer ────────┐│
│  │                           │  │                              ││
│  │  LangChain Prompt 模板    │  │  S-BERT 384 維語意嵌入     ││
│  │  Meta Llama 3（透過 Ollama 本地部署）│  │  Google GeminiTF-IDF 關鍵詞提取          ││
│  │  指數退避重試（3 次）     │  │  K-Means 語意分群            ││
│  │  JSON 結構化輸出          │  │  心理特徵分類器（5 維）      ││
│  │                           │  │  XAI 可解釋性高亮            ││
│  └───────────────────────────┘  └──────────────────────────────┘│
│                                                                 │
│  技術標註：paraphrase-multilingual-MiniLM-L12-v2                            │
│           384d vectors ｜ langdetect 雙語偵測                    │
└─────────────────────────────────────────────────────────────────┘
```

#### Analysis Layer（分析層）— 橙色 #FF9800

```
┌─────────────────────────────────────────────────────────────────┐
│  Analysis Layer                                                     │
│                                                                 │
│  Isolation Forest 異常偵測                                       │
│  ├── 時間序列趨勢監控                                            │
│  ├── 24h 預警窗口                                              │
│  └── AlertEvent 預警事件生成                                     │
│                                                                 │
│  Risk Vector 風險向量                                            │
│  ├── 多維風險量化                                                │
│  └── JSON 標準化輸出（串接金融機構）                              │
│                                                                 │
│  APScheduler 排程管理（預測 24h + 資料擷取 6h）                 │
│                                                                 │
│  技術標註：scikit-learn ｜ numpy ｜ 滑動視窗分析                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Output Layer（輸出層）— 紫色 #9C27B0

```
┌─────────────────────────────────────────────────────────────────┐
│  Output Layer                                                       │
│                                                                 │
│  ┌─── Streamlit Dashboard ───┐  ┌─── REST API ────────────────┐│
│  │                           │  │                              ││
│  │  12 個互動式功能頁面   │  │  7 個標準化端點            ││
│  │  XAI 高亮渲染             │  │  Swagger UI 文件             ││
│  │  互動式圖表（Plotly）     │  │  Risk Vector JSON 輸出       ││
│  │  即時威脅監控             │  │  健康檢查端點                ││
│  │                           │  │                              ││
│  └───────────────────────────┘  └──────────────────────────────┘│
│                                                                 │
│  技術標註：Streamlit ｜ Plotly ｜ httpx ｜ Pydantic              │
└─────────────────────────────────────────────────────────────────┘
```

#### 基礎設施層 — Docker Compose

```
┌─────────────────────────────────────────────────────────────────┐
│  Infrastructure（Docker Compose）                                │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  PostgreSQL  │  │  │  Redis       │  │  │  Qdrant      │  │
│  │  :5432        │  │  │  :6379        │  │  │  :6333/6334   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 架構圖關鍵技術參數標註

| 位置 | 標註內容 | 字級 |
|------|---------|------|
| Engine Layer 左側 | S-BERT 384 維向量 | 18pt |
| Engine Layer 右側 | LangChain Prompt 模板 | 18pt |
| Analysis Layer 左側 | Isolation Forest 異常偵測 | 18pt |
| Analysis Layer 右側 | K-Means 分群 | 18pt |
| 基礎設施層 | Docker Compose 3 服務 | 18pt |

---

## 三、程式碼片段區（佔海報面積 20%）

### 版面位置
架構圖下方，左右分割，高度約 168mm

### 視覺設計
- **背景色**：深色程式碼編輯器風格（#1E1E1E）
- **字體**：等寬字體（JetBrains Mono / Fira Code），字級 14pt
- **語法高亮**：模擬 VS Code Dark+ 主題配色

### 程式碼片段 1（左側）— `scam_engine/generator.py`

**標題**：LangChain Prompt 模板設計

```python
# scam_engine/generator.py
_SYSTEM_PROMPT = """你是一個專業的詐騙話術
分析研究員，協助防詐機構研究詐騙手法。
請嚴格按照 JSON 格式輸出：
{
  "samples": [{
    "content": "詐騙話術文本",
    "psychological_tags": ["標籤"],
    "target_audience": "目標受眾"
  }]
}"""

SCAM_GENERATION_PROMPT = (
    ChatPromptTemplate.from_messages([
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=_HUMAN_PROMPT),
    ])
)

# 指數退避重試（最多 3 次）
async def _call_llm_with_retry(
    llm, messages, request_id,
    max_attempts=3,
    backoff_multiplier=2.0):
    ...
```

**語法高亮配色**：
- 關鍵字（`async`, `def`, `class`）：藍色 #569CD6
- 字串：橙色 #CE9178
- 函數名稱：黃色 #DCDCAA
- 註解：綠色 #6A9955

### 程式碼片段 2（右側）— `pattern_analyzer/embedder.py`

**標題**：S-BERT 384 維語意嵌入

```python
# pattern_analyzer/embedder.py
EMBEDDING_DIM: int = 384

class LanguageEmbedder:
    def __init__(self, model_name: str =
        "paraphrase-multilingual-MiniLM-L12-v2"):
        self._model_name = model_name
        self._model = None

    def embed(self, text: str)
            -> EmbeddingResult:
        lang = detect_language(text)
        if not is_supported_language(lang):
            return EmbeddingResult(
                language="unsupported",
                embedding=None,
                is_supported=False)

        model = self._load_model()
        raw = model.encode(
            text, convert_to_numpy=True)
        embedding = raw.tolist()
        _validate_embedding(embedding)
        return EmbeddingResult(
            language=lang,
            embedding=embedding,
            is_supported=True)
```

---

## 四、測試覆蓋率與品質指標區（佔海報面積 12%）

### 版面位置
程式碼區下方，全寬，高度約 101mm

### 視覺設計
- **背景色**：深綠漸層（#0D2818 → #1B3A2A），象徵測試通過
- **指標卡片**：水平排列，白色圓角矩形

### 測試品質指標

| 指標 | 數值 | 視覺效果 |
|------|------|---------|
| 🧪 自動化測試總數 | **410** 個 | 大字數據 + 綠色勾勾 |
| 📊 測試類型 | **3 種** | 單元測試 + PBT + 整合測試 |
| 🎯 XAI 偵測準確率 | **84.7%** | 圓形進度環 |
| ⏱ 預警提前時間 | **24 小時** | 時鐘圖示 |

### 測試類型分布

| 測試類型 | 說明 | 框架 |
|---------|------|------|
| **單元測試** | 各模組核心函數正確性驗證 | pytest |
| **Property-Based Testing** | 隨機輸入驗證系統屬性普遍性 | Hypothesis |
| **整合測試** | 模組間協作正確性驗證 | pytest + httpx |

### 技術棧圖示列

以水平圖示列展示完整技術棧，每個技術以 Logo 圖示 + 名稱呈現：

| 技術 | 圖示 | 用途 |
|------|------|------|
| **FastAPI** | ⚡ | 後端 API 框架 |
| **Streamlit** | 📊 | 前端 Dashboard |
| **Docker** | 🐳 | 容器化部署 |
| **PostgreSQL** | 🐘 | 關聯式資料庫 |
| **Redis** | 🔴 | 快取層 |
| **Qdrant** | 🔷 | 向量資料庫 |
| **Ollama** | 🦙 | 本地 LLM 服務 |
| **scikit-learn** | 🔬 | 機器學習（TF-IDF、K-Means、Isolation Forest） |

---

## 五、AI 模型徽章、輔助開發與團隊資訊（佔海報面積 15%）

### 版面位置
海報最底部，全寬，高度約 126mm

### AI 模型徽章設計

| 徽章 | 內容 | 配色 |
|------|------|------|
| 徽章 1 | 🦙 **Meta Llama 3**（透過 Ollama 本地部署） | 藍色底 #1565C0 |
| 徽章 2 | ✨ **Google Gemini** | 綠色底 #2E7D32 |
| 徽章 3 | ❌ **未使用 DeepSeek 等中國大陸 AI 工具** | 紅色底 #C62828 |

### AI 輔助開發工具使用說明

| 工具 | 用途 | 說明 |
|------|------|------|
| **GitHub Copilot** | 程式碼輔助 | 自動補全、測試生成、文件字串、Regex 模式設計 |
| **Prompt Engineering** | LLM 話術生成 | 精心設計 System Prompt + Human Prompt，透過 Ollama 本地執行 |

### 團隊分工


| 成員 | 負責範疇 |
|------|---------|
| Member A | 後端架構、AI 模型、雲端部署 |
| Member B | 資料處理、前端介面、版本控制、簡報 |


---

## 附錄：版面區域面積分配

| 區域 | 佔海報面積 | 高度（mm） | 內容重點 |
|------|-----------|-----------|---------|
| 標題區 | 8% | ~67 | 品牌識別、系統規模指標 |
| **架構流程圖** | **45%** | **~378** | **四層系統架構（主視覺）** |
| 程式碼片段區 | 20% | ~168 | 2 個核心模組程式碼展示 |
| 品質指標區 | 12% | ~101 | 測試覆蓋率、技術棧圖示列 |
| 徽章與團隊 | 15% | ~126 | AI 模型徽章、輔助開發、團隊 |
| **合計** | **100%** | **841** | |

> ✅ 架構流程圖佔海報面積 **45%**，超過 40% 下限要求

## 附錄：需求檢核表

| 需求 | 內容 | 狀態 |
|------|------|------|
| 6.1 | A1 尺寸（594mm × 841mm） | ✅ 已標註 |
| 6.2 | 架構圖佔海報面積至少 40% | ✅ 45%（超過下限） |
| 6.3 | 架構圖標註關鍵技術參數 | ✅ S-BERT 384維、Isolation Forest、K-Means、LangChain |
| 6.4 | 至少 2 個程式碼片段 | ✅ generator.py + embedder.py |
| 6.5 | 測試覆蓋率與品質指標 | ✅ 410 測試、PBT、三種測試類型 |
| 6.6 | 技術棧圖示列 | ✅ FastAPI、Streamlit、Docker、PostgreSQL、Redis、Qdrant、Ollama、scikit-learn |
| 6.7 | Meta Llama 3 & Google Gemini 徽章 | ✅ 三個醒目徽章 |
| 6.8 | AI 輔助開發工具說明 | ✅ GitHub Copilot + Prompt Engineering |
