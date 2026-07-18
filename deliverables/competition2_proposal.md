

# ScamOracle — AI 詐騙進化預測系統

## AI 應用技術與架構設計大賽 計畫書

| 項目 | 內容 |
|------|------|
| 專案名稱 | ScamOracle — AI 詐騙進化預測系統 |
| 參賽組別 | AI 應用技術與架構設計大賽 |
| AI 模型 | Meta Llama 3（透過 Ollama 本地部署）、Google Gemini |
| 語意嵌入 | paraphrase-multilingual-MiniLM-L12-v2（384 維） |
| 自動化測試 | 410 個（單元測試 + Property-Based Testing + 整合測試） |
| 聲明 | 本專案未使用任何中國大陸開發之 AI 工具（如 DeepSeek、百度文心、通義千問等） |

---

## 一、作品及功能簡介

### 1.1 專案摘要

ScamOracle（AI 詐騙進化預測系統）是一套以「**以 AI 對抗 AI**」為核心理念的詐騙進化預測系統。系統運用 Meta Llama 3（透過 Ollama 本地部署） 與 Google Gemini 等大型語言模型，結合 NLP 語意分析、XAI 可解釋性技術與 Isolation Forest 異常偵測演算法，實現對詐騙話術演化趨勢的主動預測與提前預警。

系統採用 FastAPI + Streamlit 前後端分離架構，以 Docker Compose 管理 PostgreSQL、Redis、Qdrant 三項基礎設施服務，提供 12 個互動式功能頁面與 7 個標準化 REST API 端點，並以 410 個自動化測試確保系統品質。

### 1.2 問題背景

台灣 2023 年全台詐騙案件達 83000 件，年度損失金額高達 88.2 億元，較前一年增長 28%。投資詐騙平均每案損失 112 萬元，愛情詐騙平均每案損失 56 萬元。現有防詐機制（165 反詐騙專線、銀行交易監控、Whoscall 來電辨識）均為被動防禦模式，無法在新型詐騙大規模爆發前提前預警。

詐騙手法每 6-12 個月進化一次，從早期電話詐騙演化至 AI 深偽語音，詐騙集團已開始運用 AI 技術生成更逼真的話術。ScamOracle 的核心目標是：**在新型詐騙大規模爆發之前就預測到它**。

### 1.3 核心功能概述

ScamOracle 提供以下核心功能：

1. **LLM 話術裂變生成**：透過 Meta Llama 3（透過 Ollama 本地部署） 與 Google Gemini 逆向模擬詐騙犯思維，從單一種子情境自動裂變生成數百種話術變種
2. **NLP 語意分析**：使用 paraphrase-multilingual-MiniLM-L12-v2（384 維語意向量）進行語意嵌入，TF-IDF 提取關鍵詞，K-Means 分群辨識詐騙家族
3. **XAI 可解釋性分析**：逐句高亮標記詐騙話術中的心理操控片段，分為五種心理特徵維度
4. **Isolation Forest 異常偵測**：時間序列分析持續監控詐騙趨勢，提前 24 小時發出預警
5. **互動式防詐免疫訓練**：讓使用者在模擬情境中學習辨識詐騙手法
6. **Risk Vector API**：標準化風險向量 API，可串接金融機構即時防詐系統

### 1.4 十大核心模組功能說明

ScamOracle 由 10 個核心模組組成，各模組職責如下：

