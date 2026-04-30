# 需求文件：比賽交付物產出系統

## 簡介

本功能為 ScamOracle（AI 詐騙進化預測系統）產出兩場 AI 競賽所需的完整交付物。兩場比賽的評審標準截然不同：

- **比賽一（AI 應用創意獎 — 問題解決組）**：屬於「問題解決組」，針對專業領域、學生學習、實踐個案等問題解決方式與成效。強調產品創新性、使用者價值、AI 創意應用，並以問題解決為核心敘事（問題定義 → 解決方案 → 成效展示）
- **比賽二（AI 應用技術與架構設計大賽）**：強調系統架構設計、技術深度、AI 輔助開發流程、自動化測試

每場比賽各需產出三份交付物：計畫書（Proposal）、影片腳本（Video Script）、海報內容（Poster Content），共計六份文件。所有文件以繁體中文撰寫。

## 詞彙表

- **Deliverable_Generator**：交付物產出系統，負責根據比賽需求生成對應文件
- **Proposal**：計畫書文件，包含專案概述、技術說明、團隊分工等
- **Video_Script**：影片腳本文件，包含分鏡、旁白、畫面描述
- **Poster_Content**：海報內容文件，包含版面配置、文案、視覺元素描述
- **Competition_1**：AI 應用創意獎 — 問題解決組（創意導向），針對專業領域、學生學習、實踐個案等問題解決方式與成效
- **Competition_2**：AI 應用技術與架構設計大賽（技術導向）
- **ScamOracle**：本專案名稱，AI 詐騙進化預測系統
- **Scam_DNA**：詐騙 DNA，5 維心理特徵量化技術（信任建立、緊迫感製造、情緒勒索、權威偽裝、利益誘導）
- **XAI_Highlighter**：可解釋性 AI 高亮標記模組，標記話術中的心理操控片段
- **MaiAgent**：比賽一贊助商工具，用於描述話術生成引擎的協調邏輯
- **LLM_Engine**：大型語言模型引擎，使用 Meta Llama 3（透過 Ollama 本地部署）
- **S_BERT**：Sentence-BERT 語意嵌入模型，產出 384 維語意向量

---

## 需求

### 需求 1：比賽一計畫書產出

**使用者故事：** 身為參賽團隊成員，我希望產出一份強調創新性與使用者價值的計畫書，以符合 AI 應用創意獎的評審標準。

#### 驗收條件

1. THE Deliverable_Generator SHALL 產出一份包含以下章節的 Competition_1 計畫書：專案摘要、問題背景、解決方案、產品功能展示、創新亮點、使用者價值、AI 技術應用說明、團隊分工、未來展望
2. WHEN 描述話術生成引擎邏輯時，THE Proposal SHALL 將該功能描述為由 MaiAgent 協調運作，以爭取企業創意獎
3. THE Proposal SHALL 以使用者情境故事（User Scenario）方式呈現 ScamOracle 的核心功能，包含：詐騙對話模擬器、XAI 話術分析、詐騙免疫訓練、即時威脅監控
4. THE Proposal SHALL 包含 Scam_DNA 五維心理特徵量化技術的圖文說明，以非技術人員可理解的方式呈現
5. THE Proposal SHALL 明確標示使用 Meta Llama 3 與 Google Gemini 作為 AI 模型，未使用任何中國大陸開發的 AI 工具
6. THE Proposal SHALL 強調「以 AI 對抗 AI」的逆向思維創新點：在詐騙發生前主動預測，而非被動防禦
7. THE Proposal SHALL 將 ScamOracle 定位為問題解決型應用，清楚呈現以下三大面向：問題定義（台灣詐騙現況與話術演化趨勢）、解決方法論（NLP 語意分析、異常偵測、LLM 預測之整合方案）、以及可量化的成效指標（預警時間、偵測準確率、使用者防詐意識提升率）

### 需求 2：比賽二計畫書產出

**使用者故事：** 身為參賽團隊成員，我希望產出一份強調系統架構與技術深度的計畫書，以符合 AI 應用技術與架構設計大賽的評審標準。

#### 驗收條件

