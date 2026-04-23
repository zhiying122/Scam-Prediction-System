"""
受害風險地圖頁面邏輯

依年齡層、地區維度呈現受害風險指數，
資料來源為 Prediction_Layer 輸出的 Risk_Vector。

需求：4.3
"""

from dataclasses import dataclass, field
from typing import Any, Optional


# 合法的年齡層分類
VALID_AGE_GROUPS = {
    "18歲以下",
    "18-29歲",
    "30-44歲",
    "45-59歲",
    "60歲以上",
}

# 合法的地區分類（台灣縣市）
VALID_REGIONS = {
    "台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市",
    "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣",
    "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣",
    "台東縣", "澎湖縣", "金門縣", "連江縣",
}


# 描述性受眾標籤 → VALID_AGE_GROUPS 年齡範圍的映射表
AGE_GROUP_MAPPING: dict[str, list[str]] = {
    "中老年族群": ["45-59歲", "60歲以上"],
    "年輕族群": ["18-29歲", "18歲以下"],
    "學生族群": ["18歲以下", "18-29歲"],
    "商業人士": ["30-44歲", "45-59歲"],
    "一般民眾": ["18歲以下", "18-29歲", "30-44歲", "45-59歲", "60歲以上"],
}


def _matches_age_group(target_audience: str, age_group: str) -> bool:
    """
    檢查風險向量的 target_audience 是否與指定的 age_group 匹配。

    使用 AGE_GROUP_MAPPING 將描述性標籤（如「中老年族群」）映射到
    VALID_AGE_GROUPS 的年齡範圍（如「45-59歲」），再檢查是否包含
    指定的 age_group。

    Args:
        target_audience: 風險向量的目標受眾描述
        age_group: 要匹配的年齡層分類

    Returns:
        是否匹配
    """
    if target_audience in AGE_GROUP_MAPPING:
        return age_group in AGE_GROUP_MAPPING[target_audience]
    # 若 target_audience 本身就是 VALID_AGE_GROUPS 中的值，直接比對
    if target_audience in VALID_AGE_GROUPS:
        return target_audience == age_group
    return False


@dataclass
class RiskMapEntry:
    """
    風險地圖單一條目

    代表特定年齡層與地區的風險指數資料。
    """

    age_group: str
    """年齡層分類"""

    region: str
    """地區（縣市）"""

    risk_index: float
    """風險指數（0.0 ~ 1.0）"""

    risk_level: str
    """風險等級（高/中/低）"""

    case_count: int
    """相關案件數量"""

    dominant_scam_type: str
    """主要詐騙類型"""


@dataclass
class RiskMapData:
    """
    風險地圖完整資料

    包含所有年齡層與地區的風險指數矩陣。
    """

    entries: list[RiskMapEntry] = field(default_factory=list)
    """風險地圖條目列表"""

    age_groups: list[str] = field(default_factory=list)
    """所有年齡層列表"""

    regions: list[str] = field(default_factory=list)
    """所有地區列表"""

    overall_risk_level: str = "低"
    """整體風險等級"""

    highest_risk_entry: Optional[RiskMapEntry] = None
    """風險最高的條目"""


def compute_risk_index(risk_vectors: list[dict[str, Any]], age_group: str, region: str) -> float:
    """
    計算特定年齡層與地區的風險指數

    從 Risk_Vector 資料中篩選相關向量，計算加權平均風險分數。

    Args:
        risk_vectors: Risk_Vector 資料列表
        age_group: 年齡層分類
        region: 地區（縣市）

    Returns:
        風險指數（0.0 ~ 1.0）
    """
    if not risk_vectors:
        return 0.0

    relevant_scores: list[float] = []
    for rv in risk_vectors:
        # 檢查向量是否與指定年齡層或地區相關
        target = rv.get("target_audience", "")
        location = rv.get("region", "")
        score = rv.get("risk_score", 0.0)

        # 若向量包含年齡層或地區資訊，則納入計算
        age_match = _matches_age_group(target, age_group) if target else False
        region_match = region in location if location else False
        if age_match or region_match or (not target and not location):
            relevant_scores.append(score)

    if not relevant_scores:
        return 0.0

    return round(sum(relevant_scores) / len(relevant_scores), 4)


