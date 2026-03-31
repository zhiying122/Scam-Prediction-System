"""
預測層排程模組

使用 APScheduler 設定每 24 小時執行一次時間序列分析與異常偵測。
排程器可在測試中透過 mock 替換，避免實際觸發排程。
"""

import logging
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class PredictionScheduler:
    """
    預測分析排程器

    封裝 APScheduler，提供啟動、停止與手動觸發介面。
    預設每 24 小時執行一次分析任務。
    """

    def __init__(self, analysis_func: Callable | None = None, interval_hours: int = 24) -> None:
        """
        初始化排程器

        Args:
            analysis_func: 要排程執行的分析函數，若為 None 則使用預設分析流程
            interval_hours: 排程間隔（小時），預設 24 小時
        """
        self._scheduler = BackgroundScheduler()
        self._interval_hours = interval_hours
        self._analysis_func = analysis_func or self._default_analysis
        self._job = None

    def _default_analysis(self) -> None:
        """預設分析流程（延遲匯入避免循環依賴）"""
        from app.prediction_layer.analyzer import PredictionAnalyzer

        analyzer = PredictionAnalyzer()
        analyzer.run_analysis()

    def start(self) -> None:
        """
        啟動排程器

        設定每 interval_hours 小時執行一次分析任務，
        並立即執行第一次分析。
        """
        if self._scheduler.running:
            logger.warning("排程器已在執行中，跳過重複啟動")
            return

        self._job = self._scheduler.add_job(
            func=self._analysis_func,
            trigger=IntervalTrigger(hours=self._interval_hours),
            id="prediction_analysis",
            name="預測分析排程任務",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info("預測分析排程器已啟動，間隔：%d 小時", self._interval_hours)

    def stop(self) -> None:
        """停止排程器"""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("預測分析排程器已停止")

    def trigger_now(self) -> None:
        """立即手動觸發一次分析（用於測試或手動執行）"""
        logger.info("手動觸發預測分析")
        self._analysis_func()

    @property
    def is_running(self) -> bool:
        """回傳排程器是否正在執行"""
        return self._scheduler.running


# 全域排程器單例（可被測試替換）
_scheduler_instance: PredictionScheduler | None = None


def get_scheduler() -> PredictionScheduler:
    """取得全域排程器單例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = PredictionScheduler()
    return _scheduler_instance
