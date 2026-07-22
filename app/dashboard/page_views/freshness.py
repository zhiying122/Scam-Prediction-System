"""
資料新鮮度指示器

根據 FreshnessInfo 渲染四種顯示狀態：
- 綠色：最新資料（排程間隔內）
- 黃色：快取資料（超過排程間隔但 <24h）
- 紅色：過時資料（≥24h）
- 灰色：靜態預設資料
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.live_data.models import FreshnessInfo

_LOCAL_TZ = ZoneInfo("Asia/Taipei")


def _format_local_time(dt: datetime) -> str:
    """將 UTC 時間戳轉為台灣本地時間顯示"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_LOCAL_TZ).strftime("%Y-%m-%d %H:%M")


def render_freshness_indicator(info: FreshnessInfo) -> str:
    """
    產生新鮮度指示器文字

    Args:
        info: 資料新鮮度資訊

    Returns:
        包含 emoji 與格式化時間的指示器字串
    """
    if info.is_fresh and info.fetched_at is not None:
        time_str = _format_local_time(info.fetched_at)
        return f"✅ 資料已更新：{time_str}（來源：{info.source_name}）"

    if info.is_cached and info.fetched_at is not None:
        time_str = _format_local_time(info.fetched_at)
        if info.cache_age_hours < 24:
            hours = int(info.cache_age_hours)
            return f"⚠️ 快取資料：{time_str}（{hours} 小時前更新）"
        else:
            days = int(info.cache_age_hours / 24)
            return f"🔴 資料可能過時：{time_str}（{days} 天前更新）"

    if info.is_static:
        return "📋 顯示靜態預設資料（2023-2024）"

    # Fallback: no data
    return "📋 顯示靜態預設資料（2023-2024）"