1. THE Deliverable_Generator SHALL 產出一份遵循比賽指定章節結構的 Competition_2 計畫書，包含以下四大章節：一、作品及功能簡介；二、作品特色及創意效益描述；三、作品系統架構（使用平臺、技術與系統架構設計圖示）；四、人工智慧工具輔助開發使用情形（無則免列）
2. WHEN 撰寫「一、作品及功能簡介」章節時，THE Proposal SHALL 包含 ScamOracle 專案摘要、問題背景、核心功能概述，以及 10 個核心模組的功能說明：scam_engine、pattern_analyzer、prediction_layer、api_gateway、dashboard、data_import、access_controller、live_data、models、config
3. WHEN 撰寫「二、作品特色及創意效益描述」章節時，THE Proposal SHALL 包含「以 AI 對抗 AI」的逆向思維創新點、Scam_DNA 五維心理特徵量化技術的特色說明、409 個自動化測試的測試策略（含單元測試、Property-Based Testing（Hypothesis）與整合測試的分布）、以及效能指標與程式碼品質指標
4. WHEN 撰寫「三、作品系統架構」章節時，THE Proposal SHALL 包含完整的四層系統架構圖說明：Input Layer → Engine Layer（Llama 3、S_BERT 384 維向量）→ Analysis Layer（Isolation Forest、K-Means）→ Output Layer（WebSocket、XAI_Highlighter），以及 Docker Compose 三服務架構（PostgreSQL、Redis、Qdrant）的基礎設施說明與技術棧說明
5. WHEN 撰寫「四、人工智慧工具輔助開發使用情形」章節時，THE Proposal SHALL 包含 AI 輔助開發工具的使用說明，涵蓋 GitHub Copilot 的程式碼輔助與 Prompt Engineering 在 Ollama 上的應用
6. THE Proposal SHALL 明確標示使用 Meta Llama 3 與 Google Gemini，未使用任何中國大陸開發的 AI 工具

### 需求 3：比賽一影片腳本產出

**使用者故事：** 身為參賽團隊成員，我希望產出一份 5 分鐘產品展示導向的影片腳本，以生動呈現 ScamOracle 的使用者體驗與創新價值。

> **⚠️ 必要內容規定：** 比賽一影片創作內容應包含以下三個項目：**應用介紹、操作方式、預期效果**。未包含以上項目將予以減分。

#### 驗收條件

1. THE Video_Script SHALL 產出總長度為 5 分鐘的 Competition_1 影片腳本，包含分鏡編號、時間碼、畫面描述、旁白文字、字幕提示
2. THE Video_Script SHALL 包含一段可清楚辨識的「應用介紹」段落，說明 ScamOracle 的產品定位、核心功能與解決的問題，使評審明確理解本應用的用途與價值
3. THE Video_Script SHALL 包含一段可清楚辨識的「操作方式」段落，以實際操作畫面展示使用者如何操作 ScamOracle 系統，包含詐騙對話模擬器、XAI 話術分析高亮效果、話術 DNA 圖譜、詐騙免疫訓練等功能的操作流程
4. THE Video_Script SHALL 包含一段可清楚辨識的「預期效果」段落，展示 ScamOracle 的預期成效與影響，包含台灣詐騙現況數據（2023 年 83,000 件、損失 88.2 億元）、ScamOracle 的預警能力（提前 24 小時）、以及對使用者防詐意識提升的預期效益
5. THE Video_Script SHALL 以使用者故事開場：呈現一位民眾接到詐騙電話的情境，帶出 ScamOracle 的防詐價值
6. THE Video_Script SHALL 包含至少 4 個產品功能的實際操作畫面展示：詐騙對話模擬器、XAI 話術分析高亮效果、話術 DNA 圖譜、詐騙免疫訓練
7. THE Video_Script SHALL 包含「以 AI 對抗 AI」核心理念的視覺化呈現段落
8. THE Video_Script SHALL 以問題解決敘事弧線組織影片結構：先呈現問題現況（台灣詐騙數據與話術演化）、再展示解決方案（ScamOracle 的技術與功能）、最後展示成效（預警能力與防詐效益），此敘事弧線與必要內容項目（應用介紹、操作方式、預期效果）自然對應

### 需求 4：比賽二影片腳本產出

**使用者故事：** 身為參賽團隊成員，我希望產出一份 2 分鐘技術架構導向的影片腳本，以清晰展示 ScamOracle 的系統設計與工程品質。

#### 驗收條件

1. THE Video_Script SHALL 產出總長度為 2 分鐘的 Competition_2 影片腳本，包含分鏡編號、時間碼、畫面描述、旁白文字、技術標註
2. THE Video_Script SHALL 包含系統四層架構的動畫流程展示：資料從 Input Layer 流經 Engine Layer、Analysis Layer 到 Output Layer 的完整路徑
3. THE Video_Script SHALL 包含至少 2 段程式碼片段的畫面展示，展示核心模組的實作品質（如 scam_engine/generator.py 的 LangChain Prompt 設計、pattern_analyzer 的 S-BERT 嵌入流程）
4. THE Video_Script SHALL 包含自動化測試執行畫面，展示 409 個測試全數通過的終端機輸出
5. THE Video_Script SHALL 包含 AI 輔助開發工具（GitHub Copilot）的使用畫面展示段落
6. THE Video_Script SHALL 包含 Docker Compose 服務啟動與 API Swagger UI 的操作展示

