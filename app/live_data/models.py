"""
即時資料自動更新 - 資料模型

定義所有 Pydantic 資料模型，包含：
- ScamTypeStat、MonthlyTrendEntry、AnnualStat：基礎統計模型
- NormalizedData：正規化後的統一資料格式（含 model_validator）
- FetchResult：單次擷取結果
- DataSourceConfig：資料來源設定
- CachedData：快取資料包裝
- FreshnessInfo：資料新鮮度資訊
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ScamTypeStat(BaseModel):
    """詐騙類型統計"""

    cases: int = Field(ge=0)
    avg_loss_ntd: int = Field(ge=0)
    trend: str  # "上升" | "下降" | "穩定"


class MonthlyTrendEntry(BaseModel):
    """月度趨勢條目"""

    month: str  # "YYYY-MM" 格式
    cases: int = Field(ge=0)
    amount_billion: float = Field(ge=0)


class AnnualStat(BaseModel):
    """年度統計"""

    total_cases: int = Field(ge=0)
    total_loss_billion: float = Field(ge=0)


class NormalizedData(BaseModel):
    """正規化後的統一詐騙統計資料"""

    scam_cases_by_region: dict[str, int]
    scam_type_stats: dict[str, ScamTypeStat]
    monthly_trend: list[MonthlyTrendEntry]
    victim_age_distribution: dict[str, float]
    annual_stats: dict[str, AnnualStat]
    source_name: str
    fetched_at: datetime
    hotwords: dict[str, int] = Field(default_factory=dict)
    real_scam_scripts: list[dict] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_non_negative_regions(self) -> "NormalizedData":
        for region, count in self.scam_cases_by_region.items():
            if count < 0:
                raise ValueError(f"縣市 {region} 案件數不可為負數: {count}")
        return self

    @model_validator(mode="after")
    def validate_age_distribution_sum(self) -> "NormalizedData":
        if self.victim_age_distribution:
            total = sum(self.victim_age_distribution.values())
            if not (0.99 <= total <= 1.01):
                raise ValueError(
                    f"年齡層比例總和 {total} 不在 0.99~1.01 範圍內"
                )
        return self


class FetchResult(BaseModel):
    """單次資料擷取結果"""

    source_name: str
    fetched_at: datetime
    success: bool
    http_status: int | None = None
    error_message: str | None = None
    record_count: int | None = None


class DataSourceConfig(BaseModel):
    """資料來源設定"""

    name: str
    url: str
    data_format: Literal["json", "csv", "scraper"]
    priority: int = Field(ge=0)
    enabled: bool = True


class CachedData(BaseModel):
    """快取資料包裝"""

    data: NormalizedData
    cached_at: datetime
    source_name: str
    is_fallback: bool = False


class FreshnessInfo(BaseModel):
    """資料新鮮度資訊"""

    source_name: str
    fetched_at: datetime | None = None
    is_fresh: bool = False
    is_cached: bool = False
    is_static: bool = False
    cache_age_hours: float = 0.0
