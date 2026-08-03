"""
DeliverableGenerator — 交付物產出器（主入口）

協調 DataExtractor、ConsistencyValidator、TemplateRenderer 的完整產出流程。
提供 generate() 與 generate_all() 方法產出交付物。
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Literal

from app.deliverable_generator.extractor import DataExtractor
from app.deliverable_generator.models import (
    ProjectData,
    ValidationResult,
)
from app.deliverable_generator.renderer import TemplateRenderer
from app.deliverable_generator.validator import ConsistencyValidator

logger = logging.getLogger(__name__)


class ConsistencyError(Exception):
    """資料一致性驗證失敗時拋出的例外"""

    def __init__(self, result: ValidationResult) -> None:
        self.result = result
        errors_text = "; ".join(e.message for e in result.errors)
        super().__init__(f"資料一致性驗證失敗：{errors_text}")


def _compute_data_hash(data: ProjectData) -> str:
    """計算 ProjectData 的雜湊值，用於追蹤資料版本。"""
    # 使用關鍵欄位組合計算 hash
    key_fields = (
        data.project_name,
        str(data.test_count),
        str(data.embedding_dim),
        str(data.dashboard_page_count),
        str(data.api_endpoint_count),
        str(data.detection_accuracy),
    )
    raw = "|".join(key_fields)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class DeliverableGenerator:
    """交付物產出系統主入口"""

    def __init__(
        self,
        extractor: DataExtractor | None = None,
        validator: ConsistencyValidator | None = None,
        renderer: TemplateRenderer | None = None,
    ) -> None:
        """
        初始化交付物產出器。

        Args:
            extractor: 資料萃取器（預設自動建立）
            validator: 一致性驗證器（預設自動建立）
            renderer: 模板渲染器（預設自動建立）
        """
        self._extractor = extractor or DataExtractor()
        self._validator = validator or ConsistencyValidator()
        self._renderer = renderer or TemplateRenderer()

    def generate(
        self,
        competition: Literal["competition_1", "competition_2"],
        deliverable_type: Literal["proposal", "video_script", "poster"],
        output_dir: str = "deliverables/",
    ) -> str:
        """
        產出單一交付物。

        流程：萃取資料 → 驗證一致性 → 渲染模板 → 寫入檔案

        Args:
            competition: 比賽編號
            deliverable_type: 交付物類型
            output_dir: 輸出目錄

        Returns:
            輸出檔案路徑

        Raises:
            ConsistencyError: 資料一致性驗證失敗
        """
        # 1. 萃取資料
        logger.info("開始萃取專案資料...")
        data = self._extractor.extract()

        # 2. 驗證一致性
        logger.info("驗證資料一致性...")
        result = self._validator.validate(data)
        if not result.is_valid:
            raise ConsistencyError(result)

        # 3. 渲染模板
        logger.info("渲染模板：%s / %s", competition, deliverable_type)
        content = self._renderer.render(competition, deliverable_type, data)

        # 4. 寫入檔案
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = TemplateRenderer.get_output_filename(competition, deliverable_type)
        file_path = output_path / filename
        file_path.write_text(content, encoding="utf-8")

        logger.info("交付物已寫入：%s", file_path)
        return str(file_path)

    def generate_all(self, output_dir: str = "deliverables/") -> list[str]:
        """
        產出全部六份交付物至指定目錄。

        Args:
            output_dir: 輸出目錄

        Returns:
            輸出檔案路徑列表

        Raises:
            ConsistencyError: 資料一致性驗證失敗
        """
        # 1. 萃取資料（只萃取一次）
        logger.info("開始萃取專案資料...")
        data = self._extractor.extract()

        # 2. 驗證一致性
        logger.info("驗證資料一致性...")
        result = self._validator.validate(data)
        if not result.is_valid:
            raise ConsistencyError(result)

        # 3. 渲染全部模板
        logger.info("渲染全部六份交付物...")
        all_outputs = self._renderer.render_all(data)

        # 4. 寫入檔案
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        data_hash = _compute_data_hash(data)
        file_paths: list[str] = []

        for filename, content in all_outputs.items():
            file_path = output_path / filename
            file_path.write_text(content, encoding="utf-8")
            file_paths.append(str(file_path))
            logger.info("交付物已寫入：%s (hash=%s)", file_path, data_hash)

        logger.info(
            "全部 %d 份交付物產出完成，輸出目錄：%s",
            len(file_paths),
            output_dir,
        )
        return file_paths
