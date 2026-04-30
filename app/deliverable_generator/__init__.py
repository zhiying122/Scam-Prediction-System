"""
比賽交付物產出模組

根據兩場 AI 競賽的不同評審標準，自動產出六份結構化 Markdown 文件。
使用 DataExtractor → ConsistencyValidator → TemplateRenderer 三層架構，
確保所有交付物的數據一致性與品牌識別統一。

主要類別（將於後續任務實作）：
- ProjectData: 專案資料集合，供所有模板共用
- TeamMember: 團隊成員資訊
- ValidationError / ValidationResult: 驗證結果
- DeliverableOutput: 交付物輸出結果
- VideoScene: 影片腳本分鏡
- PosterSection: 海報版面區塊
- DataExtractor: 資料萃取器
- ConsistencyValidator: 一致性驗證器
- TemplateRenderer: 模板渲染器
- DeliverableGenerator: 交付物產出器（主入口）
"""

__all__ = [
    "ProjectData",
    "TeamMember",
    "ValidationError",
    "ValidationResult",
    "DeliverableOutput",
    "VideoScene",
    "PosterSection",
    "DataExtractor",
    "ConsistencyValidator",
    "TemplateRenderer",
    "DeliverableGenerator",
]


def __getattr__(name: str):
    """延遲匯入：在實際存取類別時才執行匯入，避免佔位模組尚未實作時報錯。"""
    _models = {
        "ProjectData", "TeamMember", "ValidationError",
        "ValidationResult", "DeliverableOutput", "VideoScene",
        "PosterSection",
    }
    _module_map = {
        "DataExtractor": "app.deliverable_generator.extractor",
        "ConsistencyValidator": "app.deliverable_generator.validator",
        "TemplateRenderer": "app.deliverable_generator.renderer",
        "DeliverableGenerator": "app.deliverable_generator.generator",
    }

    if name in _models:
        from app.deliverable_generator import models
        return getattr(models, name)
    if name in _module_map:
        import importlib
        mod = importlib.import_module(_module_map[name])
        return getattr(mod, name)
    raise AttributeError(f"module 'app.deliverable_generator' has no attribute {name!r}")
