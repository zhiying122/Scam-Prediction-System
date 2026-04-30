"""
核心資料模型

定義交付物產出系統所需的所有資料結構，包含：
- ProjectData：專案資料集合，供所有模板共用
- TeamMember：團隊成員資訊
- ValidationError / ValidationResult：驗證結果
- DeliverableOutput：交付物輸出結果
- VideoScene：影片腳本分鏡
- PosterSection：海報版面區塊
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TeamMember:
    """團隊成員資訊"""

    name: str  # "Member A" / "Member B"
    responsibilities: list[str] = field(default_factory=list)  # 負責範疇列表


@dataclass
class ProjectData:
    """
    專案資料集合

    由 DataExtractor 萃取，供所有模板共用。
    所有交付物引用此單一資料來源，確保數據一致性。
    """

    # 品牌資訊
    project_name: str  # "ScamOracle"
    project_subtitle: str  # "AI 詐騙進化預測系統"

    # 技術數據（需求 7.1 一致性要求）
    test_count: int  # 409
    embedding_dim: int  # 384
    dashboard_page_count: int  # 12
    api_endpoint_count: int  # 7
    module_names: list[str] = field(default_factory=list)  # 10 個核心模組
    tech_stack: dict[str, str] = field(default_factory=dict)  # 技術棧
    docker_services: list[str] = field(default_factory=list)  # ["PostgreSQL", "Redis", "Qdrant"]

    # 台灣詐騙統計數據
    scam_cases_2023: int = 83000  # 83,000
    scam_loss_2023: str = "88.2 億元"
    scam_loss_growth_rate: str = "28%"
    scam_cases_growth_rate: str = "27%"
    avg_loss_investment: str = "85 萬元"
    avg_loss_romance: str = "42 萬元"
    early_warning_hours: int = 24
    detection_accuracy: str = "84.7%"

    # AI 模型資訊（需求 7.5 統一描述）
    llm_models: list[str] = field(
        default_factory=lambda: [
            "Meta Llama 3（透過 Ollama 本地部署）",
            "Google Gemini",
        ]
    )
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # Scam_DNA 心理特徵
    psychological_dimensions: list[str] = field(
        default_factory=lambda: [
            "信任建立",
            "緊迫感製造",
            "情緒勒索",
            "權威偽裝",
            "利益誘導",
        ]
    )

    # 團隊分工（需求 7.6）
    team_members: list[TeamMember] = field(default_factory=list)

    # 測試策略（需求 2.3）
    test_types: dict[str, int] = field(default_factory=dict)  # {"unit": N, "property": N, "integration": N}

    # 系統架構層次
    architecture_layers: list[str] = field(
        default_factory=lambda: ["Input", "Engine", "Analysis", "Output"]
    )


@dataclass
class ValidationError:
    """驗證錯誤"""

    field: str  # 欄位名稱
    expected: str  # 預期值描述
    actual: str  # 實際值
    message: str  # 錯誤訊息


@dataclass
class ValidationResult:
    """驗證結果"""

    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)


@dataclass
class DeliverableOutput:
    """單一交付物輸出結果"""

    competition: str  # "competition_1" | "competition_2"
    deliverable_type: str  # "proposal" | "video_script" | "poster"
    content: str  # 渲染後的 Markdown 內容
    file_path: str  # 輸出檔案路徑
    rendered_at: datetime = field(default_factory=datetime.now)  # 渲染時間
    data_hash: str = ""  # ProjectData 的雜湊值（用於追蹤資料版本）


@dataclass
class VideoScene:
    """影片腳本分鏡"""

    scene_number: int  # 分鏡編號
    time_start: str  # 起始時間碼 "MM:SS"
    time_end: str  # 結束時間碼 "MM:SS"
    visual_description: str  # 畫面描述
    narration: str  # 旁白文字
    subtitle_hint: str = ""  # 字幕提示（比賽一）或技術標註（比賽二）
    section_tag: str = ""  # 段落標記（"應用介紹" | "操作方式" | "預期效果"）


@dataclass
class PosterSection:
    """海報版面區塊"""

    section_name: str  # 區塊名稱
    position: str  # 版面位置（"top" | "middle" | "bottom"）
    area_percentage: float  # 佔海報面積百分比
    content_elements: list[str] = field(default_factory=list)  # 內容元素列表
    visual_type: str = "text"  # 視覺類型（"text" | "chart" | "code" | "image" | "badge"）
