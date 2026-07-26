"""
即時詐騙對話模擬器頁面邏輯

讓用戶與 AI 扮演的「詐騙犯」進行真實對話，
系統即時分析每一句話的操控手法，訓練用戶識別詐騙。
"""

from dataclasses import dataclass, field
from typing import Any

# 詐騙情境設定
SIMULATOR_SCENARIOS = {
    "假冒銀行客服": {
        "scammer_persona": "台灣銀行信用卡中心客服專員「林小姐」",
        "opening": "您好，我是台灣銀行信用卡中心，請問是{name}先生/小姐嗎？您的帳戶在今天凌晨有一筆異常交易，需要您配合確認。",
        "goal": "騙取帳號密碼或引導轉帳至「安全帳戶」",
        "difficulty": "中級",
        "system_prompt": """你正在扮演一個詐騙犯，角色是假冒台灣銀行客服的詐騙者。
你的目標是：
1. 建立信任感（聲稱是官方客服）
2. 製造緊迫感（說帳戶有異常）
3. 引導受害者提供帳號密碼或轉帳

規則：
- 用繁體中文對話
- 保持「客服」的專業語氣
- 逐步升級壓力
- 如果用戶質疑，用更多「官方」說法來反駁
- 每次回應不超過 3 句話
- 不要直接說「我是詐騙犯」

記住：這是教育用途的模擬，幫助用戶學習識別詐騙。""",
    },
    "投資詐騙": {
        "scammer_persona": "投資顧問「陳經理」",
        "opening": "您好！我是某某投資顧問公司的陳經理，我們有一個內部消息，想跟您分享一個千載難逢的投資機會。",
        "goal": "誘導受害者投入資金到假投資平台",
        "difficulty": "高級",
        "system_prompt": """你正在扮演一個投資詐騙犯，角色是假冒投資顧問。
你的目標是：
1. 建立專業形象和信任
2. 用高報酬吸引受害者
3. 引導受害者投入資金

規則：
- 用繁體中文對話
- 保持「專業顧問」語氣
- 先給小額「獲利」建立信任
- 逐步要求更大金額投入
- 每次回應不超過 3 句話

記住：這是教育用途的模擬。""",
    },
    "假冒政府機關": {
        "scammer_persona": "刑事局偵查員「王警官」",
        "opening": "您好，我是刑事局偵查員王警官，您的帳戶涉及一起跨國洗錢案件，需要您配合調查。",
        "goal": "以法律威脅迫使受害者轉帳至「監管帳戶」",
        "difficulty": "高級",
        "system_prompt": """你正在扮演一個假冒政府機關的詐騙犯。
你的目標是：
1. 用官方身份製造恐懼
2. 以法律責任威脅受害者
3. 要求轉帳至「監管帳戶」

規則：
- 用繁體中文對話
- 保持「官員」的嚴肅語氣
- 強調保密性（不能告訴家人）
- 每次回應不超過 3 句話

記住：這是教育用途的模擬。""",
    },
}

# 識破詐騙的關鍵提示
SCAM_BUSTING_TIPS = {
    "假冒銀行客服": [
        "真正的銀行不會主動要求你提供密碼或驗證碼",
        "掛斷電話，自己撥打銀行官方客服號碼確認",
        "銀行不會要求你轉帳到「安全帳戶」",
        "遇到緊急情況，先冷靜，詐騙犯最怕你有時間思考",
    ],
    "投資詐騙": [
        "保證獲利是詐騙的最大特徵，合法投資都有風險",
        "不要相信「內部消息」或「VIP群組」",
        "初期小額獲利是誘餌，目的是讓你投入更多",
        "向金管會查詢是否為合法投資機構",
    ],
    "假冒政府機關": [
        "政府機關不會要求你轉帳到「監管帳戶」",
        "真正的調查不會要求你保密，可以告訴家人",
        "掛斷電話，直接撥打 165 反詐騙專線確認",
        "任何要求你匯款的「官員」都是詐騙",
    ],
}


@dataclass
class SimulatorSession:
    """對話模擬器會話狀態"""
    scenario: str
    messages: list[dict[str, str]] = field(default_factory=list)
    turn_count: int = 0
    scam_tactics_detected: list[str] = field(default_factory=list)
    user_resistance_score: int = 0  # 用戶識破詐騙的分數
    is_ended: bool = False
    end_reason: str = ""  # "escaped"（識破）或 "caught"（被騙）

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        if role == "user":
            self.turn_count += 1

    @property
    def scenario_info(self) -> dict[str, Any]:
        return SIMULATOR_SCENARIOS.get(self.scenario, {})


def build_simulator_prompt(scenario: str, conversation_history: list[dict]) -> list[dict]:
    """建立模擬器的 LLM Prompt"""
    scenario_info = SIMULATOR_SCENARIOS.get(scenario, {})
    system_prompt = scenario_info.get("system_prompt", "")

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    return messages


def analyze_user_response(user_text: str, scenario: str) -> dict[str, Any]:
    """
    分析用戶回應，判斷是否識破詐騙

    Returns:
        包含識破程度、觸發的防詐關鍵詞、建議的字典
    """
    from app.pattern_analyzer.xai_highlighter import XAIHighlighter
    from app.pattern_analyzer.psych_classifier import PsychologicalClassifier

    # 防詐關鍵詞（用戶說這些代表在識破詐騙）
    resistance_keywords = [
        "掛斷", "不相信", "詐騙", "假的", "報警", "165",
        "不轉帳", "不提供", "確認", "官方電話", "家人",
        "不對", "懷疑", "奇怪", "不可能", "查證",
        "不會打電話", "銀行不會", "自己打", "官方客服",
    ]

    resistance_score = sum(1 for kw in resistance_keywords if kw in user_text)
    is_resisting = resistance_score >= 1

    tips = SCAM_BUSTING_TIPS.get(scenario, [])

    return {
        "is_resisting": is_resisting,
        "resistance_score": resistance_score,
        "tips": tips[:2] if not is_resisting else [],
        "praise": "很好！你識破了詐騙手法！" if is_resisting else "",
    }