def build_risk_map(
    risk_vectors: list[dict[str, Any]],
    age_groups: Optional[list[str]] = None,
    regions: Optional[list[str]] = None,
) -> RiskMapData:
    """
    建立受害風險地圖資料

    依年齡層與地區維度計算風險指數，生成完整的風險地圖資料結構。

    Args:
        risk_vectors: Risk_Vector 資料列表
        age_groups: 要顯示的年齡層列表（預設使用所有合法年齡層）
        regions: 要顯示的地區列表（預設使用所有合法地區）

    Returns:
        風險地圖完整資料
    """
    target_age_groups = age_groups or sorted(VALID_AGE_GROUPS)
    target_regions = regions or sorted(VALID_REGIONS)

    entries: list[RiskMapEntry] = []
    highest_risk_entry: Optional[RiskMapEntry] = None
    max_risk_index = -1.0

    for age_group in target_age_groups:
        for region in target_regions:
            risk_index = compute_risk_index(risk_vectors, age_group, region)

            # 判斷風險等級
            if risk_index >= 0.7:
                risk_level = "高"
            elif risk_index >= 0.4:
                risk_level = "中"
            else:
                risk_level = "低"

            # 統計相關案件數量與主要詐騙類型
            case_count = 0
            scam_type_counts: dict[str, int] = {}
            for rv in risk_vectors:
                target = rv.get("target_audience", "")
                location = rv.get("region", "")
                age_match = _matches_age_group(target, age_group) if target else False
                region_match = region in location if location else False
                if age_match or region_match or (not target and not location):
                    case_count += 1
                    scam_type = rv.get("scam_cluster_label", "未分類")
                    scam_type_counts[scam_type] = scam_type_counts.get(scam_type, 0) + 1

            dominant_scam_type = (
                max(scam_type_counts, key=lambda k: scam_type_counts[k])
                if scam_type_counts
                else "無資料"
            )

            entry = RiskMapEntry(
                age_group=age_group,
                region=region,
                risk_index=risk_index,
                risk_level=risk_level,
                case_count=case_count,
                dominant_scam_type=dominant_scam_type,
            )
            entries.append(entry)

            if risk_index > max_risk_index:
                max_risk_index = risk_index
                highest_risk_entry = entry

    # 計算整體風險等級
    if max_risk_index >= 0.7:
        overall_risk_level = "高"
    elif max_risk_index >= 0.4:
        overall_risk_level = "中"
    else:
        overall_risk_level = "低"

    return RiskMapData(
        entries=entries,
        age_groups=target_age_groups,
        regions=target_regions,
        overall_risk_level=overall_risk_level,
        highest_risk_entry=highest_risk_entry,
    )


def get_risk_map_summary(risk_map: RiskMapData) -> dict[str, Any]:
    """
    取得風險地圖摘要資訊

    Args:
        risk_map: 風險地圖完整資料

    Returns:
        摘要字典，包含各風險等級的條目數量與最高風險資訊
    """
    high_count = sum(1 for e in risk_map.entries if e.risk_level == "高")
    medium_count = sum(1 for e in risk_map.entries if e.risk_level == "中")
    low_count = sum(1 for e in risk_map.entries if e.risk_level == "低")

    summary: dict[str, Any] = {
        "overall_risk_level": risk_map.overall_risk_level,
        "total_entries": len(risk_map.entries),
        "high_risk_count": high_count,
        "medium_risk_count": medium_count,
        "low_risk_count": low_count,
    }

    if risk_map.highest_risk_entry:
        summary["highest_risk"] = {
            "age_group": risk_map.highest_risk_entry.age_group,
            "region": risk_map.highest_risk_entry.region,
            "risk_index": risk_map.highest_risk_entry.risk_index,
            "dominant_scam_type": risk_map.highest_risk_entry.dominant_scam_type,
        }

    return summary
