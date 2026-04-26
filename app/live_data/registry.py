"""
資料來源註冊表

管理所有外部資料來源端點，支援優先順序排序、
連續失敗自動停用與自動恢復機制。
包含爬蟲型資料來源（scraper）作為最高優先來源。
"""

import logging
from datetime import datetime, timedelta, timezone

from app.live_data.models import DataSourceConfig

logger = logging.getLogger(__name__)

# 預設資料來源
# priority=0 的 scraper 來源會最先嘗試，使用網頁爬蟲 + LLM 解析
# 後續 HTTP API 來源作為備援（雖然目前這些 API 端點不存在，
# 但保留以便未來政府開放 API 時可直接啟用）
_DEFAULT_SOURCES = [
    DataSourceConfig(
        name="scraper:台灣詐騙統計",
        url="scraper://all",
        data_format="scraper",
        priority=0,
        enabled=True,
    ),
    DataSourceConfig(
        name="data.gov.tw",
        url="https://data.gov.tw/datasets/search?qs=詐騙統計",
        data_format="json",
        priority=1,
        enabled=True,
    ),
    DataSourceConfig(
        name="NPA 開放資料",
        url="https://165.npa.gov.tw",
        data_format="json",
        priority=2,
        enabled=True,
    ),
]


class DataSourceRegistry:
    """
    管理所有外部資料來源端點

    支援：
    - 依優先順序排序回傳啟用來源
    - 連續失敗自動停用（預設 3 次）
    - 停用後自動恢復（預設 1 小時）
    """

    def __init__(
        self,
        sources: list[DataSourceConfig] | None = None,
        failure_threshold: int = 3,
        recovery_hours: int = 1,
    ) -> None:
        self._sources = list(sources) if sources is not None else list(_DEFAULT_SOURCES)
        self._failure_threshold = failure_threshold
        self._recovery_hours = recovery_hours
        # 追蹤每個來源的連續失敗次數與停用時間
        self._consecutive_failures: dict[str, int] = {}
        self._disabled_until: dict[str, datetime] = {}

    def get_active_sources(self) -> list[DataSourceConfig]:
        """回傳啟用中的來源，依 priority 由小到大排序"""
        self._check_auto_recovery()
        active = [s for s in self._sources if s.enabled]
        return sorted(active, key=lambda s: s.priority)

    def record_failure(self, source_name: str) -> None:
        """記錄來源失敗，累計達閾值後自動停用"""
        self._consecutive_failures[source_name] = (
            self._consecutive_failures.get(source_name, 0) + 1
        )
        failures = self._consecutive_failures[source_name]
        logger.warning(
            "來源 '%s' 擷取失敗（連續第 %d 次）", source_name, failures
        )

        if failures >= self._failure_threshold:
            for src in self._sources:
                if src.name == source_name:
                    src.enabled = False
                    self._disabled_until[source_name] = datetime.now(
                        timezone.utc
                    ) + timedelta(hours=self._recovery_hours)
                    logger.error(
                        "來源 '%s' 連續失敗 %d 次，已暫時停用至 %s",
                        source_name,
                        failures,
                        self._disabled_until[source_name].isoformat(),
                    )
                    break

    def record_success(self, source_name: str) -> None:
        """記錄來源成功，重置失敗計數並恢復啟用"""
        self._consecutive_failures[source_name] = 0
        self._disabled_until.pop(source_name, None)
        for src in self._sources:
            if src.name == source_name:
                src.enabled = True
                break

    def _check_auto_recovery(self) -> None:
        """檢查並恢復已到期的停用來源"""
        now = datetime.now(timezone.utc)
        recovered = []
        for name, until in list(self._disabled_until.items()):
            if now >= until:
                for src in self._sources:
                    if src.name == name:
                        src.enabled = True
                        self._consecutive_failures[name] = 0
                        recovered.append(name)
                        logger.info("來源 '%s' 停用期已到，自動恢復啟用", name)
                        break
        for name in recovered:
            self._disabled_until.pop(name, None)
