# 實作計畫：即時資料自動更新 (Live Data Auto-Update)

## 概述

將系統從硬編碼的靜態詐騙統計資料轉換為可自動從外部來源擷取最新台灣詐騙統計資料的動態架構。實作包含 8 個核心元件（DataSourceRegistry、DataFetcher、DataNormalizer、FetchScheduler、CacheManager、FallbackProvider、FreshnessIndicator、設定擴充），以及 10 個正確性屬性的驗證測試。

## 任務

- [x] 1. 建立專案結構與核心資料模型
  - [x] 1.1 建立 `app/live_data/` 模組目錄與 `__init__.py`
    - 建立 `app/live_data/__init__.py`，匯出所有公開類別
    - _需求: 1, 2, 3_

  - [x] 1.2 實作 Pydantic 資料模型 (`app/live_data/models.py`)
    - 實作 `ScamTypeStat`、`MonthlyTrendEntry`、`AnnualStat`、`NormalizedData` Pydantic BaseModel
    - 實作 `NormalizedData` 的 `model_validator`：`validate_non_negative_regions` 與 `validate_age_distribution_sum`
    - 實作 `FetchResult`、`DataSourceConfig`、`CachedData`、`FreshnessInfo` 資料類別
    - _需求: 3.1, 3.2, 3.4, 3.5_

  - [ ]* 1.3 撰寫 Property 5 屬性測試：資料驗證規則
    - **Property 5: 資料驗證規則**
    - 使用 Hypothesis 生成隨機 `NormalizedData`（含無效值），驗證非負整數與比例總和 0.99~1.01 的接受/拒絕行為
    - **驗證: 需求 3.4**

  - [ ]* 1.4 撰寫 Property 6 屬性測試：NormalizedData JSON 往返
    - **Property 6: NormalizedData JSON 往返**
    - 使用 Hypothesis 生成隨機有效 `NormalizedData`，驗證 `model_dump_json()` → `model_validate_json()` 往返等價
    - **驗證: 需求 3.5**

- [x] 2. 實作 DataSourceRegistry 與設定擴充
  - [x] 2.1 擴充 `app/config.py` Settings 類別
    - 新增 `data_fetch_interval_hours`、`data_fetch_timeout_seconds`、`data_cache_file_path`、`data_source_failure_threshold`、`data_source_recovery_hours` 設定欄位
    - _需求: 2.1, 2.2, 4.3_

  - [x] 2.2 實作 DataSourceRegistry (`app/live_data/registry.py`)
    - 實作 `DataSourceRegistry` 類別：`__init__`、`get_active_sources`、`record_failure`、`record_success`、`_check_auto_recovery`
    - 支援依優先順序排序回傳啟用來源
    - 連續失敗 3 次自動停用 1 小時，到期後自動恢復
    - _需求: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 2.3 撰寫 Property 1 屬性測試：來源優先順序排序
    - **Property 1: 來源優先順序排序**
    - 使用 Hypothesis 生成隨機 `DataSourceConfig` 清單，驗證 `get_active_sources()` 僅回傳啟用來源且依 priority 由小到大排序
    - **驗證: 需求 2.3**

  - [ ]* 2.4 撰寫 Property 2 屬性測試：來源失敗狀態機
    - **Property 2: 來源失敗狀態機**
    - 使用 Hypothesis 生成隨機 success/failure 呼叫序列，驗證連續 3 次失敗後停用、恢復機制
    - **驗證: 需求 2.4**

