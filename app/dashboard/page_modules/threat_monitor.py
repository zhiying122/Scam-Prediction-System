"""
即時威脅監控儀表板頁面邏輯

模擬 SOC（安全操作中心）風格的即時威脅監控，
顯示當前威脅等級、新興話術偵測、預警事件流。
"""

from datetime import datetime, timedelta
from typing import Any

from data.taiwan_scam_data import (
    SCAM_TYPE_STATS as _STATIC_SCAM_TYPE_STATS,
    MONTHLY_TREND as _STATIC_MONTHLY_TREND,
    TAIWAN_SCAM_CASES_BY_REGION as _STATIC_CASES_BY_REGION,
)


# 威脅等級定義
THREAT_LEVELS = {
    "CRITICAL": {"label": "嚴重", "color": "#ff4757", "icon": "🔴"},
    "HIGH":     {"label": "高",   "color": "#ff6b35", "icon": "🟠"},
    "MEDIUM":   {"label": "中",   "color": "#ffd32a", "icon": "🟡"},
    "LOW":      {"label": "低",   "color": "#0be881", "icon": "🟢"},
}

# 詐騙話術進化時間軸資料（2021-2026）
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
    "假冒政府機關": [
        {
            "year": 2021,
            "keywords": ["檢察官", "監管帳戶", "洗錢防制"],
            "method": "電話假冒檢察官要求轉帳",
            "avg_loss": 280000,
            "cases": 7800,
            "new_tactic": "利用境外電話偽裝來電顯示為政府機關號碼",
        },
        {
            "year": 2022,
            "keywords": ["健保局", "個資外洩", "法院傳票"],
            "method": "假冒健保局 + 法院傳票恐嚇",
            "avg_loss": 300000,
            "cases": 8200,
            "new_tactic": "結合假冒健保局與法院雙重身份施壓",
        },
        {
            "year": 2023,
            "keywords": ["刑事局", "凍結帳戶", "公文傳真"],
            "method": "假公文 + 假刑事局偵查員",
            "avg_loss": 320000,
            "cases": 8765,
            "new_tactic": "傳送偽造公文 PDF 與假偵查員證件照片",
        },
        {
            "year": 2024,
            "keywords": ["數位身分證", "MyData", "政府APP"],
            "method": "假冒政府數位服務 + 釣魚連結",
            "avg_loss": 340000,
            "cases": 8900,
            "new_tactic": "偽裝政府數位服務平台，騙取數位身分驗證資訊",
        },
    ],
    "愛情詐騙": [
        {
            "year": 2021,
            "keywords": ["交友軟體", "海外工作", "匯款"],
            "method": "交友軟體假身份 + 海外急難匯款",
            "avg_loss": 350000,
            "cases": 4800,
            "new_tactic": "大量使用盜用照片建立假交友檔案",
        },
        {
            "year": 2022,
            "keywords": ["視訊交友", "投資邀約", "感情操控"],
            "method": "感情培養 + 投資邀約複合詐騙",
            "avg_loss": 380000,
            "cases": 5500,
            "new_tactic": "結合愛情與投資詐騙，先培養感情再引導投資",
        },
        {
            "year": 2023,
            "keywords": ["AI聊天", "深偽視訊", "跨境匯款"],
            "method": "AI 聊天機器人 + 深偽視訊通話",
            "avg_loss": 420000,
            "cases": 6543,
            "new_tactic": "使用 AI 聊天維持長期互動，深偽視訊增加信任",
        },
        {
            "year": 2024,
            "keywords": ["虛擬伴侶", "語音克隆", "情感AI"],
            "method": "AI 虛擬伴侶 + 語音克隆技術",
            "avg_loss": 460000,
            "cases": 7200,
            "new_tactic": "利用語音克隆與情感 AI 打造高度擬真虛擬伴侶",
        },
    ],
    "購物詐騙": [
        {
            "year": 2021,
            "keywords": ["網拍", "假賣家", "貨到付款"],
            "method": "網拍假賣家 + 貨到付款空包裹",
            "avg_loss": 12000,
            "cases": 20500,
            "new_tactic": "大量建立一頁式購物網站販售假商品",
        },
        {
            "year": 2022,
            "keywords": ["社群團購", "直播帶貨", "退款詐騙"],
            "method": "社群團購詐騙 + 假退款客服",
            "avg_loss": 14000,
            "cases": 19800,
            "new_tactic": "利用社群平台直播帶貨，收款後不出貨",
        },
        {
            "year": 2023,
            "keywords": ["電商平台", "假客服", "重複扣款"],
            "method": "假電商客服 + 重複扣款退款話術",
            "avg_loss": 15000,
            "cases": 18234,
            "new_tactic": "偽裝電商平台客服，以重複扣款為由騙取帳密",
        },
        {
            "year": 2024,
            "keywords": ["AI客服", "假評價", "跨境電商"],
            "method": "AI 假客服 + 跨境電商詐騙",
            "avg_loss": 16000,
            "cases": 17000,
            "new_tactic": "使用 AI 客服機器人自動化詐騙流程，規模化操作",
        },
    ],
    "中獎詐騙": [
        {
            "year": 2021,
            "keywords": ["中獎通知", "手續費", "稅金"],
            "method": "簡訊中獎通知 + 預繳手續費",
            "avg_loss": 40000,
            "cases": 5800,
            "new_tactic": "大量發送假中獎簡訊，要求預繳稅金與手續費",
        },
        {
            "year": 2022,
            "keywords": ["抽獎活動", "社群分享", "釣魚連結"],
            "method": "社群假抽獎活動 + 釣魚網站",
            "avg_loss": 42000,
            "cases": 5200,
            "new_tactic": "在社群平台建立假抽獎活動，騙取個資與金融資訊",
        },
        {
            "year": 2023,
            "keywords": ["電子發票", "載具中獎", "假官網"],
            "method": "假電子發票中獎 + 偽造財政部網站",
            "avg_loss": 45000,
            "cases": 4321,
            "new_tactic": "偽造電子發票中獎通知，建立假財政部兌獎網站",
        },
        {
            "year": 2024,
            "keywords": ["NFT空投", "加密獎勵", "假DApp"],
            "method": "假加密貨幣空投 + 惡意智能合約",
            "avg_loss": 48000,
            "cases": 3800,
            "new_tactic": "利用假 NFT 空投與加密獎勵，誘導連接錢包竊取資產",
        },
    ],
    "工作詐騙": [
        {
            "year": 2021,
            "keywords": ["海外工作", "高薪", "培訓費"],
            "method": "假海外高薪工作 + 預繳培訓費",
            "avg_loss": 75000,
            "cases": 5600,
            "new_tactic": "以東南亞高薪工作為誘餌，收取培訓費與簽證費",
        },
        {
            "year": 2022,
            "keywords": ["柬埔寨", "緬甸", "人口販運"],
            "method": "跨境工作詐騙 + 人口販運",
            "avg_loss": 85000,
            "cases": 6500,
            "new_tactic": "以高薪工作誘騙至東南亞，限制人身自由從事詐騙",
        },
        {
            "year": 2023,
            "keywords": ["居家工作", "刷單", "保證金"],
            "method": "假居家工作 + 刷單詐騙",
            "avg_loss": 95000,
            "cases": 7654,
            "new_tactic": "以居家兼職為名，誘導刷單並要求繳交保證金",
        },
        {
            "year": 2024,
            "keywords": ["AI標註", "遠端工作", "數據標記"],
            "method": "假 AI 數據標註工作 + 預付費用",
            "avg_loss": 105000,
            "cases": 8500,
            "new_tactic": "偽裝 AI 公司招募數據標註員，收取設備費與培訓費",
        },
    ],
}

