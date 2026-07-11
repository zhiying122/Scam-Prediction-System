"""AlertEvent 資料模型"""
from dataclasses import dataclass
from datetime import datetime

VALID_RISK_LEVELS = frozenset({"高", "中", "低"})


@dataclass
class AlertEvent:
    id: str
    risk_level: str
    trigger_features: list
    risk_vector_id: str
    notified_operators: list
    notified_at: datetime
    created_at: datetime

    def __post_init__(self):
        if self.risk_level not in VALID_RISK_LEVELS:
            raise ValueError(f"risk_level 必須為 {VALID_RISK_LEVELS} 之一")