- [x] 3. 實作 DataNormalizer
  - [x] 3.1 實作 DataNormalizer 核心邏輯 (`app/live_data/normalizer.py`)
    - 實作 `DataNormalizer` 類別：`__init__`、`register_parser`、`normalize`、`validate`
    - 實作解析器註冊機制（`ParserFunc` 型別）
    - 實作缺失欄位以快取值填補邏輯
    - _需求: 3.1, 3.2, 3.3, 8.1, 8.2_

  - [x] 3.2 實作內建解析器 (`app/live_data/parsers.py`)
    - 實作 `json_gov_parser`：解析政府開放資料 JSON 格式
    - 實作 `csv_stats_parser`：解析 CSV 統計報表格式
    - _需求: 8.3_

  - [ ]* 3.3 撰寫 Property 3 屬性測試：正規化器產生有效輸出
    - **Property 3: 正規化器產生有效輸出**
    - 使用 Hypothesis 生成隨機符合預期格式的原始資料，驗證 `normalize()` 產生通過 Pydantic 驗證的 `NormalizedData`
    - **驗證: 需求 3.1, 3.2**

  - [ ]* 3.4 撰寫 Property 4 屬性測試：缺失欄位快取填補
    - **Property 4: 缺失欄位快取填補**
    - 使用 Hypothesis 生成隨機部分資料 + 隨機快取，驗證填補後 `NormalizedData` 包含完整欄位
    - **驗證: 需求 3.3**

- [x] 4. Checkpoint - 確認核心元件測試通過
  - 確認所有測試通過，若有問題請詢問使用者。

- [x] 5. 實作 CacheManager 與 FallbackProvider
  - [x] 5.1 實作 CacheManager (`app/live_data/cache_manager.py`)
    - 實作 `CacheManager` 類別：`__init__`、`store`、`load`、`get_freshness_info`
    - 實作雙層快取（記憶體 + 磁碟 JSON）：`_persist_to_disk`、`_load_from_disk`
    - 磁碟快取路徑：`data/live_cache.json`
    - _需求: 5.1, 5.2, 5.4, 5.5_

  - [x] 5.2 實作 FallbackProvider (`app/live_data/fallback.py`)
    - 實作 `FallbackProvider` 類別：`__init__`、`get_data`、`_load_static_defaults`
    - 降級順序：磁碟快取 → `data/taiwan_scam_data.py` 靜態預設資料
    - 靜態資料轉換為 `NormalizedData` 格式，`source_name` 標記為「靜態預設資料」
    - _需求: 5.3_

  - [ ]* 5.3 撰寫 Property 8 屬性測試：快取磁碟持久化往返
    - **Property 8: 快取磁碟持久化往返**
    - 使用 Hypothesis 生成隨機有效 `NormalizedData`，驗證 `CacheManager` 儲存至磁碟後再載入等價
    - **驗證: 需求 5.4, 5.5**

  - [ ]* 5.4 撰寫單元測試：FallbackProvider 靜態資料降級
    - 測試無快取時回傳 `taiwan_scam_data.py` 資料
    - 測試回傳資料的 `source_name` 為「靜態預設資料」
    - _需求: 5.3_

- [x] 6. 實作 DataFetcher
  - [x] 6.1 實作 DataFetcher (`app/live_data/fetcher.py`)
    - 實作 `DataFetcher` 類別：`__init__`、`fetch`、`get_recent_results`、`consecutive_failure_count`
    - 使用 `httpx.AsyncClient` 進行非同步 HTTP 請求，單一來源逾時 30 秒
    - 依優先順序逐一嘗試來源，第一個成功即停止
    - 保留最近 100 筆 `FetchResult` 紀錄（環形緩衝區）
    - 所有來源失敗時觸發 `FallbackProvider`
    - 連續 3 次排程擷取失敗時記錄 ERROR 日誌（含「連續擷取失敗」字樣）
    - _需求: 1.1, 1.2, 1.3, 1.4, 1.5, 7.1, 7.3_

  - [ ]* 6.2 撰寫 Property 10 屬性測試：FetchResult 環形緩衝區
    - **Property 10: FetchResult 環形緩衝區**
    - 使用 Hypothesis 生成隨機長度 FetchResult 序列，驗證 `get_recent_results(100)` 長度不超過 100 且保留最近紀錄
    - **驗證: 需求 7.2**

  - [ ]* 6.3 撰寫單元測試：DataFetcher 成功與失敗路徑
    - Mock HTTP 200 回應，驗證正規化與快取流程
    - Mock 所有來源失敗，驗證 FallbackProvider 被呼叫
    - 驗證連續 3 次失敗後 ERROR 日誌內容
    - _需求: 1.1, 1.3, 1.4, 1.5, 7.3_

