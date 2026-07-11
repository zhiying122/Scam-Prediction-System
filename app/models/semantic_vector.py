"""SemanticVector 資料模型"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SemanticVector:
    id: str
    script_id: str
    embedding: list
    top_keywords: list
    cluster_label: str
    psychological_tags: list
    created_at: datetime
