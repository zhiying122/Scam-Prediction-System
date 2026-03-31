-- AI 詐騙進化預測系統 - PostgreSQL 初始化腳本
-- 建立必要的擴充套件與初始設定

-- 啟用 UUID 生成擴充套件
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 啟用 pg_trgm 擴充套件（支援模糊文字搜尋）
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 設定時區為 UTC
SET timezone = 'UTC';
