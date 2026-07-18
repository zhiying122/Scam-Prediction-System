-- AI 詐騙進化預測系統 - PostgreSQL 初始化腳本
-- 建立必要的擴充套件、資料表與索引
-- 對應 app/models/ 下的所有資料模型

-- ── 擴充套件 ─────────────────────────────────────────────────────────────────

-- 啟用 UUID 生成擴充套件
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 啟用 pg_trgm 擴充套件（支援模糊文字搜尋）
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 設定時區為 UTC
SET timezone = 'UTC';


-- ── scam_scripts（詐騙話術）───────────────────────────────────────────────────
-- 對應 app/models/scam_script.py::ScamScript

CREATE TABLE IF NOT EXISTS scam_scripts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id         VARCHAR(64)  NOT NULL,
    content         TEXT         NOT NULL,
    scenario        VARCHAR(64)  NOT NULL,
    target_audience VARCHAR(64)  NOT NULL,
    psychological_tags  JSONB    NOT NULL DEFAULT '[]',
    language        VARCHAR(16)  NOT NULL DEFAULT 'zh-TW',
    is_regulated    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      VARCHAR(64)  NOT NULL,
    -- 業務約束：is_regulated 恆為 true（需求 1.5）
    CONSTRAINT chk_is_regulated CHECK (is_regulated = TRUE)
);

CREATE INDEX IF NOT EXISTS idx_scam_scripts_task_id   ON scam_scripts (task_id);
CREATE INDEX IF NOT EXISTS idx_scam_scripts_scenario  ON scam_scripts (scenario);
CREATE INDEX IF NOT EXISTS idx_scam_scripts_created_at ON scam_scripts (created_at DESC);
-- 全文搜尋索引（支援話術內容模糊搜尋）
CREATE INDEX IF NOT EXISTS idx_scam_scripts_content_trgm
    ON scam_scripts USING gin (content gin_trgm_ops);


-- ── case_reports（報案資料）───────────────────────────────────────────────────
-- 對應 app/models/case_report.py::CaseReport

