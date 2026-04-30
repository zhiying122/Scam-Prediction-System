# 實作計畫：比賽交付物產出系統

## 概覽

本實作計畫將 ScamOracle 比賽交付物產出系統的設計拆解為可逐步執行的編碼任務。系統採用 DataExtractor → ConsistencyValidator → TemplateRenderer 三層架構，使用 Jinja2 模板引擎產出六份 Markdown 交付物。所有任務使用 Python 實作，與現有專案技術棧一致。

## 任務

- [x] 1. 建立模組結構與核心資料模型
  - [x] 1.1 建立 `app/deliverable_generator/` 目錄結構與 `__init__.py`
    - 建立 `app/deliverable_generator/__init__.py`
    - 建立 `app/deliverable_generator/models.py`
    - 建立 `app/deliverable_generator/extractor.py`
    - 建立 `app/deliverable_generator/validator.py`
    - 建立 `app/deliverable_generator/renderer.py`
    - 建立 `app/deliverable_generator/generator.py`
    - 建立 `templates/competition/` 模板目錄
    - _需求：7.1, 7.2_

  - [x] 1.2 實作 `models.py` 核心資料模型
    - 定義 `TeamMember` dataclass（name, responsibilities）
    - 定義 `ProjectData` dataclass，包含所有品牌資訊、技術數據、統計數據、AI 模型資訊、心理特徵、團隊分工、測試策略、架構層次等欄位
    - 定義 `ValidationError` 與 `ValidationResult` dataclass
    - 定義 `DeliverableOutput` dataclass（competition, deliverable_type, content, file_path, rendered_at, data_hash）
    - 定義 `VideoScene` dataclass（scene_number, time_start, time_end, visual_description, narration, subtitle_hint, section_tag）
    - 定義 `PosterSection` dataclass（section_name, position, area_percentage, content_elements, visual_type）
    - _需求：7.1, 7.2, 7.5, 7.6_

  - [ ]* 1.3 撰寫 `models.py` 的單元測試
    - 測試 ProjectData 可正確實例化
    - 測試 TeamMember 欄位存取
    - 測試 ValidationResult 的 is_valid 判斷
    - _需求：7.1_

- [x] 2. 實作 DataExtractor 資料萃取器
  - [x] 2.1 實作 `extractor.py` 的 `DataExtractor` 類別
    - 實作 `extract()` 方法，從專案檔案萃取完整 ProjectData
    - 實作 `_count_tests()` 方法，掃描 `tests/` 目錄計算測試函數總數
    - 實作 `_list_modules()` 方法，列出 `app/` 下的 10 個核心模組名稱
    - 實作 `_extract_tech_stack()` 方法，從 README.md 萃取技術棧資訊
    - 實作 `_extract_scam_statistics()` 方法，從 `data/taiwan_scam_data.py` 萃取統計數據
    - 實作降級策略：當檔案缺失時使用硬編碼預設值並記錄警告
    - _需求：7.1, 7.2, 7.5, 7.6_

  - [ ]* 2.2 撰寫 DataExtractor 的單元測試
    - 測試從實際專案檔案萃取資料的正確性
    - 測試檔案缺失時的降級行為
    - 測試 test_count 計算結果為正整數
    - 測試 module_names 包含 10 個模組
    - _需求：7.1_

- [x] 3. 實作 ConsistencyValidator 一致性驗證器
  - [x] 3.1 實作 `validator.py` 的 `ConsistencyValidator` 類別
    - 定義 `BANNED_AI_TOOLS` 禁止工具名稱集合（deepseek, baidu, ernie, qwen, tongyi, chatglm, zhipu, minimax, baichuan）
    - 實作 `validate()` 方法，驗證 ProjectData 所有一致性規則
    - 驗證規則包含：test_count > 0、embedding_dim == 384、dashboard_page_count == 12、api_endpoint_count == 7、len(module_names) == 10、project_name == "ScamOracle"、len(team_members) == 2、len(psychological_dimensions) == 5
    - 實作 `_check_banned_ai_tools()` 方法，檢查 llm_models 是否包含禁止工具
    - _需求：1.5, 2.6, 7.1, 7.2_

  - [ ]* 3.2 撰寫屬性測試：禁止使用中國大陸 AI 工具
    - **屬性 2：禁止使用中國大陸 AI 工具**
    - 使用 Hypothesis 隨機生成包含禁止工具名稱的 llm_models 列表
    - 驗證 ConsistencyValidator 對所有禁止工具均回傳 is_valid=False
    - **驗證需求：1.5, 2.6**

  - [ ]* 3.3 撰寫 ConsistencyValidator 的單元測試
    - 測試合法 ProjectData 通過驗證
    - 測試 embedding_dim ≠ 384 時驗證失敗
    - 測試 project_name ≠ "ScamOracle" 時驗證失敗
    - 測試多個驗證錯誤同時回傳
    - _需求：7.1_

- [x] 4. 檢查點 — 確認核心元件正確
  - 確保所有測試通過，如有問題請詢問使用者。

