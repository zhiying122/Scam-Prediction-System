"""
資料擷取排程器

基於 APScheduler 的排程元件，復用 PredictionScheduler 的設計模式。
預設每 6 小時觸發一次資料擷取，啟動時立即觸發一次。
"""

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.live_data.fetcher import DataFetcher

logger = logging.getLogger(__name__)

_DEFAULT_INTERVAL_HOURS = 6
_MIN_INTERVAL_HOURS = 1
_MAX_INTERVAL_HOURS = 168


class FetchScheduler:
    """
    基於 APScheduler 的資料擷取排程器

    復用 PredictionScheduler 的 BackgroundScheduler + IntervalTrigger 模式。
    預設間隔 6 小時，透過 DATA_FETCH_INTERVAL_HOURS 環境變數設定。
    啟動時立即觸發一次擷取，使用 max_instances=1 防止任務重疊。
    """

    def __init__(
        self,
        fetcher: DataFetcher,
        interval_hours: int = _DEFAULT_INTERVAL_HOURS,
    ) -> None:
        self._fetcher = fetcher
        self._interval_hours = self.validate_interval(interval_hours)
        self._scheduler = BackgroundScheduler()
        self._job = None

    def start(self) -> None:
        """
        啟動排程器

        設定每 interval_hours 小時執行一次擷取任務，
        並立即觸發一次擷取。使用 max_instances=1 防止重疊。
        """
        if self._scheduler.running:
            logger.warning("資料擷取排程器已在執行中，跳過重複啟動")
            return

        self._job = self._scheduler.add_job(
            func=self._run_fetch,
            trigger=IntervalTrigger(hours=self._interval_hours),
            id="live_data_fetch",
            name="即時資料擷取排程任務",
            replace_existing=True,
            max_instances=1,
        )
        self._scheduler.start()
        logger.info(
            "資料擷取排程器已啟動，間隔：%d 小時", self._interval_hours
        )

        # 立即觸發一次擷取
        self.trigger_now()

    def stop(self) -> None:
        """停止排程器"""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("資料擷取排程器已停止")

    def trigger_now(self) -> None:
        """立即手動觸發一次擷取"""
        logger.info("手動觸發資料擷取")
        self._run_fetch()

    def _run_fetch(self) -> None:
        """執行非同步擷取（在同步排程中呼叫）"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 在已有事件迴圈的環境中（如 FastAPI）
                asyncio.ensure_future(self._fetcher.fetch())
            else:
                loop.run_until_complete(self._fetcher.fetch())
        except RuntimeError:
            # 沒有事件迴圈時建立新的
            asyncio.run(self._fetcher.fetch())

    @property
    def is_running(self) -> bool:
        """回傳排程器是否正在執行"""
        return self._scheduler.running

    @staticmethod
    def validate_interval(value: int) -> int:
        """
        驗證排程間隔值

        Args:
            value: 排程間隔（小時）

        Returns:
            有效範圍 1~168 內回傳原值，超出範圍回傳預設值 6
        """
        if _MIN_INTERVAL_HOURS <= value <= _MAX_INTERVAL_HOURS:
            return value
        logger.warning(
            "排程間隔 %d 超出有效範圍 (%d~%d)，使用預設值 %d",
            value,
            _MIN_INTERVAL_HOURS,
            _MAX_INTERVAL_HOURS,
            _DEFAULT_INTERVAL_HOURS,
        )
        return _DEFAULT_INTERVAL_HOURS
