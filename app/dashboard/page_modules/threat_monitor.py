"""
即時威脅監控儀表板頁面邏輯

模擬 SOC（安全操作中心）風格的即時威脅監控，
顯示當前威脅等級、新興話術偵測、預警事件流。
"""

import random
from datetime import datetime, timedelta
from typing import Any


# 威脅等級定義
THREAT_LEVELS = {
    "CRITICAL": {"label": "嚴重", "color": "#ff4757", "icon": "🔴"},
    "HIGH":     {"label": "高",   "color": "#ff6b35", "icon": "🟠"},
    "MEDIUM":   {"label": "中",   "color": "#ffd32a", "icon": "🟡"},
    "LOW":      {"label": "低",   "color": "#0be881", "icon": "🟢"},
}

# 詐騙話術進化時間軸資料（2021-2024）
EVOLUTION_TIMELINE: dict[str, list[dict[str, Any]]] = {
    "假冒銀行客服": [
        {
            "year": 2021,
            "keywords": ["帳戶異常", "電話客服", "身分驗證"],
            "method": "電話語音詐騙",
            "avg_loss": 120000,
            "cases": 8500,
            "new_tactic": "首次大規模使用語音合成技術",
        },
        {
            "year": 2022,
            "keywords": ["簡訊連結", "釣魚網站", "OTP驗證碼"],
            "method": "簡訊釣魚 + 假網站",
            "avg_loss": 145000,
            "cases": 11200,
            "new_tactic": "結合假冒銀行官網，竊取網銀帳密",
        },
        {
            "year": 2023,
            "keywords": ["LINE客服", "安全帳戶", "凍結帳戶"],
            "method": "LINE 假客服 + 安全帳戶話術",
            "avg_loss": 168000,
            "cases": 14800,
            "new_tactic": "轉移至 LINE 平台，偽裝官方帳號",
        },
        {
            "year": 2024,
            "keywords": ["AI語音", "深偽技術", "視訊驗證"],
            "method": "AI 深偽語音 + 視訊詐騙",
            "avg_loss": 195000,
            "cases": 16500,
            "new_tactic": "使用 AI 複製銀行客服聲音，視訊中偽裝真人",
        },
    ],
    "投資詐騙": [
        {
            "year": 2021,
            "keywords": ["股票明牌", "投資群組", "老師帶單"],
            "method": "LINE 投資群組 + 假老師",
            "avg_loss": 450000,
            "cases": 7200,
            "new_tactic": "大量建立假投資社群，製造獲利假象",
        },
        {
            "year": 2022,
            "keywords": ["虛擬貨幣", "比特幣", "NFT"],
            "method": "加密貨幣投資詐騙",
            "avg_loss": 620000,
            "cases": 9800,
            "new_tactic": "利用加密貨幣熱潮，建立假交易平台",
        },
        {
            "year": 2023,
            "keywords": ["AI投資", "量化交易", "機器人交易"],
            "method": "假 AI 量化交易平台",
            "avg_loss": 780000,
            "cases": 11500,
            "new_tactic": "偽裝 AI 自動交易系統，初期給予真實獲利",
        },
        {
            "year": 2024,
            "keywords": ["ChatGPT投資", "AI預測", "大數據選股"],
            "method": "假 AI 投資顧問 + 深偽名人背書",
            "avg_loss": 920000,
            "cases": 13200,
            "new_tactic": "使用深偽技術偽造名人推薦影片，結合 AI 話術",
        },
    ],
}

# 即時預警事件（模擬串流資料）
def generate_live_alerts(n: int = 8) -> list[dict[str, Any]]:
    """生成模擬的即時預警事件串流"""
    scam_types = ["假冒銀行客服", "投資詐騙", "假冒政府機關", "愛情詐騙", "工作詐騙"]
    regions = ["台北市", "新北市", "台中市", "高雄市", "桃園市", "台南市"]
    tactics = [
        "偵測到新型 AI 語音詐騙話術",
        "發現假冒官方 LINE 帳號群組",
        "新興加密貨幣投資詐騙變種",
        "深偽技術視訊詐騙案例上升",
        "假冒政府機關簡訊大量發送",
        "工作詐騙招募廣告異常增加",
        "愛情詐騙跨境匯款模式出現",
        "購物平台假賣家帳號激增",
    ]

    alerts = []
    now = datetime.now()
    for i in range(n):
        minutes_ago = random.randint(1, 120)
        risk_score = random.uniform(0.5, 0.98)
        level = "CRITICAL" if risk_score > 0.85 else "HIGH" if risk_score > 0.7 else "MEDIUM"
        alerts.append({
            "id": f"ALT-{2024100 + i}",
            "time": (now - timedelta(minutes=minutes_ago)).strftime("%H:%M:%S"),
            "scam_type": random.choice(scam_types),
            "region": random.choice(regions),
            "tactic": random.choice(tactics),
            "risk_score": round(risk_score, 3),
            "level": level,
            "cases_detected": random.randint(3, 50),
        })

    return sorted(alerts, key=lambda a: a["time"], reverse=True)


def get_current_threat_summary() -> dict[str, Any]:
    """取得當前威脅摘要統計"""
    return {
        "overall_level": "HIGH",
        "active_threats": 23,
        "new_variants_24h": 7,
        "total_cases_today": 284,
        "highest_risk_type": "投資詐騙",
        "highest_risk_region": "新北市",
        "ai_scam_ratio": 0.34,  # 34% 的詐騙使用 AI 技術
        "trend": "上升",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
