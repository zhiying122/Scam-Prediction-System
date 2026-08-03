"""ScamScript 資料模型"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScamScript:
    id: str
    task_id: str
    content: str
    scenario: str
    target_audience: str
    psychological_tags: list
    language: str
    is_regulated: bool
    created_at: datetime
    created_by: str

    def __post_init__(self):
        if not self.is_regulated:
            raise ValueError("is_regulated 必須恆為 True（需求 1.5）")
