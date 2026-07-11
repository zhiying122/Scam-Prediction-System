"""AccessLog 資料模型"""
from dataclasses import dataclass
from datetime import datetime

VALID_ACTIONS = frozenset({"read", "export", "bulk_export", "write", "delete", "generate", "import"})

# audit_log 只允許的操作類型（存取日誌語意）
AUDIT_VALID_ACTIONS = frozenset({"read", "export", "bulk_export"})


@dataclass
class AccessLog:
    id: str
    operator_id: str
    action: str
    resource_id: str
    resource_type: str
    timestamp: datetime
    prev_hash: str
    current_hash: str