- [x] 7. 實作 FetchScheduler
  - [x] 7.1 實作 FetchScheduler (`app/live_data/scheduler.py`)
    - 實作 `FetchScheduler` 類別：`__init__`、`start`、`stop`、`trigger_now`、`is_running`、`validate_interval`
    - 復用 `PredictionScheduler` 的 `BackgroundScheduler` + `IntervalTrigger` 模式
    - 預設間隔 6 小時，透過 `DATA_FETCH_INTERVAL_HOURS` 環境變數設定
    - 有效範圍 1~168 小時，超出範圍使用預設值 6
    - 啟動時立即觸發一次擷取，使用 `max_instances=1` 防止任務重疊
    - _需求: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 7.2 撰寫 Property 7 屬性測試：排程間隔驗證
    - **Property 7: 排程間隔驗證**
    - 使用 Hypothesis 生成隨機整數，驗證 `validate_interval()` 在 1~168 回傳原值，超出範圍回傳 6
    - **驗證: 需求 4.3, 4.4**

- [x] 8. Checkpoint - 確認後端元件測試通過
  - 確認所有測試通過，若有問題請詢問使用者。

- [x] 9. 實作 FreshnessIndicator 與 Dashboard 整合
  - [x] 9.1 實作 FreshnessIndicator (`app/dashboard/page_modules/freshness.py`)
    - 實作 `render_freshness_indicator(info: FreshnessInfo) -> str` 函數
    - 四種顯示狀態：綠色（✅ 最新）、黃色（⚠️ 快取 <24h）、紅色（🔴 快取 ≥24h）、灰色（📋 靜態）
    - _需求: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 9.2 整合 Dashboard 頁面
    - 在 `app/dashboard/streamlit_app.py` 頂部加入 FreshnessIndicator 顯示
    - 加入「立即更新」按鈕，觸發 `FetchScheduler.trigger_now()`
    - 替換 Dashboard 資料來源：從 `data/taiwan_scam_data.py` 改為 `CacheManager`
    - _需求: 6.1, 6.6_

  - [ ]* 9.3 撰寫 Property 9 屬性測試：新鮮度指示器渲染
    - **Property 9: 新鮮度指示器渲染**
    - 使用 Hypothesis 生成隨機 `FreshnessInfo`，驗證渲染輸出包含正確的 emoji 與格式
    - **驗證: 需求 6.2, 6.3, 6.4, 6.5**

- [x] 10. 整合 API Gateway 生命週期與模組串接
  - [x] 10.1 整合 FetchScheduler 至 API Gateway 生命週期
    - 在 `app/api_gateway/main.py` 的 `lifespan` 中加入 `FetchScheduler` 的啟動與停止
    - _需求: 4.1, 4.2_

  - [x] 10.2 建立模組工廠函數 (`app/live_data/__init__.py`)
    - 實作 `get_fetch_scheduler()`、`get_cache_manager()` 等全域單例取得函數
    - 串接所有元件：Registry → Fetcher → Normalizer → CacheManager → FallbackProvider → Scheduler
    - _需求: 1, 2, 3, 4, 5_

  - [ ]* 10.3 撰寫整合測試：端對端擷取流程
    - Mock 外部 API，驗證從擷取到快取的完整流程
    - 驗證 Dashboard 能正確讀取 CacheManager 資料
    - 驗證排程器啟動 → 觸發 → 停止的完整生命週期
    - _需求: 1, 4, 5_

- [x] 11. 最終 Checkpoint - 確認所有測試通過
  - 確認所有測試通過，若有問題請詢問使用者。

## 備註

- 標記 `*` 的任務為選用任務，可跳過以加速 MVP 開發
- 每個任務皆參照具體需求編號，確保可追溯性
- Checkpoint 任務確保漸進式驗證
- 屬性測試驗證通用正確性屬性（10 個 Property）
- 單元測試驗證特定範例與邊界條件
- 所有測試檔案集中於 `tests/test_live_data.py`
