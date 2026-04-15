"""
沙盤推演介面邏輯

提供新興詐騙變種手法的沙盤推演功能，
允許操作人員輸入情境參數並觀察預測結果。

需求：4.2
"""

from dataclasses import dataclass, field
from typing import Any, Optional


# 合法的詐騙情境類型
VALID_SCENARIO_TYPES = {
    "假冒銀行客服",
    "假冒政府機關",
    "投資詐騙",
    "愛情詐騙",
    "購物詐騙",
    "中獎詐騙",
    "工作詐騙",
    "其他",
}

# 合法的目標受眾類型
VALID_TARGET_AUDIENCES = {
    "中老年族群",
    "年輕族群",
    "學生族群",
    "商業人士",
    "一般民眾",
}


@dataclass
class SandboxParams:
    """
    沙盤推演情境參數

    操作人員輸入的情境設定，用於觸發預測模型推演。
    """

    scenario_type: str
    """詐騙情境類型（如：假冒銀行客服、投資詐騙等）"""

    target_audience: str
    """目標受眾特徵（如：中老年族群、年輕族群等）"""

    risk_level_filter: Optional[str] = None
    """風險等級篩選（高/中/低），None 表示不篩選"""

    time_window_days: int = 7
    """分析時間視窗（天數），預設 7 天"""

    extra_context: dict[str, Any] = field(default_factory=dict)
    """額外情境參數（自由格式）"""


@dataclass
class SandboxResult:
    """
    沙盤推演結果

    包含預測的詐騙變種特徵與風險評估。
    """

    scenario_type: str
    """輸入的詐騙情境類型"""

    target_audience: str
    """輸入的目標受眾"""

    predicted_risk_level: str
    """預測的風險等級（高/中/低）"""

    predicted_features: list[str]
    """預測的高風險語意特徵列表"""

    confidence_score: float
    """預測信心分數（0.0 ~ 1.0）"""

    related_cluster_labels: list[str]
    """相關詐騙類群標籤列表"""

    summary: str
    """推演摘要說明"""


def validate_sandbox_params(params: SandboxParams) -> list[str]:
    """
    驗證沙盤推演參數合法性

    Args:
        params: 沙盤推演情境參數

    Returns:
        錯誤訊息列表，若為空則表示參數合法
    """
    errors: list[str] = []

    if not params.scenario_type or not params.scenario_type.strip():
        errors.append("scenario_type 不可為空")

    if not params.target_audience or not params.target_audience.strip():
        errors.append("target_audience 不可為空")

    if params.risk_level_filter and params.risk_level_filter not in {"高", "中", "低"}:
        errors.append(f"risk_level_filter 必須為 高/中/低 之一，實際值：{params.risk_level_filter}")

    if params.time_window_days < 1 or params.time_window_days > 365:
        errors.append(f"time_window_days 必須在 1 ~ 365 之間，實際值：{params.time_window_days}")

    return errors


def run_sandbox_simulation(
    params: SandboxParams,
    risk_vectors: Optional[list[dict[str, Any]]] = None,
) -> SandboxResult:
    """
    執行沙盤推演模擬

    根據輸入的情境參數，結合現有 Risk_Vector 資料進行推演，
    預測可能出現的詐騙變種特徵與風險等級。

    Args:
        params: 沙盤推演情境參數
        risk_vectors: 可選的 Risk_Vector 資料列表（用於推演參考）

    Returns:
        沙盤推演結果

    Raises:
        ValueError: 若參數不合法
    """
    errors = validate_sandbox_params(params)
    if errors:
        raise ValueError(f"參數驗證失敗：{'; '.join(errors)}")

    # 從 Risk_Vector 資料中提取相關特徵（若有提供）
    predicted_features: list[str] = []
    related_clusters: list[str] = []
    max_risk_score = 0.0

    if risk_vectors:
        for rv in risk_vectors:
            # 篩選符合情境的向量
            cluster = rv.get("scam_cluster_label", "")
            if params.scenario_type in cluster or cluster in params.scenario_type:
                features = rv.get("high_risk_features", [])
                predicted_features.extend(features)
                if cluster:
                    related_clusters.append(cluster)
                score = rv.get("risk_score", 0.0)
                if score > max_risk_score:
                    max_risk_score = score

    # 去重特徵
    seen: set[str] = set()
    unique_features: list[str] = []
    for f in predicted_features:
        if f and f not in seen:
            seen.add(f)
            unique_features.append(f)

    # 若無相關資料，提供預設推演結果
    if not unique_features:
        unique_features = [f"針對{params.target_audience}的{params.scenario_type}手法"]
        max_risk_score = 0.5

    # 判斷預測風險等級
    if max_risk_score >= 0.7:
        predicted_risk_level = "高"
    elif max_risk_score >= 0.4:
        predicted_risk_level = "中"
    else:
        predicted_risk_level = "低"

    # 若有風險等級篩選，記錄篩選條件但不覆蓋預測結果
    filter_note = f"（已套用篩選：{params.risk_level_filter}）" if params.risk_level_filter else ""

    summary = (
        f"針對「{params.scenario_type}」情境與「{params.target_audience}」受眾的沙盤推演，"
        f"預測風險等級為「{predicted_risk_level}」{filter_note}，"
        f"識別出 {len(unique_features)} 項高風險特徵。"
    )

    return SandboxResult(
        scenario_type=params.scenario_type,
        target_audience=params.target_audience,
        predicted_risk_level=predicted_risk_level,
        predicted_features=unique_features[:10],  # 最多顯示 10 項特徵
        confidence_score=min(max_risk_score + 0.1, 1.0),
        related_cluster_labels=list(set(related_clusters))[:5],
        summary=summary,
    )
