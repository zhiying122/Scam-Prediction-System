"""
沙盤推演頁面邏輯 — page_views 層

Re-export 自 page_modules.sandbox，統一 import 路徑。
streamlit_app/pages/3_沙盤推演.py 從 app.dashboard.page_views.sandbox 引入。

需求：4.2
"""

from app.dashboard.page_modules.sandbox import (  # noqa: F401
    VALID_SCENARIO_TYPES,
    VALID_TARGET_AUDIENCES,
    SandboxParams,
    SandboxResult,
    run_sandbox_simulation,
    validate_sandbox_params,
)

__all__ = [
    "VALID_SCENARIO_TYPES",
    "VALID_TARGET_AUDIENCES",
    "SandboxParams",
    "SandboxResult",
    "run_sandbox_simulation",
    "validate_sandbox_params",
]
