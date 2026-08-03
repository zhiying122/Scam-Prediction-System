"""
DataExtractor — 資料萃取器

從 ScamOracle 專案原始碼與設定檔中萃取所有交付物所需的技術數據與統計資訊。
支援降級策略：當檔案缺失時使用硬編碼預設值並記錄警告。
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from app.deliverable_generator.models import ProjectData, TeamMember

logger = logging.getLogger(__name__)


class DataExtractor:
    """從專案原始碼與設定檔萃取資料"""

    def __init__(self, project_root: str | None = None) -> None:
        """
        初始化資料萃取器。

        Args:
            project_root: 專案根目錄路徑。預設為當前工作目錄。
        """
        self._root = Path(project_root) if project_root else Path.cwd()

    def extract(self) -> ProjectData:
        """萃取完整專案資料，回傳 ProjectData 實例。"""
        test_count = self._count_tests()
        module_names = self._list_modules()
        tech_stack = self._extract_tech_stack()
        scam_stats = self._extract_scam_statistics()
        docker_services = self._extract_docker_services()

        return ProjectData(
            # 品牌資訊
            project_name="ScamOracle",
            project_subtitle="AI 詐騙進化預測系統",
            # 技術數據
            test_count=test_count,
            embedding_dim=384,
            dashboard_page_count=12,
            api_endpoint_count=7,
            module_names=module_names,
            tech_stack=tech_stack,
            docker_services=docker_services,
            # 台灣詐騙統計數據
            scam_cases_2023=scam_stats.get("scam_cases_2023", 83000),
            scam_loss_2023=scam_stats.get("scam_loss_2023", "88.2 億元"),
            scam_loss_growth_rate=scam_stats.get("scam_loss_growth_rate", "28%"),
            scam_cases_growth_rate=scam_stats.get("scam_cases_growth_rate", "27%"),
            avg_loss_investment=scam_stats.get("avg_loss_investment", "85 萬元"),
            avg_loss_romance=scam_stats.get("avg_loss_romance", "42 萬元"),
            early_warning_hours=24,
            detection_accuracy="88.9%（規則式 XAI 分類器，1,200 筆測試集）",
            # AI 模型資訊
            llm_models=[
                "Meta Llama 3（透過 Ollama 本地部署）",
                "Google Gemini",
            ],
            embedding_model="paraphrase-multilingual-MiniLM-L12-v2",
            # Scam_DNA 心理特徵
            psychological_dimensions=[
                "信任建立",
                "緊迫感製造",
                "情緒勒索",
                "權威偽裝",
                "利益誘導",
            ],
            # 團隊分工
            team_members=[
                TeamMember(
                    name="Member A",
                    responsibilities=["後端架構", "AI 模型", "雲端部署"],
                ),
                TeamMember(
                    name="Member B",
                    responsibilities=["資料處理", "前端介面", "版本控制", "簡報"],
                ),
            ],
            # 測試策略
            test_types={"unit": test_count, "property": 0, "integration": 0},
            # 系統架構層次
            architecture_layers=["Input", "Engine", "Analysis", "Output"],
        )

    # ── 私有萃取方法 ─────────────────────────────────────────────────────────

    def _count_tests(self) -> int:
        """
        掃描 tests/ 目錄計算測試函數總數。

        計算所有 .py 檔案中以 ``def test_`` 或 ``async def test_`` 開頭的函數。
        當 tests/ 目錄不存在時回傳 0 並記錄警告。
        """
        tests_dir = self._root / "tests"
        if not tests_dir.is_dir():
            logger.warning("tests/ 目錄不存在，test_count 設為 0")
            return 0

        count = 0
        pattern = re.compile(r"^\s*(async\s+)?def\s+test_")
        for py_file in tests_dir.rglob("*.py"):
            try:
                text = py_file.read_text(encoding="utf-8")
                for line in text.splitlines():
                    if pattern.match(line):
                        count += 1
            except OSError as exc:
                logger.warning("無法讀取測試檔案 %s: %s", py_file, exc)

        return count

    def _list_modules(self) -> list[str]:
        """
        列出 app/ 下的核心模組名稱。

        核心模組定義為 app/ 下包含 __init__.py 的子目錄（Python packages），
        排除 __pycache__ 等隱藏目錄。
        """
        app_dir = self._root / "app"
        if not app_dir.is_dir():
            logger.warning("app/ 目錄不存在，module_names 設為空列表")
            return []

        modules: list[str] = []
        for item in sorted(app_dir.iterdir()):
            if (
                item.is_dir()
                and not item.name.startswith("__")
                and (item / "__init__.py").exists()
            ):
                modules.append(item.name)

        if not modules:
            logger.warning("app/ 下未找到任何 Python 套件")

        return modules

    def _extract_tech_stack(self) -> dict[str, str]:
        """
        萃取技術棧資訊。

        嘗試從 README.md 的技術棧表格解析，失敗時使用硬編碼預設值。
        """
        readme_path = self._root / "README.md"

        if readme_path.is_file():
            try:
                content = readme_path.read_text(encoding="utf-8")
                tech_stack = self._parse_tech_stack_from_readme(content)
                if tech_stack:
                    return tech_stack
            except OSError as exc:
                logger.warning("無法讀取 README.md: %s", exc)

        logger.warning("無法從 README.md 萃取技術棧，使用硬編碼預設值")
        return self._default_tech_stack()

    def _parse_tech_stack_from_readme(self, content: str) -> dict[str, str]:
        """從 README.md 內容解析技術棧表格。"""
        tech_stack: dict[str, str] = {}

        # 找到「技術棧」章節下的表格
        in_tech_section = False
        in_table = False
        for line in content.splitlines():
            if re.match(r"^#+\s*技術棧", line):
                in_tech_section = True
                continue
            if in_tech_section and line.startswith("|") and "---" not in line:
                # 解析表格行: | 類別 | 技術 |
                parts = [p.strip() for p in line.split("|")]
                # parts[0] 和 parts[-1] 是空字串（因為 | 開頭和結尾）
                parts = [p for p in parts if p]
                if len(parts) >= 2 and parts[0] != "類別":
                    tech_stack[parts[0]] = parts[1]
                in_table = True
            elif in_tech_section and in_table and not line.startswith("|"):
                # 離開表格區域
                break

        return tech_stack

    @staticmethod
    def _default_tech_stack() -> dict[str, str]:
        """硬編碼的預設技術棧。"""
        return {
            "後端框架": "FastAPI + Uvicorn",
            "LLM 整合": "LangChain + Ollama（主要）/ GPT-4o / Gemini（備用）",
            "NLP": "Sentence-BERT (paraphrase-multilingual-MiniLM-L12-v2)",
            "機器學習": "scikit-learn (TF-IDF, K-Means, Isolation Forest)",
            "XAI": "規則式 Regex 高亮 + 信心分數",
            "排程": "APScheduler（預測分析 24h + 資料擷取 6h）",
            "前端": "Streamlit（12 頁面）",
            "測試": "pytest + Hypothesis (Property-Based Testing)",
            "容器化": "Docker + Docker Compose",
        }

    def _extract_scam_statistics(self) -> dict[str, Any]:
        """
        從 data/taiwan_scam_data.py 萃取台灣詐騙統計數據。

        嘗試匯入模組取得 ANNUAL_STATS 與 SCAM_TYPE_STATS，
        失敗時使用硬編碼預設值。
        """
        try:
            from data.taiwan_scam_data import ANNUAL_STATS, SCAM_TYPE_STATS

            stats_2023 = ANNUAL_STATS.get(2023, {})
            total_cases = stats_2023.get("total_cases", 83000)
            total_loss = stats_2023.get("total_loss_billion", 88.2)

            # 計算年增率
            stats_2022 = ANNUAL_STATS.get(2022, {})
            cases_2022 = stats_2022.get("total_cases", 65000)
            loss_2022 = stats_2022.get("total_loss_billion", 68.7)

            cases_growth = round((total_cases - cases_2022) / cases_2022 * 100)
            loss_growth = round((total_loss - loss_2022) / loss_2022 * 100)

            # 從 SCAM_TYPE_STATS 萃取平均損失
            investment_stats = SCAM_TYPE_STATS.get("投資詐騙", {})
            romance_stats = SCAM_TYPE_STATS.get("愛情詐騙", {})
            avg_investment = investment_stats.get("avg_loss_ntd", 850000)
            avg_romance = romance_stats.get("avg_loss_ntd", 420000)

            return {
                "scam_cases_2023": total_cases,
                "scam_loss_2023": f"{total_loss} 億元",
                "scam_loss_growth_rate": f"{loss_growth}%",
                "scam_cases_growth_rate": f"{cases_growth}%",
                "avg_loss_investment": f"{avg_investment // 10000} 萬元",
                "avg_loss_romance": f"{avg_romance // 10000} 萬元",
            }
        except Exception as exc:
            logger.warning("無法從 data/taiwan_scam_data.py 萃取統計數據: %s，使用硬編碼預設值", exc)
            return self._default_scam_statistics()

    @staticmethod
    def _default_scam_statistics() -> dict[str, Any]:
        """硬編碼的預設詐騙統計數據。"""
        return {
            "scam_cases_2023": 83000,
            "scam_loss_2023": "88.2 億元",
            "scam_loss_growth_rate": "28%",
            "scam_cases_growth_rate": "27%",
            "avg_loss_investment": "85 萬元",
            "avg_loss_romance": "42 萬元",
        }

    def _extract_docker_services(self) -> list[str]:
        """
        從 docker-compose.yml 萃取 Docker 服務列表。

        回傳人類可讀的服務名稱（如 PostgreSQL、Redis、Qdrant），
        失敗時使用硬編碼預設值。
        """
        compose_path = self._root / "docker-compose.yml"
        if not compose_path.is_file():
            logger.warning("docker-compose.yml 不存在，docker_services 使用預設值")
            return self._default_docker_services()

        try:
            # 使用 yaml 解析 docker-compose.yml
            import yaml

            content = compose_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
            services = list(data.get("services", {}).keys())

            # 將服務名稱映射為人類可讀名稱
            name_map = {
                "postgres": "PostgreSQL",
                "redis": "Redis",
                "qdrant": "Qdrant",
            }
            return [name_map.get(s, s) for s in services]
        except Exception as exc:
            logger.warning("無法解析 docker-compose.yml: %s，使用預設值", exc)
            return self._default_docker_services()

    @staticmethod
    def _default_docker_services() -> list[str]:
        """硬編碼的預設 Docker 服務列表。"""
        return ["PostgreSQL", "Redis", "Qdrant"]