| 編號 | 模組名稱 | 功能說明 |
|------|---------|---------|
| 1 | `access_controller` | 存取控制模組，實作 RBAC 角色權限管理、SHA-256 稽核日誌、TOTP 二次驗證 |
| 2 | `api_gateway` | FastAPI 後端 API 閘道，提供 7 個 REST API 端點，含 API Key 驗證、速率限制、請求日誌中介軟體 |
| 3 | `dashboard` | Streamlit 前端儀表板，12 個互動式功能頁面，包含系統總覽、即時威脅監控、詐騙對話模擬器、話術 DNA 圖譜等 |
| 4 | `data_import` | 報案資料匯入模組，支援 CSV/JSON 格式，內建 PII 去識別化處理（正則表達式遮蔽身分證、電話、地址等敏感資訊） |
| 5 | `deliverable_generator` | deliverable_generator 模組 |
| 6 | `live_data` | 即時資料自動更新模組，每 6 小時從政府開放資料平台擷取最新統計，含三層降級機制（即時 → 快取 → 靜態） |
| 7 | `models` | 資料模型定義模組，定義 ScamScript、AccessLog、CaseReport、ModelVersion、RiskVector、AlertEvent 等核心資料結構 |
| 8 | `pattern_analyzer` | NLP 語意分析模組，整合 Sentence-BERT 384 維嵌入、TF-IDF 關鍵詞提取、K-Means 分群、心理特徵分類器、XAI 可解釋性高亮標記 |
| 9 | `prediction_layer` | 預測與預警模組，包含 Isolation Forest 異常偵測、Risk Vector 風險向量生成、AlertEvent 預警事件產生、APScheduler 排程管理 |
| 10 | `scam_engine` | LLM 話術裂變生成引擎，透過 LangChain 整合 Ollama/Gemini，從種子情境生成詐騙話術變種。包含 Prompt 模板設計、指數退避重試邏輯、結構化錯誤回應 |


---

## 二、作品特色及創意效益描述

### 2.1 核心創新：以 AI 對抗 AI

ScamOracle 的核心創新在於「**以 AI 對抗 AI**」的逆向思維。傳統防詐思維是「等詐騙出現 → 分析手法 → 建立防禦」，永遠慢詐騙犯一步。ScamOracle 徹底翻轉這個邏輯：

| 傳統防禦 | ScamOracle |
|---------|------------------------|
| 被動等待詐騙發生 | **主動預測未來詐騙手法** |
| 事後分析已知手法 | **AI 模擬詐騙犯思維，預測未知手法** |
| 更新資料庫需數週 | **24 小時內發出預警** |
| 黑盒子判斷 | **XAI 可解釋性，讓人看懂詐騙運作** |

這就像疫苗的原理：不是等人生病才治療，而是先用減毒病毒讓免疫系統認識威脅，提前建立抗體。ScamOracle 就是台灣社會的「防詐疫苗」。

### 2.2 Scam_DNA 五維心理特徵量化技術

ScamOracle 獨創 Scam_DNA 技術，將每一段詐騙話術量化為五個心理操控維度：

| 維度 | 說明 | 技術實作 |
|------|------|---------|
| **信任建立** | 詐騙犯建立虛假信任關係，讓受害者放下戒心 | 規則式 Regex 分類器 + 信心分數 |
| **緊迫感製造** | 製造時間壓力，迫使受害者在短時間內做出決定 | 規則式 Regex 分類器 + 信心分數 |
| **情緒勒索** | 利用恐懼、愧疚等情緒操控受害者行為 | 規則式 Regex 分類器 + 信心分數 |
| **權威偽裝** | 假冒政府機關、銀行等權威身份取信受害者 | 規則式 Regex 分類器 + 信心分數 |
| **利益誘導** | 以高報酬、免費贈品等利益吸引受害者上鉤 | 規則式 Regex 分類器 + 信心分數 |


每種詐騙手法都有獨特的 Scam_DNA 特徵分布，如同生物 DNA 決定生物特徵。透過 paraphrase-multilingual-MiniLM-L12-v2 產生的 384 維語意向量，系統能自動辨識詐騙話術的「家族關係」，追蹤演化軌跡。

### 2.3 自動化測試策略

ScamOracle 以 410 個自動化測試確保系統品質，採用三種測試類型：

| 測試類型 | 說明 | 工具 |
|---------|------|------|
| **單元測試** | 驗證各模組核心函數的正確性，覆蓋正常路徑與邊緣案例 | pytest |
| **Property-Based Testing** | 透過隨機生成輸入驗證系統屬性的普遍性，如「心理特徵標籤必須屬於合法集合」 | Hypothesis |
| **整合測試** | 驗證模組間的協作正確性，如 API Gateway → Scam Engine → Pattern Analyzer 的完整流程 | pytest + httpx |

