"""Demo 用假資料，模擬後端 API 回傳"""
import random

HOTWORD_FREQ = {
    "立即": 312, "轉帳": 289, "銀行": 276, "帳戶": 254, "凍結": 231,
    "驗證": 198, "異常": 187, "緊急": 175, "投資": 163, "獲利": 152,
    "警察": 141, "客服": 138, "保證": 127, "免費": 119, "中獎": 108,
    "點擊": 97,  "連結": 89,  "密碼": 82,  "身份": 76,  "詐騙": 71,
}

RISK_VECTORS = [
    {"scam_cluster_label": "假冒銀行客服", "risk_score": 0.91, "high_risk_features": ["緊迫感製造", "權威偽裝"], "target_audience": "中老年族群", "region": "台北市"},
    {"scam_cluster_label": "投資詐騙",     "risk_score": 0.85, "high_risk_features": ["利益誘導", "信任建立"],   "target_audience": "商業人士",   "region": "新北市"},
    {"scam_cluster_label": "假冒政府機關", "risk_score": 0.78, "high_risk_features": ["權威偽裝", "情緒勒索"],   "target_audience": "中老年族群", "region": "台中市"},
    {"scam_cluster_label": "愛情詐騙",     "risk_score": 0.72, "high_risk_features": ["信任建立", "情緒勒索"],   "target_audience": "年輕族群",   "region": "高雄市"},
    {"scam_cluster_label": "購物詐騙",     "risk_score": 0.65, "high_risk_features": ["利益誘導"],               "target_audience": "一般民眾",   "region": "桃園市"},
    {"scam_cluster_label": "中獎詐騙",     "risk_score": 0.58, "high_risk_features": ["利益誘導", "緊迫感製造"], "target_audience": "一般民眾",   "region": "台南市"},
]

SAMPLE_SCRIPTS = [
    "您好，我是中華銀行客服專員，您的帳戶發現異常交易，請立即提供驗證碼，否則帳戶將在24小時內凍結！",
    "恭喜您中獎了！您已獲得100萬元大獎，請立即點擊連結填寫個人資料領取獎金，機會難得，今天截止！",
    "我是刑事局調查員，您的帳戶涉及洗錢案件，請配合調查立即轉帳至安全帳戶，否則您的家人也會受到牽連。",
    "這是一個保證獲利的投資機會，我們的專業團隊有多年經驗，零風險高報酬，每月穩定獲利30%，立即加入！",
    "您好，我是您的老朋友，我現在急需用錢，請馬上轉帳給我，我明天一定還你，拜託了！",
]

TREND_DATA = [
    {"date": "2026-03-01", "count": 45},
    {"date": "2026-03-08", "count": 52},
    {"date": "2026-03-15", "count": 61},
    {"date": "2026-03-22", "count": 78},
    {"date": "2026-03-29", "count": 95},
    {"date": "2026-04-01", "count": 112},
]