CREATE TABLE IF NOT EXISTS case_reports (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source           VARCHAR(128) NOT NULL,
    scam_type        VARCHAR(64)  NOT NULL,
    description      TEXT         NOT NULL,
    reported_at      DATE         NOT NULL,
    import_batch_id  UUID         NOT NULL,
    pii_removed      BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_case_reports_scam_type    ON case_reports (scam_type);
CREATE INDEX IF NOT EXISTS idx_case_reports_reported_at  ON case_reports (reported_at DESC);
CREATE INDEX IF NOT EXISTS idx_case_reports_batch        ON case_reports (import_batch_id);
-- 全文搜尋
CREATE INDEX IF NOT EXISTS idx_case_reports_desc_trgm
    ON case_reports USING gin (description gin_trgm_ops);


-- ── risk_vectors（風險向量）───────────────────────────────────────────────────
-- 對應 app/models/risk_vector.py::RiskVector

CREATE TABLE IF NOT EXISTS risk_vectors (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    high_risk_features  JSONB        NOT NULL DEFAULT '[]',
    scam_cluster_label  VARCHAR(64)  NOT NULL,
    risk_score          NUMERIC(5,4) NOT NULL CHECK (risk_score BETWEEN 0.0 AND 1.0),
    risk_level          VARCHAR(2)   NOT NULL CHECK (risk_level IN ('高', '中', '低')),
    time_range_start    TIMESTAMPTZ  NOT NULL,
    time_range_end      TIMESTAMPTZ  NOT NULL,
    version             VARCHAR(32)  NOT NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_time_range CHECK (time_range_end > time_range_start)
);

CREATE INDEX IF NOT EXISTS idx_risk_vectors_risk_level    ON risk_vectors (risk_level);
CREATE INDEX IF NOT EXISTS idx_risk_vectors_cluster_label ON risk_vectors (scam_cluster_label);
CREATE INDEX IF NOT EXISTS idx_risk_vectors_created_at    ON risk_vectors (created_at DESC);


-- ── alert_events（預警事件）───────────────────────────────────────────────────
-- 對應 app/models/alert_event.py::AlertEvent

CREATE TABLE IF NOT EXISTS alert_events (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    risk_level          VARCHAR(2)   NOT NULL CHECK (risk_level IN ('高', '中', '低')),
    trigger_features    JSONB        NOT NULL DEFAULT '[]',
    risk_vector_id      UUID         NOT NULL REFERENCES risk_vectors (id) ON DELETE CASCADE,
    notified_operators  JSONB        NOT NULL DEFAULT '[]',
    notified_at         TIMESTAMPTZ  NOT NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alert_events_risk_level   ON alert_events (risk_level);
CREATE INDEX IF NOT EXISTS idx_alert_events_created_at   ON alert_events (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_events_vector_id    ON alert_events (risk_vector_id);


-- ── model_versions（模型版本）────────────────────────────────────────────────
-- 對應 app/models/model_version.py::ModelVersion

CREATE TABLE IF NOT EXISTS model_versions (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version              VARCHAR(32)  NOT NULL UNIQUE,
    accuracy_before      NUMERIC(5,4) NOT NULL CHECK (accuracy_before BETWEEN 0.0 AND 1.0),
    accuracy_after       NUMERIC(5,4) NOT NULL CHECK (accuracy_after  BETWEEN 0.0 AND 1.0),
    training_data_count  INTEGER      NOT NULL CHECK (training_data_count >= 0),
    new_cluster_count    INTEGER      NOT NULL CHECK (new_cluster_count >= 0),
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by           VARCHAR(64)  NOT NULL,
    is_active            BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_model_versions_is_active  ON model_versions (is_active);
CREATE INDEX IF NOT EXISTS idx_model_versions_created_at ON model_versions (created_at DESC);

-- 確保最多只有一個 active 版本
CREATE UNIQUE INDEX IF NOT EXISTS idx_model_versions_one_active
    ON model_versions (is_active)
    WHERE is_active = TRUE;


-- ── access_logs（存取日誌）────────────────────────────────────────────────────
-- 對應 app/models/access_log.py::AccessLog
-- 使用 append-only 設計（不允許 UPDATE / DELETE）

CREATE TABLE IF NOT EXISTS access_logs (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operator_id   VARCHAR(64)  NOT NULL,
    action        VARCHAR(32)  NOT NULL CHECK (
                      action IN ('read', 'export', 'bulk_export', 'write', 'delete', 'generate', 'import')
                  ),
    resource_id   VARCHAR(128) NOT NULL,
    resource_type VARCHAR(64)  NOT NULL,
    timestamp     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    prev_hash     VARCHAR(64)  NOT NULL,
    current_hash  VARCHAR(64)  NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_access_logs_operator_id ON access_logs (operator_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_timestamp   ON access_logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_access_logs_action      ON access_logs (action);
CREATE INDEX IF NOT EXISTS idx_access_logs_resource    ON access_logs (resource_type, resource_id);

-- 防止竄改：禁止對 access_logs 執行 UPDATE 或 DELETE
CREATE OR REPLACE RULE access_logs_no_update AS
    ON UPDATE TO access_logs DO INSTEAD NOTHING;

CREATE OR REPLACE RULE access_logs_no_delete AS
    ON DELETE TO access_logs DO INSTEAD NOTHING;


-- ── 初始資料：預設模型版本 ────────────────────────────────────────────────────

INSERT INTO model_versions (
    id, version, accuracy_before, accuracy_after,
    training_data_count, new_cluster_count, created_by, is_active
)
VALUES (
    uuid_generate_v4(),
    'v1.0.0',
    0.000,   -- 初始版本無前版準確率
    0.889,   -- 對應 taiwan_scam_data.py::MODEL_PERFORMANCE accuracy
    1200,    -- 對應 MODEL_PERFORMANCE test_samples
    8,       -- 對應 8 種詐騙類型初始分群
    'system',
    TRUE
)
ON CONFLICT (version) DO NOTHING;