- [x] 5. 實作比賽一 Jinja2 模板
  - [x] 5.1 建立比賽一計畫書模板 `templates/competition/comp1_proposal.md.j2`
    - 包含 9 個必要章節：專案摘要、問題背景、解決方案、產品功能展示、創新亮點、使用者價值、AI 技術應用說明、團隊分工、未來展望
    - 產品功能展示以使用者情境故事呈現：詐騙對話模擬器、XAI 話術分析、詐騙免疫訓練、即時威脅監控
    - 包含 MaiAgent 協調運作說明
    - 包含 Scam_DNA 五維心理特徵量化圖文說明（非技術人員可理解）
    - 包含「以 AI 對抗 AI」逆向思維創新點
    - 以問題解決敘事框架呈現：問題定義 → 解決方案 → 成效展示
    - 明確標示使用 Meta Llama 3 與 Google Gemini，未使用中國大陸 AI 工具
    - _需求：1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 7.3, 7.5, 7.7_

  - [x] 5.2 建立比賽一影片腳本模板 `templates/competition/comp1_video_script.md.j2`
    - 產出 10 個分鏡、總長 5 分鐘（300 秒）的腳本
    - 每個分鏡包含：分鏡編號、時間碼、畫面描述、旁白文字、字幕提示
    - 包含可清楚辨識的「應用介紹」段落
    - 包含可清楚辨識的「操作方式」段落，展示至少 4 個功能操作
    - 包含可清楚辨識的「預期效果」段落，展示數據與預警能力
    - 以使用者故事開場（民眾接到詐騙電話情境）
    - 包含「以 AI 對抗 AI」核心理念視覺化呈現
    - 以問題解決敘事弧線組織結構
    - _需求：3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

  - [x] 5.3 建立比賽一海報內容模板 `templates/competition/comp1_poster.md.j2`
    - 以產品使用情境為主視覺：系統介面截圖區域、使用者操作流程圖、功能亮點卡片
    - 包含 Scam_DNA 五維雷達圖視覺化設計說明
    - 包含「使用 Meta Llama 3 & Google Gemini」醒目徽章設計
    - 包含台灣詐騙現況關鍵數據視覺化區塊
    - 包含「以 AI 對抗 AI」核心標語與品牌識別
    - 以問題解決敘事結構編排版面：上方問題 → 中間方案 → 下方成效
    - _需求：5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [x] 6. 實作比賽二 Jinja2 模板
  - [x] 6.1 建立比賽二計畫書模板 `templates/competition/comp2_proposal.md.j2`
    - 遵循比賽指定四大章節結構
    - 「一、作品及功能簡介」：專案摘要、問題背景、核心功能概述、10 個核心模組功能說明
    - 「二、作品特色及創意效益描述」：以 AI 對抗 AI、Scam_DNA、409 測試策略、效能指標
    - 「三、作品系統架構」：四層架構圖（Input → Engine → Analysis → Output）、Docker Compose 三服務、技術棧
    - 「四、人工智慧工具輔助開發使用情形」：GitHub Copilot、Prompt Engineering
    - 明確標示使用 Meta Llama 3 與 Google Gemini
    - _需求：2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 7.4, 7.5_

  - [x] 6.2 建立比賽二影片腳本模板 `templates/competition/comp2_video_script.md.j2`
    - 產出 7 個分鏡、總長 2 分鐘（120 秒）的腳本
    - 每個分鏡包含：分鏡編號、時間碼、畫面描述、旁白文字、技術標註
    - 包含四層系統架構動畫流程展示
    - 包含至少 2 段程式碼片段畫面展示（generator.py LangChain Prompt、embedder.py S-BERT 嵌入）
    - 包含 409 測試全數通過的終端機輸出畫面
    - 包含 GitHub Copilot 使用畫面展示
    - 包含 Docker Compose 啟動與 API Swagger UI 操作展示
    - _需求：4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 6.3 建立比賽二海報內容模板 `templates/competition/comp2_poster.md.j2`
    - A1 尺寸（594mm × 841mm）版面配置
    - 大型系統架構流程圖為主視覺，佔海報面積至少 40%
    - 架構圖標註關鍵技術參數：S_BERT 384 維、Isolation Forest、K-Means、LangChain
    - 包含至少 2 個程式碼片段區塊（等寬字體、語法高亮配色）
    - 包含測試覆蓋率與品質指標區塊：409 測試、PBT、三種測試類型
    - 包含技術棧圖示列：FastAPI、Streamlit、Docker、PostgreSQL、Redis、Qdrant、Ollama、scikit-learn
    - 包含「使用 Meta Llama 3 & Google Gemini」醒目徽章
    - 包含 AI 輔助開發工具使用說明區塊
    - _需求：6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [x] 7. 檢查點 — 確認所有模板建立完成
  - 確保所有測試通過，如有問題請詢問使用者。