### 需求 5：比賽一海報內容產出

**使用者故事：** 身為參賽團隊成員，我希望產出一份產品展示導向的海報內容，以視覺化方式呈現 ScamOracle 的創新價值與使用者情境。

#### 驗收條件

1. THE Poster_Content SHALL 產出 Competition_1 海報版面配置與文案內容
2. THE Poster_Content SHALL 以產品使用情境為主視覺，包含：系統介面截圖區域、使用者操作流程圖、功能亮點卡片
3. THE Poster_Content SHALL 包含 Scam_DNA 五維雷達圖的視覺化設計說明
4. THE Poster_Content SHALL 包含「使用 Meta Llama 3 & Google Gemini」的醒目徽章設計，明確標示未使用 DeepSeek
5. THE Poster_Content SHALL 包含台灣詐騙現況的關鍵數據視覺化區塊（案件數、損失金額、年增率）
6. THE Poster_Content SHALL 包含「以 AI 對抗 AI」的核心標語與 ScamOracle 品牌識別
7. THE Poster_Content SHALL 以問題解決敘事結構編排版面：上方區域呈現問題視覺化（台灣詐騙現況數據與話術演化圖示）、中間區域呈現解決方案概覽（ScamOracle 核心功能與技術亮點）、下方區域呈現成效數據（預警能力指標與使用者效益）

### 需求 6：比賽二海報內容產出

**使用者故事：** 身為參賽團隊成員，我希望產出一份 A1 尺寸的技術架構導向海報內容，以大型系統架構流程圖為核心展示 ScamOracle 的技術設計。

#### 驗收條件

1. THE Poster_Content SHALL 產出 A1 尺寸（594mm × 841mm）的 Competition_2 海報版面配置與文案內容
2. THE Poster_Content SHALL 以大型系統架構流程圖為主視覺，佔據海報面積至少 40%，包含四層架構（Input → Engine → Analysis → Output）的完整資料流
3. THE Poster_Content SHALL 在架構圖中標註關鍵技術參數：S_BERT 384 維向量、Isolation Forest 異常偵測、K-Means 分群、LangChain Prompt 模板
4. THE Poster_Content SHALL 包含至少 2 個程式碼片段區塊，展示核心模組的實作（使用等寬字體、語法高亮配色）
5. THE Poster_Content SHALL 包含測試覆蓋率與品質指標區塊：409 個測試、Property-Based Testing、三種測試類型分布
6. THE Poster_Content SHALL 包含技術棧圖示列：FastAPI、Streamlit、Docker、PostgreSQL、Redis、Qdrant、Ollama、scikit-learn
7. THE Poster_Content SHALL 包含「使用 Meta Llama 3 & Google Gemini」的醒目徽章設計，明確標示未使用 DeepSeek
8. THE Poster_Content SHALL 包含 AI 輔助開發工具使用說明區塊（GitHub Copilot、Prompt Engineering）

### 需求 7：交付物一致性與品牌規範

**使用者故事：** 身為參賽團隊成員，我希望所有交付物維持一致的品牌識別與資訊正確性，以展現專業度。

#### 驗收條件

1. THE Deliverable_Generator SHALL 確保所有六份交付物中的技術數據一致：409 個測試、384 維向量、12 個功能頁面、7 個 API 端點
2. THE Deliverable_Generator SHALL 確保所有交付物使用一致的專案名稱「ScamOracle」與副標題「AI 詐騙進化預測系統」
3. THE Deliverable_Generator SHALL 確保 Competition_1 的所有交付物聚焦於創新性、使用者價值、產品體驗，避免過度技術細節
4. THE Deliverable_Generator SHALL 確保 Competition_2 的所有交付物聚焦於架構設計、程式碼品質、測試策略，避免過度行銷語言
5. WHEN 提及 AI 模型時，THE Deliverable_Generator SHALL 統一使用「Meta Llama 3（透過 Ollama 本地部署）」與「Google Gemini」的完整描述
6. THE Deliverable_Generator SHALL 在所有交付物中包含團隊分工資訊：Member A 負責後端架構、AI 模型、雲端部署；Member B 負責資料處理、前端介面、版本控制、簡報
7. THE Deliverable_Generator SHALL 確保 Competition_1 的所有交付物一致地以問題解決敘事框架呈現：問題定義（台灣詐騙現況與話術演化）→ 解決方案（ScamOracle 的 NLP、異常偵測、LLM 預測整合方案）→ 成效展示（可量化的預警與防詐效益指標）
