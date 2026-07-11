"""RiskVector 資料模型"""
from dataclasses import dataclass
from datetime import datetime

VALID_RISK_LEVELS = frozenset({"高", "中", "低"})


@dataclass
class RiskVector:
    id: str
    high_risk_features: list
    scam_cluster_label: str
    risk_score: float
    risk_level: str
    time_range_start: datetime
    time_range_end: datetime
    version: str
    created_at: datetime

    def __post_init__(self):
        if not (0.0 <= self.risk_score <= 1.0):
            raise ValueError("risk_score 必須在 [0.0, 1.0] 範圍內")
        if self.risk_level not in VALID_RISK_LEVELS:
            raise ValueError(f"risk_level 必須為 {VALID_RISK_LEVELS} 之一")
