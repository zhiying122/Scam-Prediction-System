"""
系統設定模組

集中管理所有環境變數，包含資料庫連線、API 金鑰、LLM 設定等。
使用 pydantic-settings 從環境變數或 .env 檔案載入設定。
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    系統全域設定

    所有設定均可透過環境變數覆寫，
    環境變數名稱與欄位名稱相同（大寫）。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── 應用程式基本設定 ──────────────────────────────────────────────────────
    app_name: str = Field(default="ScamDNA — AI 詐騙話術進化預警系統", description="應用程式名稱")
    app_env: Literal["development", "testing", "production"] = Field(
        default="development", description="執行環境"
    )
    debug: bool = Field(default=False, description="是否啟用除錯模式")
    log_level: str = Field(default="INFO", description="日誌等級")

    # ── PostgreSQL 資料庫設定 ─────────────────────────────────────────────────
    postgres_host: str = Field(default="localhost", description="PostgreSQL 主機位址")
    postgres_port: int = Field(default=5432, description="PostgreSQL 連接埠")
    postgres_db: str = Field(default="scam_prediction", description="資料庫名稱")
    postgres_user: str = Field(default="postgres", description="資料庫使用者名稱")
    postgres_password: str = Field(default="postgres", description="資料庫密碼")

    @property
    def postgres_dsn(self) -> str:
        """組合 PostgreSQL 連線字串（asyncpg 格式）"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_dsn_sync(self) -> str:
        """組合 PostgreSQL 同步連線字串（psycopg2 格式，用於 Alembic 遷移）"""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis 快取設定 ────────────────────────────────────────────────────────
    redis_host: str = Field(default="localhost", description="Redis 主機位址")
    redis_port: int = Field(default=6379, description="Redis 連接埠")
    redis_db: int = Field(default=0, description="Redis 資料庫編號")
    redis_password: str = Field(default="", description="Redis 密碼（空字串表示無密碼）")
    redis_cache_ttl: int = Field(default=86400, description="快取預設 TTL（秒），預設 24 小時")

    @property
    def redis_url(self) -> str:
        """組合 Redis 連線 URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ── Qdrant 向量資料庫設定 ─────────────────────────────────────────────────
    qdrant_host: str = Field(default="localhost", description="Qdrant 主機位址")
    qdrant_port: int = Field(default=6333, description="Qdrant HTTP 連接埠")
    qdrant_grpc_port: int = Field(default=6334, description="Qdrant gRPC 連接埠")
    qdrant_api_key: str = Field(default="", description="Qdrant API 金鑰（雲端版本使用）")
    qdrant_collection_name: str = Field(
        default="semantic_vectors", description="語意向量集合名稱"
    )
    qdrant_vector_size: int = Field(default=384, description="語意向量維度（MiniLM 輸出）")

    # ── LLM API 設定 ──────────────────────────────────────────────────────────
    llm_provider: Literal["openai", "google", "azure", "ollama"] = Field(
        default="openai", description="LLM 服務提供商"
    )
    llm_fallback: Literal["", "openai", "google", "ollama"] = Field(
        default="ollama", description="主要 LLM 失敗時的備援提供商（空字串表示不啟用）"
    )
    openai_api_key: str = Field(default="", description="OpenAI API 金鑰")
    openai_model: str = Field(default="gpt-4o", description="OpenAI 模型名稱")
    google_api_key: str = Field(default="", description="Google Gemini API 金鑰")
    google_model: str = Field(default="gemini-2.0-flash", description="Google 模型名稱")
    azure_openai_api_key: str = Field(default="", description="Azure OpenAI API 金鑰")
    azure_openai_endpoint: str = Field(default="", description="Azure OpenAI 端點 URL")
    azure_openai_deployment: str = Field(default="", description="Azure OpenAI 部署名稱")
    ollama_model: str = Field(default="llama3.2", description="Ollama 本地模型名稱")

    # LLM 呼叫參數
    llm_timeout_seconds: int = Field(default=300, description="LLM API 呼叫逾時秒數")
    llm_max_retries: int = Field(default=3, description="LLM API 最大重試次數")
    llm_retry_initial_delay: float = Field(default=1.0, description="重試初始延遲秒數")
    llm_retry_backoff_multiplier: float = Field(default=2.0, description="重試退避倍數")
    llm_retry_max_delay: float = Field(default=30.0, description="重試最大延遲秒數")

    # ── Sentence-BERT 語意嵌入設定 ────────────────────────────────────────────
    embedding_model_name: str = Field(
        default="paraphrase-multilingual-MiniLM-L12-v2",
        description="Sentence-BERT 模型名稱",
    )
    embedding_batch_size: int = Field(default=32, description="語意嵌入批次大小")

    # ── API 閘道設定 ──────────────────────────────────────────────────────────
    api_gateway_host: str = Field(default="0.0.0.0", description="API 閘道監聽位址")
    api_gateway_port: int = Field(default=8001, description="API 閘道監聽連接埠")
    api_rate_limit_window_seconds: int = Field(
        default=60, description="速率限制滑動視窗大小（秒）"
    )
    api_rate_limit_default: int = Field(
        default=100, description="預設每視窗最大請求次數"
    )

    # ── 存取管制設定 ──────────────────────────────────────────────────────────
    bulk_export_threshold: int = Field(
        default=100, description="觸發二次驗證的批量匯出閾值"
    )
    totp_issuer: str = Field(default="AI Scam Prediction System", description="TOTP 發行者名稱")

    # ── 排程設定 ──────────────────────────────────────────────────────────────
    prediction_schedule_hours: int = Field(
        default=24, description="預測分析排程間隔（小時）"
    )
    alert_notification_timeout_minutes: int = Field(
        default=5, description="預警通知逾時時間（分鐘）"
    )

    # ── 即時資料擷取設定 ──────────────────────────────────────────────────────
    data_fetch_interval_hours: int = Field(
        default=6, description="資料擷取排程間隔（小時）"
    )
    data_fetch_timeout_seconds: int = Field(
        default=30, description="單一來源 HTTP 請求逾時（秒）"
    )
    data_cache_file_path: str = Field(
        default="data/live_cache.json", description="快取持久化檔案路徑"
    )
    data_source_failure_threshold: int = Field(
        default=3, description="來源連續失敗停用閾值"
    )
    data_source_recovery_hours: int = Field(
        default=1, description="來源停用後自動恢復時間（小時）"
    )


@lru_cache
def get_settings() -> Settings:
    """
    取得系統設定單例

    使用 lru_cache 確保全域只有一個 Settings 實例，
    避免重複讀取環境變數。
    """
    from dotenv import load_dotenv
    load_dotenv(override=True)
    return Settings()
