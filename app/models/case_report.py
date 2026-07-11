"""CaseReport 資料模型"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CaseReport:
    id: str
    source: str
    scam_type: str
    description: str
    reported_at: datetime
    import_batch_id: str
    pii_removed: bool