```bash
# 執行全部 410 個測試
python -m pytest tests/ -v

# 各模組測試
python -m pytest tests/test_scam_engine.py -v          # 詐騙生成引擎
python -m pytest tests/test_pattern_analyzer.py -v     # 模式分析器
python -m pytest tests/test_prediction_layer.py -v     # 預測層
python -m pytest tests/test_api_gateway.py -v          # API 閘道
python -m pytest tests/test_access_control.py -v       # 存取控制
python -m pytest tests/test_data_import.py -v          # 資料匯入
python -m pytest tests/test_dashboard.py -v            # 儀表板邏輯
python -m pytest tests/test_models.py -v               # 資料模型
```

### 2.4 效能指標與程式碼品質

| 指標 | 數值 | 說明 |
|------|------|------|
| XAI 偵測準確率 | 88.9% | 基於 165 通報案例與正常對話的混合測試集 |
| 預警提前時間 | 24 小時 | Isolation Forest 異常偵測演算法 |
| 語意向量維度 | 384 維 | Sentence-BERT MiniLM 模型固定輸出 |
| 自動化測試 | 410 個 | 含單元測試、PBT、整合測試 |
| 功能頁面 | 12 個 | Streamlit 互動式 Dashboard |
| API 端點 | 7 個 | FastAPI REST API |
| 核心模組 | 10 個 | Python 套件化架構 |
| Docker 服務 | 3 個 | PostgreSQL、Redis、Qdrant |

---

## 三、作品系統架構

### 3.1 四層系統架構圖

ScamOracle 採用四層架構設計，資料從輸入層流經引擎層、分析層到輸出層：

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Input Layer（輸入層）                          │
│                                                                     │
│   使用者輸入詐騙情境種子 → API Gateway 接收請求 → 參數驗證與路由     │
│   FastAPI + Uvicorn ｜ API Key 驗證 ｜ 速率限制 ｜ 請求日誌          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Engine Layer（引擎層）                          │
│                                                                     │
│   ┌─────────────────────┐    ┌──────────────────────────────────┐  │
│   │   Scam Engine        │    │   Pattern Analyzer                │  │
│   │   ─────────────────  │    │   ────────────────────────────── │  │
│   │   LangChain Prompt   │    │   S-BERT 384維語意嵌入          │  │
│   │   Meta Llama 3（透過 Ollama 本地部署）  │    │   Google GeminiTF-IDF 關鍵詞提取             │  │
│   │   指數退避重試       │    │   心理特徵分類器（5 維）         │  │
│   │   結構化錯誤回應     │    │   XAI 可解釋性高亮              │  │
│   └─────────────────────┘    └──────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Analysis Layer（分析層）                        │
│                                                                     │
│   ┌─────────────────────┐    ┌──────────────────────────────────┐  │
│   │   Isolation Forest   │    │   K-Means Clustering              │  │
│   │   ─────────────────  │    │   ────────────────────────────── │  │
│   │   時間序列異常偵測   │    │   話術語意分群                   │  │
│   │   24h 預警窗口       │    │   詐騙家族辨識                   │  │
│   │   趨勢變化監控       │    │   演化軌跡追蹤                   │  │
│   └─────────────────────┘    └──────────────────────────────────┘  │
│                                                                     │
│   Risk Vector 風險向量生成 ｜ AlertEvent 預警事件 ｜ APScheduler    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Output Layer（輸出層）                         │
│                                                                     │
│   ┌─────────────────────┐    ┌──────────────────────────────────┐  │
│   │   Streamlit Dashboard│    │   REST API                        │  │
│   │   ─────────────────  │    │   ────────────────────────────── │  │
│   │   12 個功能頁面       │    │   7 個標準化端點                │  │
│   │   XAI 高亮渲染       │    │   Risk Vector JSON 輸出          │  │
│   │   互動式圖表         │    │   Swagger UI 文件                │  │
│   └─────────────────────┘    └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 資料處理流程

