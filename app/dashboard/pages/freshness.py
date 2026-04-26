"""
資料新鮮度指示器

根據 FreshnessInfo 渲染四種顯示狀態：
- 綠色：最新資料
- 黃色：快取資料（<24h）
- 紅色：過時資料（≥24h）
- 灰色：靜態預設資料
"""

from app.live_data.models import FreshnessInfo


def render_freshness_indicator(info: FreshnessInfo) -> str:
    """
    產生新鮮度指示器文字

    Args:
        info: 資料新鮮度資訊

    Returns:
        包含 emoji 與格式化時間的指示器字串
    """
    if info.is_fresh and info.fetched_at is not None:
        time_str = info.fetched_at.strftime("%Y-%m-%d %H:%M")
        return f"✅ 資料已更新：{time_str}（來源：{info.source_name}）"

    if info.is_cached and info.fetched_at is not None:
        time_str = info.fetched_at.strftime("%Y-%m-%d %H:%M")
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
