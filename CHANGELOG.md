# Changelog

所有重大變更皆記錄於此文件。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)，
版本號遵循 [Semantic Versioning](https://semver.org/lang/zh-TW/)。

## [1.0.0] - 2026-08-03

### 新增
- 六大核心功能模組完整實作
  - 話術裂變生成引擎（LangChain + GPT-4o / Gemini / Ollama）
  - XAI 可解釋分析（五類心理操控特徵 + 信心分數）
  - Isolation Forest 趨勢偵測預警（每日排程）
  - Risk Vector API（REST JSON 標準化風險向量）
  - 互動式防詐免疫訓練（含防詐免疫證書）
  - 12 頁面即時威脅儀表板
- 詐騙對話模擬器支援 4 種情境：假冒銀行客服、投資詐騙、愛情詐騙、假冒政府機關
- RBAC 角色型存取控制（4 角色 × 3 操作）
- SHA-256 雜湊鏈稽核日誌（防竄改）
- TOTP MFA 二次驗證（批量匯出 > 100 筆）
- 四層資料降級策略（即時擷取 → 磁碟快取 → 靜態預設）
- LLM 備援自動切換（主 provider 失敗自動切換備援）
- CSV/JSON 報案資料匯入 + PII 去識別化
- API Gateway（API Key + 滑動視窗速率限制 + 請求日誌）
- Docker Compose 基礎設施（PostgreSQL + Redis + Qdrant）
- 完整自動化測試套件（376+ 筆，含 Property-Based Testing）
- MIT License

### 安全性提升
- 密碼雜湊從 SHA-256 升級為 bcrypt（自動加鹽）
- 向下相容舊格式，登入時自動升級至 bcrypt

### 文件
- 完整 README（含快速開始、環境設定、API 文件、專案結構）
- AWS 部署指南
- Demo 操作指南
- 安全政策文件（SECURITY.md）
