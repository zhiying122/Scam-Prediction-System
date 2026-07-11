"""ModelVersion 資料模型"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ModelVersion:
    id: str
    version: str
    accuracy_before: float
    accuracy_after: float
    training_data_count: int
    new_cluster_count: int
    created_at: datetime
    created_by: str
    is_active: bool

    def __post_init__(self):
        if not (0.0 <= self.accuracy_before <= 1.0):
            raise ValueError("accuracy_before 必須在 [0.0, 1.0] 範圍內")
        if not (0.0 <= self.accuracy_after <= 1.0):
            raise ValueError("accuracy_after 必須在 [0.0, 1.0] 範圍內")
