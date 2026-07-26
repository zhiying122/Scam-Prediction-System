"""
詐騙免疫訓練頁面邏輯

提供互動式詐騙識別訓練，用戶閱讀 LLM 生成的詐騙對話後作答，
系統給出 XAI 解析與分數，累積達標後頒發防詐免疫證書。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# 難度設定
DIFFICULTY_LEVELS = {
    "初級 🟢": {
        "description": "明顯的詐騙特徵，適合第一次接觸",
        "min_samples": 3,
        "pass_score": 60,
        "scenario_hint": "包含明顯的緊迫感或利益誘導",
    },
    "中級 🟡": {
        "description": "混合多種手法，需要仔細辨別",
        "min_samples": 5,
        "pass_score": 70,
        "scenario_hint": "混合信任建立與權威偽裝",
    },
    "高級 🔴": {
        "description": "高度擬真，接近真實詐騙話術",
        "min_samples": 5,
        "pass_score": 80,
        "scenario_hint": "高度擬真，不含明顯破綻",
    },
}

# 詐騙類型選項
SCAM_TYPES = [
    "假冒銀行客服",
    "投資詐騙",
    "假冒政府機關",
    "愛情詐騙",
    "購物詐騙",
    "中獎詐騙",
    "工作詐騙",
]

# 心理特徵說明（給用戶看的解說）
TAG_EXPLANATIONS = {
    "信任建立": "詐騙者試圖讓你放下戒心，聲稱是你的朋友、專業人士或可信賴的機構",
    "緊迫感製造": "製造時間壓力，讓你來不及思考就採取行動",
    "情緒勒索": "利用你對家人的擔心或罪惡感來操控你",
    "權威偽裝": "假冒警察、銀行、政府等具有權威的身份",
    "利益誘導": "用高報酬、免費獎品或投資機會吸引你",
}


@dataclass
class TrainingQuestion:
    """單一訓練題目"""
    content: str
    """詐騙話術文本"""
    is_scam: bool
    """是否為詐騙（訓練題目恆為 True）"""
    psychological_tags: list[str]
    """正確答案：包含的心理操控特徵"""
    difficulty: str
    """難度等級"""
    scam_type: str
    """詐騙類型"""


@dataclass
class TrainingSession:
    """訓練會話狀態"""
    difficulty: str
    scam_type: str
    questions: list[TrainingQuestion] = field(default_factory=list)
    current_index: int = 0
    score: int = 0
    total_questions: int = 0
    answers: list[dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed: bool = False

    @property
    def current_question(self) -> TrainingQuestion | None:
        if self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    @property
    def progress_pct(self) -> float:
        if not self.total_questions:
            return 0.0
        return self.current_index / self.total_questions * 100

    @property
    def final_score_pct(self) -> float:
        if not self.total_questions:
            return 0.0
        return self.score / self.total_questions * 100

    @property
    def passed(self) -> bool:
        threshold = DIFFICULTY_LEVELS.get(self.difficulty, {}).get("pass_score", 70)
        return self.final_score_pct >= threshold


def build_training_prompt(scam_type: str, difficulty: str) -> tuple[str, str]:
    """
    建立訓練題目生成的 Prompt

    Returns:
        (scenario, target_audience) 供 generate_scam_samples 使用
    """
    hint = DIFFICULTY_LEVELS.get(difficulty, {}).get("scenario_hint", "")
    scenario = f"{scam_type}詐騙話術，{hint}，用於防詐訓練教材"
    target_audience = "一般民眾（訓練用途，需要讓受訓者能識別詐騙特徵）"
    return scenario, target_audience


def evaluate_answer(
    question: TrainingQuestion,
    user_identified_tags: list[str],
) -> dict[str, Any]:
    """
    評估用戶答案並給分

    Args:
        question: 訓練題目
        user_identified_tags: 用戶選擇的心理特徵標籤

    Returns:
        評估結果字典，包含得分、正確答案、解說
    """
    correct_tags = set(question.psychological_tags)
    user_tags = set(user_identified_tags)

    # 計算命中率
    if not correct_tags:
        tag_score = 100 if not user_tags else 50
    else:
        hits = len(correct_tags & user_tags)
        false_positives = len(user_tags - correct_tags)
        tag_score = max(0, int((hits / len(correct_tags) * 100) - (false_positives * 10)))

    is_correct = tag_score >= 60

    missed_tags = correct_tags - user_tags
    extra_tags = user_tags - correct_tags

    feedback_parts = []
    if hits := len(correct_tags & user_tags):
        feedback_parts.append(f"✅ 正確識別 {hits} 個特徵")
    if missed_tags:
        feedback_parts.append(f"❌ 漏掉：{', '.join(missed_tags)}")
    if extra_tags:
        feedback_parts.append(f"⚠️ 誤判：{', '.join(extra_tags)}")

    return {
        "is_correct": is_correct,
        "tag_score": tag_score,
        "correct_tags": list(correct_tags),
        "user_tags": list(user_tags),
        "missed_tags": list(missed_tags),
        "extra_tags": list(extra_tags),
        "feedback": "、".join(feedback_parts) if feedback_parts else "完美答對！",
        "tag_explanations": {
            tag: TAG_EXPLANATIONS.get(tag, "") for tag in correct_tags
        },
    }


def generate_certificate_html(session: TrainingSession) -> str:
    """
    生成防詐免疫證書 HTML

    Args:
        session: 已完成的訓練會話

    Returns:
        HTML 字串
    """
    score_pct = session.final_score_pct
    level_emoji = {"初級 🟢": "🥉", "中級 🟡": "🥈", "高級 🔴": "🥇"}.get(session.difficulty, "🏅")
    date_str = datetime.now().strftime("%Y 年 %m 月 %d 日")

    return f"""
    <div style="
        border: 3px solid #2c3e50;
        border-radius: 12px;
        padding: 30px;
        text-align: center;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        font-family: 'Microsoft JhengHei', sans-serif;
        max-width: 600px;
        margin: 0 auto;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    ">
        <div style="font-size: 3rem;">{level_emoji}</div>
        <h2 style="color: #2c3e50; margin: 10px 0 5px;">防詐免疫認證證書</h2>
        <p style="color: #4B5563; font-size: 0.9rem;">ScamDNA — AI 詐騙話術進化預警系統</p>
        <hr style="border: 1px solid #bdc3c7; margin: 15px 0;">
        <p style="font-size: 1.1rem; color: #2c3e50;">本證書認證持有人已完成</p>
        <h3 style="color: #e74c3c; margin: 5px 0;">「{session.scam_type}」{session.difficulty}防詐訓練</h3>
        <div style="
            background: #2c3e50;
            color: white;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        ">
            <div style="font-size: 2.5rem; font-weight: bold;">{score_pct:.0f}%</div>
            <div style="font-size: 0.9rem; color: #e5e7eb;">答題正確率</div>
        </div>
        <p style="color: #4B5563; font-size: 0.85rem;">認證日期：{date_str}</p>
        <p style="color: #27ae60; font-weight: bold; font-size: 0.9rem;">
            ✅ 此人具備識別 {session.scam_type} 的基本防詐能力
        </p>
    </div>
    """