# 預警事件描述對照表（基於真實詐騙類型）
_TACTIC_DESCRIPTIONS: dict[str, str] = {
    "假冒銀行客服": "偵測到新型 AI 語音詐騙話術",
    "投資詐騙": "新興加密貨幣投資詐騙變種",
    "假冒政府機關": "假冒政府機關簡訊大量發送",
    "愛情詐騙": "愛情詐騙跨境匯款模式出現",
    "購物詐騙": "購物平台假賣家帳號激增",
    "中獎詐騙": "中獎詐騙簡訊與釣魚連結增加",
    "工作詐騙": "工作詐騙招募廣告異常增加",
    "AI 深偽詐騙": "AI 深偽詐騙相關預警",
}


def generate_live_alerts(
    n: int = 8,
    scam_type_stats: dict[str, dict[str, Any]] | None = None,
    cases_by_region: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    """基於真實統計數據生成預警事件，使用當前真實時間。

    使用 scam_type_stats 的案件數計算風險分數，
    使用 cases_by_region 取得真實地區，
    時間戳基於當前系統時間，帶有不規則間隔。

    Args:
        n: 生成的預警事件數量
        scam_type_stats: 詐騙類型統計（預設使用靜態資料）
        cases_by_region: 各縣市案件數（預設使用靜態資料）
    """
    import hashlib

    # 使用傳入的資料或降級至靜態資料
    _scam_stats = scam_type_stats if scam_type_stats is not None else _STATIC_SCAM_TYPE_STATS
    _regions = cases_by_region if cases_by_region is not None else _STATIC_CASES_BY_REGION

    # 按案件數降序排列詐騙類型（確定性排序）
    sorted_types = sorted(
        _scam_stats.items(), key=lambda x: x[1]["cases"], reverse=True
    )
    max_cases = max(s["cases"] for s in _scam_stats.values())

    # 按案件數降序排列地區
    sorted_regions = sorted(
        _regions.items(), key=lambda x: x[1], reverse=True
    )

    now = datetime.now()
    alerts: list[dict[str, Any]] = []
    num_types = len(sorted_types)
    num_regions = len(sorted_regions)

    for i in range(n):
        scam_name, stats = sorted_types[i % num_types]
        region_name, _ = sorted_regions[i % num_regions]

        # 風險分數：案件數 / 最大案件數
        risk_score = round(stats["cases"] / max_cases, 3)
        level = (
            "CRITICAL" if risk_score > 0.85
            else "HIGH" if risk_score > 0.7
            else "MEDIUM"
        )

        # 用 hash 產生不規則但確定性的時間偏移（避免整點）
        seed = hashlib.md5(f"{scam_name}-{i}-{now.strftime('%Y%m%d%H')}".encode()).hexdigest()
        base_minutes = (i + 1) * 12 + int(seed[:2], 16) % 9  # 不規則間隔
        extra_seconds = int(seed[2:4], 16) % 60  # 不規則秒數
        alert_time = now - timedelta(minutes=base_minutes, seconds=extra_seconds)

        # 動態 alert ID：基於當前日期
        alert_id = f"ALT-{now.strftime('%Y%m%d')}{i:02d}"

        tactic = _TACTIC_DESCRIPTIONS.get(scam_name, f"{scam_name}相關預警")

        alerts.append({
            "id": alert_id,
            "time": alert_time.strftime("%H:%M:%S"),
            "scam_type": scam_name,
            "region": region_name,
            "tactic": tactic,
            "risk_score": risk_score,
            "level": level,
            "cases_detected": stats["cases"] // 365,
        })

    return sorted(alerts, key=lambda a: a["time"], reverse=True)


def get_current_threat_summary(
    scam_type_stats: dict[str, dict[str, Any]] | None = None,
    monthly_trend: list[dict[str, Any]] | None = None,
    cases_by_region: dict[str, int] | None = None,
) -> dict[str, Any]:
    """基於真實統計數據動態計算當前威脅摘要。

    Args:
        scam_type_stats: 詐騙類型統計（預設使用靜態資料）
        monthly_trend: 月度趨勢資料（預設使用靜態資料）
        cases_by_region: 各縣市案件數（預設使用靜態資料）

    Returns:
        dict 包含：
        - active_threats: 趨勢為「上升」的詐騙類型數量
        - new_variants_24h: 基於最新月份案件數 / 30 的日均新變種估算
        - total_cases_today: 最新月份案件數 / 30（日均）
        - ai_scam_ratio: 趨勢上升類型案件數佔總案件數比例
        - highest_risk_type: 案件數最多的詐騙類型
        - highest_risk_region: 案件數最多的地區
    """
    # 使用傳入的資料或降級至靜態資料
    _scam_stats = scam_type_stats if scam_type_stats is not None else _STATIC_SCAM_TYPE_STATS
    _trend = monthly_trend if monthly_trend is not None else _STATIC_MONTHLY_TREND
    _regions = cases_by_region if cases_by_region is not None else _STATIC_CASES_BY_REGION

    # 計算趨勢上升的類型數量
    rising_types = {
        name: stats
        for name, stats in _scam_stats.items()
        if stats["trend"] == "上升"
    }
    active_threats = len(rising_types)

    # 最新月份的日均案件數
    latest_month = _trend[-1]
    total_cases_today = latest_month["cases"] // 30

    # 新變種估算：上升趨勢類型的日均案件數
    rising_daily = sum(s["cases"] for s in rising_types.values()) // 365
    new_variants_24h = rising_daily

    # AI 詐騙比例：上升趨勢類型案件數 / 總案件數
    total_cases_all = sum(s["cases"] for s in _scam_stats.values())
    rising_cases = sum(s["cases"] for s in rising_types.values())
    ai_scam_ratio = round(rising_cases / total_cases_all, 2) if total_cases_all else 0.0

    # 最高風險類型：案件數最多
    highest_risk_type = max(_scam_stats, key=lambda k: _scam_stats[k]["cases"])

    # 最高風險地區：案件數最多
    highest_risk_region = max(
        _regions, key=_regions.get  # type: ignore[arg-type]
    )

    # 整體威脅等級
    overall_level = "HIGH" if active_threats >= 3 else "MEDIUM" if active_threats >= 1 else "LOW"

    # 趨勢判斷
    if len(_trend) >= 2:
        trend = "上升" if _trend[-1]["cases"] > _trend[-2]["cases"] else "穩定"
    else:
        trend = "穩定"

    return {
        "overall_level": overall_level,
        "active_threats": active_threats,
        "new_variants_24h": new_variants_24h,
        "total_cases_today": total_cases_today,
        "highest_risk_type": highest_risk_type,
        "highest_risk_region": highest_risk_region,
        "ai_scam_ratio": ai_scam_ratio,
        "trend": trend,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
