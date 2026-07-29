"""
資料新鮮度指示器

根據 FreshnessInfo 渲染四種顯示狀態：
- 綠色：最新資料（排程間隔內）
- 黃色：快取資料（超過排程間隔但 <24h）
- 紅色：過時資料（≥24h）
- 灰色：靜態預設資料

頂欄不顯示時間戳與裝飾符號，避免視覺雜訊。
"""

from app.live_data.models import FreshnessInfo


def render_freshness_indicator(info: FreshnessInfo) -> str:
    """
    產生新鮮度指示器文字（無時間戳、無 emoji）。

    Args:
        info: 資料新鮮度資訊

    Returns:
        簡潔狀態字串
    """
    if info.is_fresh and info.fetched_at is not None:
        return f"資料已更新（來源：{info.source_name}）"

    if info.is_cached and info.fetched_at is not None:
        if info.cache_age_hours < 24:
            hours = int(info.cache_age_hours)
            return f"快取資料（{hours} 小時前更新）"
        days = int(info.cache_age_hours / 24)
        return f"資料可能過時（{days} 天前更新）"

    if info.is_static:
        return "顯示靜態預設資料（2023-2024）"

    return "顯示靜態預設資料（2023-2024）"