```
情境種子輸入
    │
    ▼
LLM 話術裂變生成（LangChain + Meta Llama 3（透過 Ollama 本地部署） / Google Gemini）
    │
    ▼
NLP 語意特徵萃取（paraphrase-multilingual-MiniLM-L12-v2 → 384 維向量）
    │
    ├──→ TF-IDF 關鍵詞提取
    ├──→ K-Means 語意分群
    └──→ 心理特徵分類（信任建立、緊迫感製造、情緒勒索、權威偽裝、利益誘導）
          │
          ▼
    XAI 可解釋性高亮標記
          │
          ▼
    Scam_DNA 五維心理特徵量化
          │
          ▼
    Isolation Forest 異常偵測 → AlertEvent 預警
          │
          ▼
    Risk Vector 風險向量輸出 → API 串接金融機構
```

### 3.3 Docker Compose 基礎設施架構

ScamOracle 使用 Docker Compose 管理 3 項基礎設施服務：

| 服務 | 映像檔 | 用途 | 連接埠 |
|------|--------|------|--------|
| **PostgreSQL** | postgres:16-alpine | 關聯式資料庫，儲存 ScamScript、AccessLog、CaseReport、ModelVersion、RiskVector、AlertEvent | 5432 |
| **Redis** | redis:7-alpine | 快取層，用於 API 速率限制計數、Dashboard 快取、Risk Vector 快取 | 6379 |
| **Qdrant** | qdrant/qdrant:v1.9.0 | 向量資料庫，儲存 384 維語意向量，支援相似度搜尋 | 6333/6334 |


```yaml
# docker-compose.yml 服務定義
services:
  postgresql:
    image: postgres:16-alpine

  redis:
    image: redis:7-alpine

  qdrant:
    image: qdrant/qdrant:v1.9.0

volumes:
  postgresql_data:
  redis_data:
  qdrant_data:

networks:
  scam_network:
    driver: bridge
```

### 3.4 技術棧說明

| 類別 | 技術 |
|------|------|
| 後端框架 | FastAPI + Uvicorn |
| LLM 整合 | LangChain + Ollama（主要）/ GPT-4o / Gemini（備用） |
| NLP | Sentence-BERT (paraphrase-multilingual-MiniLM-L12-v2) |
| 機器學習 | scikit-learn (TF-IDF, K-Means, Isolation Forest) |
| XAI | 規則式 Regex 高亮 + 信心分數 |
| 排程 | APScheduler（預測分析 24h + 資料擷取 6h） |
| 前端 | Streamlit（12 頁面） |
| 測試 | pytest + Hypothesis (Property-Based Testing) |
| 容器化 | Docker + Docker Compose |


### 3.5 專案結構

```
ScamOracle/
├── app/
│   ├── access_controller/
│   ├── api_gateway/
│   ├── dashboard/
│   ├── data_import/
│   ├── deliverable_generator/
│   ├── live_data/
│   ├── models/
│   ├── pattern_analyzer/
│   ├── prediction_layer/
│   ├── scam_engine/
├── data/
│   └── taiwan_scam_data.py
├── tests/                        # 410 個自動化測試
├── docker-compose.yml            # Docker 服務定義
├── requirements.txt              # Python 依賴
└── README.md
```

---

## 四、人工智慧工具輔助開發使用情形

### 4.1 GitHub Copilot 程式碼輔助

ScamOracle 開發過程中使用 GitHub Copilot 作為 AI 程式碼輔助工具，主要應用於以下場景：

| 應用場景 | 說明 | 效益 |
|---------|------|------|
| **程式碼自動補全** | Copilot 根據上下文自動建議程式碼片段，加速日常編碼 | 減少重複性編碼時間約 30% |
| **測試程式碼生成** | 根據函數簽名自動建議測試案例，輔助撰寫 410 個測試 | 提升測試覆蓋率 |
| **文件字串生成** | 自動生成 Python docstring，確保程式碼文件完整 | 統一文件格式 |
| **正則表達式輔助** | 心理特徵分類器的 Regex 模式設計，Copilot 建議多語言匹配模式 | 提升分類器覆蓋率 |
| **API 路由設計** | FastAPI 路由定義與 Pydantic 模型設計的自動補全 | 加速 API 開發 |

