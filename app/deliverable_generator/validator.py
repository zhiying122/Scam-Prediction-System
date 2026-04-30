"""
ConsistencyValidator — 一致性驗證器

驗證 ProjectData 中的技術數據一致性，確保所有交付物引用相同的數據。
包含禁止使用中國大陸 AI 工具的檢查規則。
"""

from __future__ import annotations

from app.deliverable_generator.models import ProjectData, ValidationError, ValidationResult


class ConsistencyValidator:
    """交付物資料一致性驗證器"""

    # 禁止使用的 AI 工具名稱（小寫比對）
    BANNED_AI_TOOLS: frozenset[str] = frozenset({
        "deepseek",
        "baidu",
        "ernie",
        "qwen",
        "tongyi",
        "chatglm",
        "zhipu",
        "minimax",
        "baichuan",
    })

    def validate(self, data: ProjectData) -> ValidationResult:
        """
        驗證專案資料一致性

        Args:
            data: 專案資料

        Returns:
            驗證結果，包含是否通過與錯誤列表
        """
        errors: list[ValidationError] = []

        # 測試數量必須為正整數
        if data.test_count <= 0:
            errors.append(ValidationError(
                field="test_count",
                expected="> 0",
                actual=str(data.test_count),
                message="測試數量必須為正整數",
            ))

        # 向量維度必須為 384
        if data.embedding_dim != 384:
            errors.append(ValidationError(
                field="embedding_dim",
                expected="384",
                actual=str(data.embedding_dim),
                message="向量維度必須為 384",
            ))

        # Dashboard 頁面數量必須為 12
        if data.dashboard_page_count != 12:
            errors.append(ValidationError(
                field="dashboard_page_count",
                expected="12",
                actual=str(data.dashboard_page_count),
                message="Dashboard 頁面數量必須為 12",
            ))

        # API 端點數量必須為 7
        if data.api_endpoint_count != 7:
            errors.append(ValidationError(
                field="api_endpoint_count",
                expected="7",
                actual=str(data.api_endpoint_count),
                message="API 端點數量必須為 7",
            ))

        # 核心模組數量必須為 10
        if len(data.module_names) != 10:
            errors.append(ValidationError(
                field="module_names",
                expected="10",
                actual=str(len(data.module_names)),
                message="核心模組數量必須為 10",
            ))

        # 專案名稱必須為 ScamOracle
        if data.project_name != "ScamOracle":
            errors.append(ValidationError(
                field="project_name",
                expected="ScamOracle",
                actual=data.project_name,
                message="專案名稱必須為 ScamOracle",
            ))

        # 團隊成員必須為 2 人
        if len(data.team_members) != 2:
            errors.append(ValidationError(
                field="team_members",
                expected="2",
                actual=str(len(data.team_members)),
                message="團隊成員必須為 2 人",
            ))

        # 心理特徵維度必須為 5
        if len(data.psychological_dimensions) != 5:
            errors.append(ValidationError(
                field="psychological_dimensions",
                expected="5",
                actual=str(len(data.psychological_dimensions)),
                message="心理特徵維度必須為 5",
            ))

        # 檢查禁止的 AI 工具
        errors.extend(self._check_banned_ai_tools(data.llm_models))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
        )

    def _check_banned_ai_tools(self, models: list[str]) -> list[ValidationError]:
        """
        檢查 AI 模型列表是否包含禁止的工具

        Args:
            models: AI 模型名稱列表

        Returns:
            包含禁止工具的驗證錯誤列表
        """
        errors: list[ValidationError] = []
        for model in models:
            model_lower = model.lower()
            for banned in self.BANNED_AI_TOOLS:
                if banned in model_lower:
                    errors.append(ValidationError(
                        field="llm_models",
                        expected="不含中國大陸 AI 工具",
                        actual=model,
                        message=f"AI 模型列表不得包含 {banned}（發現於 '{model}'）",
                    ))
        return errors