- [x] 8. 實作 TemplateRenderer 模板渲染器
  - [x] 8.1 實作 `renderer.py` 的 `TemplateRenderer` 類別
    - 初始化 Jinja2 Environment，設定 template_dir 為 `templates/competition/`
    - 實作 `render()` 方法，根據 competition 與 deliverable_type 選擇對應模板並渲染
    - 實作 `render_all()` 方法，渲染全部六份交付物並回傳 {文件名稱: 內容} 字典
    - _需求：7.1, 7.2, 7.3, 7.4_

  - [ ]* 8.2 撰寫屬性測試：計畫書必要章節完整性
    - **屬性 1：計畫書必要章節完整性**
    - 使用 Hypothesis 隨機生成合法 ProjectData
    - 驗證比賽一計畫書包含 9 個必要章節標題
    - 驗證比賽二計畫書包含 4 個指定章節標題
    - **驗證需求：1.1, 2.1**

  - [ ]* 8.3 撰寫屬性測試：影片腳本時長正確性
    - **屬性 3：影片腳本時長正確性**
    - 使用 Hypothesis 隨機生成合法 ProjectData
    - 驗證比賽一影片腳本分鏡時間碼總和為 300 秒
    - 驗證比賽二影片腳本分鏡時間碼總和為 120 秒
    - 驗證每個分鏡結束時間碼大於起始時間碼
    - **驗證需求：3.1, 4.1**

  - [ ]* 8.4 撰寫屬性測試：跨交付物資料一致性
    - **屬性 4：跨交付物資料一致性**
    - 使用 Hypothesis 隨機生成合法 ProjectData
    - 渲染全部六份交付物後，驗證所有文件中的技術數據（測試數量、向量維度、頁面數、端點數）、專案名稱、副標題、團隊資訊完全一致
    - **驗證需求：7.1, 7.2, 7.6**

  - [ ]* 8.5 撰寫屬性測試：ProjectData 欄位渲染完整性
    - **屬性 5：ProjectData 欄位渲染完整性**
    - 使用 Hypothesis 隨機生成合法 ProjectData
    - 驗證比賽二計畫書包含所有 module_names、architecture_layers、docker_services
    - 驗證比賽二海報包含所有 tech_stack 技術名稱
    - **驗證需求：2.2, 2.4, 6.6**

  - [ ]* 8.6 撰寫屬性測試：比賽二海報架構圖面積下限
    - **屬性 6：比賽二海報架構圖面積下限**
    - 使用 Hypothesis 隨機生成合法 ProjectData
    - 驗證比賽二海報中架構流程圖區塊的 area_percentage >= 40%
    - **驗證需求：6.2**

- [x] 9. 實作 DeliverableGenerator 主入口與整合
  - [x] 9.1 實作 `generator.py` 的 `DeliverableGenerator` 類別
    - 初始化時注入 DataExtractor、ConsistencyValidator、TemplateRenderer（支援依賴注入）
    - 實作 `generate()` 方法：萃取資料 → 驗證一致性 → 渲染模板 → 寫入檔案
    - 實作 `generate_all()` 方法：產出全部六份交付物至 `deliverables/` 目錄
    - 驗證失敗時拋出 ConsistencyError 並回傳 ValidationResult
    - _需求：7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

  - [ ]* 9.2 撰寫 DeliverableGenerator 整合測試
    - 測試完整 generate_all() 流程（萃取 → 驗證 → 渲染 → 寫入）
    - 測試產出六份 .md 檔案至 deliverables/ 目錄
    - 測試驗證失敗時的錯誤處理
    - _需求：7.1, 7.2_

  - [ ]* 9.3 撰寫 TemplateRenderer 的單元測試
    - 測試比賽一計畫書包含 MaiAgent 描述（需求 1.2）
    - 測試比賽一計畫書包含 4 個核心功能名稱（需求 1.3）
    - 測試比賽一計畫書包含 Scam_DNA 五維說明（需求 1.4）
    - 測試比賽一計畫書包含「以 AI 對抗 AI」（需求 1.6）
    - 測試比賽一影片腳本包含「應用介紹」「操作方式」「預期效果」三段（需求 3.2, 3.3, 3.4）
    - 測試比賽一影片腳本以使用者故事開場（需求 3.5）
    - 測試比賽二影片腳本包含至少 2 段程式碼片段（需求 4.3）
    - 測試比賽二影片腳本包含測試執行畫面（需求 4.4）
    - 測試比賽一海報包含五維雷達圖說明（需求 5.3）
    - 測試比賽二海報包含 A1 尺寸標註（需求 6.1）
    - 測試比賽二海報包含至少 2 個程式碼片段（需求 6.4）
    - 測試 AI 模型完整描述格式（需求 7.5）
    - _需求：1.2, 1.3, 1.4, 1.6, 3.2, 3.3, 3.4, 3.5, 4.3, 4.4, 5.3, 6.1, 6.4, 7.5_

- [x] 10. 最終檢查點 — 確保所有測試通過
  - 確保所有測試通過，如有問題請詢問使用者。

## 備註

- 標記 `*` 的任務為選擇性任務，可跳過以加速 MVP 開發
- 每個任務均標註對應的需求編號，確保需求可追溯性
- 檢查點確保增量式驗證，及早發現問題
- 屬性測試驗證設計文件中定義的 6 個正確性屬性
- 單元測試驗證具體範例與邊緣案例，與屬性測試互補
- 所有模板與程式碼使用 Python + Jinja2，與現有專案技術棧一致