#### 使用範例：心理特徵分類器 Regex 模式

```python
# GitHub Copilot 輔助設計的心理特徵分類器關鍵詞模式
_URGENCY_PATTERNS: list[str] = [
    r"立即", r"馬上", r"緊急", r"限時", r"今天",
    r"現在", r"快速", r"盡快", r"不要錯過", r"最後機會",
    r"即將截止", r"倒數", r"24小時", r"48小時",
    # Copilot 建議的英文關鍵詞
    r"urgent", r"immediately", r"right now",
    r"limited time", r"act now", r"expires",
]
```

### 4.2 Prompt Engineering（Ollama 本地 LLM）

ScamOracle 的核心功能依賴精心設計的 Prompt Engineering，透過 Ollama 本地部署的 Meta Llama 3 模型執行：

#### LangChain Prompt 模板設計

```python
# scam_engine/generator.py — LangChain Prompt 模板
_SYSTEM_PROMPT = """你是一個專業的詐騙話術分析研究員，
協助防詐機構研究詐騙手法。
你的任務是根據給定的詐騙情境，
生成多種不同語氣與手法的詐騙對話樣本，
供防詐系統訓練與研究使用。

請嚴格按照以下 JSON 格式輸出：
{
  "samples": [
    {
      "content": "詐騙話術文本（至少 50 字）",
      "psychological_tags": ["心理操控類別標籤"],
      "target_audience": "目標受眾描述"
    }
  ]
}

心理操控類別標籤必須從以下五類中選擇：
- 信任建立
- 緊迫感製造
- 情緒勒索
- 權威偽裝
- 利益誘導
"""
```

#### Prompt Engineering 設計原則

| 原則 | 說明 | 實作方式 |
|------|------|---------|
| **角色設定** | 將 LLM 定位為「詐騙話術分析研究員」，確保輸出符合研究用途 | System Prompt 角色定義 |
| **結構化輸出** | 要求 LLM 以 JSON 格式輸出，便於程式解析 | JSON Schema 約束 |
| **標籤約束** | 限定心理操控標籤為五類合法值，避免 LLM 自行發明標籤 | 列舉式約束 |
| **品質要求** | 要求每個樣本至少 50 字、不同樣本間語氣差異明顯 | 明確品質指標 |
| **安全護欄** | 明確標示生成目的為「防詐系統訓練與研究」 | 用途聲明 |

#### Ollama 本地部署優勢

| 優勢 | 說明 |
|------|------|
| **資料不外洩** | 所有 LLM 推論在本地執行，詐騙話術資料不會傳送至雲端 |
| **零 API 費用** | 使用開源 Meta Llama 3 模型，無需支付 API 呼叫費用 |
| **低延遲** | 本地推論延遲遠低於雲端 API，提升使用者體驗 |
| **離線可用** | 不依賴網路連線，適合安全敏感的執法機關環境 |

---

## 附錄：AI 模型使用聲明

| AI 模型 | 用途 | 部署方式 |
|---------|------|---------|
| Meta Llama 3（透過 Ollama 本地部署） | 話術裂變生成、對話模擬、時間軸生成 | 本地部署 |
| Google Gemini | 備用 LLM 引擎、多模型對比驗證 | 雲端 API |
| paraphrase-multilingual-MiniLM-L12-v2 | 384 維語意向量嵌入 | 本地模型 |
| GitHub Copilot | 程式碼輔助開發 | IDE 外掛 |

**本專案未使用任何中國大陸開發之 AI 工具**，包括但不限於：DeepSeek、百度文心一言（ERNIE Bot）、通義千問（Qwen）、ChatGLM、MiniMax、百川（Baichuan）等。

## 附錄：團隊分工


| 成員 | 負責範疇 |
|------|---------|
| Member A | 後端架構、AI 模型、雲端部署 |
| Member B | 資料處理、前端介面、版本控制、簡報 |


