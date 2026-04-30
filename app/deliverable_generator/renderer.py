"""
TemplateRenderer — 模板渲染器

使用 Jinja2 模板引擎，將 ProjectData 渲染為六份 Markdown 交付物文件。
比賽一模板聚焦使用者情境與產品展示，比賽二模板聚焦系統架構與技術深度。
"""

from __future__ import annotations

from typing import Literal

import jinja2

from app.deliverable_generator.models import ProjectData


# 模板檔案名稱對應表
_TEMPLATE_MAP: dict[tuple[str, str], str] = {
    ("competition_1", "proposal"): "comp1_proposal.md.j2",
    ("competition_1", "video_script"): "comp1_video_script.md.j2",
    ("competition_1", "poster"): "comp1_poster.md.j2",
    ("competition_2", "proposal"): "comp2_proposal.md.j2",
    ("competition_2", "video_script"): "comp2_video_script.md.j2",
    ("competition_2", "poster"): "comp2_poster.md.j2",
}

# 輸出檔案名稱對應表
_OUTPUT_NAME_MAP: dict[tuple[str, str], str] = {
    ("competition_1", "proposal"): "competition1_proposal.md",
    ("competition_1", "video_script"): "competition1_video_script.md",
    ("competition_1", "poster"): "competition1_poster.md",
    ("competition_2", "proposal"): "competition2_proposal.md",
    ("competition_2", "video_script"): "competition2_video_script.md",
    ("competition_2", "poster"): "competition2_poster.md",
}


class TemplateRenderer:
    """Jinja2 模板渲染器"""

    def __init__(self, template_dir: str = "templates/competition") -> None:
        """
        初始化模板渲染器。

        Args:
            template_dir: 模板目錄路徑，預設為 templates/competition/
        """
        self._template_dir = template_dir
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=False,
            keep_trailing_newline=True,
        )

    def render(
        self,
        competition: Literal["competition_1", "competition_2"],
        deliverable_type: Literal["proposal", "video_script", "poster"],
        data: ProjectData,
    ) -> str:
        """
        渲染指定比賽與交付物類型的文件。

        Args:
            competition: 比賽編號（"competition_1" 或 "competition_2"）
            deliverable_type: 交付物類型（"proposal"、"video_script" 或 "poster"）
            data: 專案資料

        Returns:
            渲染後的 Markdown 文字

        Raises:
            FileNotFoundError: 模板檔案不存在
            jinja2.TemplateError: 模板渲染失敗
        """
        key = (competition, deliverable_type)
        template_name = _TEMPLATE_MAP.get(key)
        if template_name is None:
            raise ValueError(
                f"不支援的比賽/交付物組合：{competition}/{deliverable_type}"
            )

        try:
            template = self._env.get_template(template_name)
        except jinja2.TemplateNotFound as exc:
            raise FileNotFoundError(
                f"模板檔案不存在：{self._template_dir}/{template_name}"
            ) from exc

        return template.render(data=data)

    def render_all(self, data: ProjectData) -> dict[str, str]:
        """
        渲染全部六份交付物。

        Args:
            data: 專案資料

        Returns:
            {輸出檔案名稱: 渲染後內容} 的字典
        """
        results: dict[str, str] = {}
        for (competition, deliverable_type), output_name in _OUTPUT_NAME_MAP.items():
            content = self.render(competition, deliverable_type, data)
            results[output_name] = content
        return results

    @staticmethod
    def get_output_filename(
        competition: Literal["competition_1", "competition_2"],
        deliverable_type: Literal["proposal", "video_script", "poster"],
    ) -> str:
        """
        取得輸出檔案名稱。

        Args:
            competition: 比賽編號
            deliverable_type: 交付物類型

        Returns:
            輸出檔案名稱
        """
        key = (competition, deliverable_type)
        name = _OUTPUT_NAME_MAP.get(key)
        if name is None:
            raise ValueError(
                f"不支援的比賽/交付物組合：{competition}/{deliverable_type}"
            )
        return name
