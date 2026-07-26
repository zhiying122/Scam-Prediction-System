"""對話模擬器頁面邏輯單元測試。"""

from app.dashboard.page_modules.scam_simulator import (
    SimulatorSession,
    analyze_user_response,
    build_simulator_prompt,
)


def test_add_message_increments_turn_only_for_user():
    sim = SimulatorSession(scenario="假冒銀行客服")
    sim.add_message("assistant", "開場")
    assert sim.turn_count == 0
    sim.add_message("user", "銀行不會打電話給我")
    assert sim.turn_count == 1
    assert len(sim.messages) == 2


def test_analyze_user_response_detects_bank_wont_call():
    result = analyze_user_response("銀行不會打電話給我", "假冒銀行客服")
    assert result["is_resisting"] is True
    assert result["resistance_score"] >= 1


def test_build_simulator_prompt_includes_system_and_history():
    history = [
        {"role": "assistant", "content": "您好"},
        {"role": "user", "content": "你是誰"},
    ]
    messages = build_simulator_prompt("假冒銀行客服", history)
    assert messages[0]["role"] == "system"
    assert messages[1:] == history
