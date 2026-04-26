"""
LLM 自動生成進化時間軸

使用 Ollama/LLM 搜尋最新詐騙新聞，自動生成當年度的進化時間軸條目。
結果快取至磁碟（data/timeline_cache.json），30 天內不重複呼叫。
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

# 快取設定
_CACHE_FILE = Path("data/timeline_cache.json")
_CACHE_TTL_DAYS = 30

# 7 種詐騙類型
_SCAM_TYPES = [
    "假冒銀行客服",
    "投資詐騙",
    "假冒政府機關",
    "愛情詐騙",
    "購物詐騙",
    "中獎詐騙",
    "工作詐騙",
]

# ── LLM Prompt ────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """你是台灣詐騙犯罪研究專家，專門追蹤詐騙手法的演化趨勢。
請根據你的知識，為指定年份的每種詐騙類型生成一筆進化時間軸條目。

請嚴格按照以下 JSON 格式輸出，不要包含任何其他文字：
{{
  "timeline": {{
    "詐騙類型名稱": {{
      "year": {year},
      "keywords": ["關鍵字1", "關鍵字2", "關鍵字3"],
      "method": "主要手法描述",
      "avg_loss": 數字（新台幣平均損失金額）,
      "cases": 數字（估計案件數）,
      "new_tactic": "該年度最新觀察到的戰術"
    }}
  }}
}}

要求：
1. keywords 必須恰好 3 個，反映該年度最新趨勢關鍵字
2. method 描述該年度的主要詐騙手法（15-30 字）
3. avg_loss 為新台幣金額，須為合理數字
4. cases 為全年估計案件數，須為合理數字
5. new_tactic 描述該年度最新觀察到的詐騙戰術（20-40 字）
6. 所有內容使用繁體中文"""

_HUMAN_PROMPT = """請為以下 {year} 年的台灣詐騙類型各生成一筆進化時間軸條目：

詐騙類型：
{scam_types}

請根據 {year} 年台灣詐騙趨勢，為每種類型提供最新的演化資料。
數據應反映真實趨勢（如 AI 技術應用、社群平台變化等）。"""


# ── LLM 客戶端 ────────────────────────────────────────────────────────────────

def _build_llm_client():
    """根據 LLM_PROVIDER 設定建立對應的 LLM 客戶端（與 scam_engine 相同模式）"""
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI

    from app.config import get_settings

    get_settings.cache_clear()
    load_dotenv(override=True)
    s = get_settings()
    if s.llm_provider == "ollama":
        return ChatOpenAI(
            model=s.ollama_model,
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            temperature=0.7,
        )
    elif s.llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=s.google_model,
            google_api_key=s.google_api_key,
            temperature=0.7,
        )
    else:
        return ChatOpenAI(
            model=s.openai_model,
            api_key=s.openai_api_key,
            temperature=0.7,
        )


# ── 快取管理 ──────────────────────────────────────────────────────────────────

def _load_cache() -> dict | None:
    """從磁碟載入快取，回傳 None 表示無快取或讀取失敗。"""
    try:
        if not _CACHE_FILE.exists():
            return None
        raw = _CACHE_FILE.read_text(encoding="utf-8")
        return json.loads(raw)
    except Exception as exc:
        logger.warning("讀取 timeline 快取失敗: %s", exc)
        return None


def _save_cache(data: dict) -> None:
    """將資料寫入磁碟快取。"""
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "year": data.get("year", datetime.now().year),
            "timeline": data.get("timeline", {}),
        }
        _CACHE_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("timeline 快取已寫入 %s", _CACHE_FILE)
    except Exception as exc:
        logger.warning("寫入 timeline 快取失敗: %s", exc)


def _is_cache_valid(cache: dict) -> bool:
    """檢查快取是否在 30 天有效期內且年份匹配。"""
    try:
        generated_at = datetime.fromisoformat(cache["generated_at"])
        # 確保 generated_at 有時區資訊
        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - generated_at).days
        cached_year = cache.get("year", 0)
        current_year = datetime.now().year
        return age_days < _CACHE_TTL_DAYS and cached_year == current_year
    except (KeyError, ValueError, TypeError) as exc:
        logger.warning("快取驗證失敗: %s", exc)
        return False


# ── LLM 呼叫 ─────────────────────────────────────────────────────────────────

def _parse_llm_response(raw: str) -> dict | None:
    """從 LLM 回應中解析 timeline JSON。"""
    # 嘗試直接解析
    try:
        data = json.loads(raw)
        if "timeline" in data and isinstance(data["timeline"], dict):
            return data["timeline"]
    except json.JSONDecodeError:
        pass

    # 嘗試從文字中提取 JSON 區塊
    match = re.search(r'\{[\s\S]*"timeline"[\s\S]*\}', raw)
    if match:
        try:
            data = json.loads(match.group())
            if "timeline" in data and isinstance(data["timeline"], dict):
                return data["timeline"]
        except json.JSONDecodeError:
            pass

    return None


def _validate_entry(entry: dict, year: int) -> dict | None:
    """驗證單筆 timeline 條目格式是否正確。"""
    try:
        keywords = entry.get("keywords", [])
        if not isinstance(keywords, list) or len(keywords) < 1:
            return None
        # 確保恰好 3 個 keywords
        keywords = [str(k) for k in keywords[:3]]
        while len(keywords) < 3:
            keywords.append("新型手法")

        method = str(entry.get("method", "")).strip()
        if not method:
            return None

        avg_loss = int(entry.get("avg_loss", 0))
        cases = int(entry.get("cases", 0))
        new_tactic = str(entry.get("new_tactic", "")).strip()

        if avg_loss <= 0 or cases <= 0 or not new_tactic:
            return None

        return {
            "year": year,
            "keywords": keywords,
            "method": method,
            "avg_loss": avg_loss,
            "cases": cases,
            "new_tactic": new_tactic,
        }
    except (ValueError, TypeError):
        return None


async def _call_llm_for_timeline(
    scam_types: list[str], year: int
) -> dict | None:
    """呼叫 LLM 生成指定年份的 timeline 條目。

    Returns:
        dict mapping scam_type -> validated entry, or None on failure.
    """
    try:
        llm = _build_llm_client()
        types_text = "\n".join(f"- {t}" for t in scam_types)
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT.format(year=year)),
            HumanMessage(content=_HUMAN_PROMPT.format(
                year=year, scam_types=types_text,
            )),
        ]

        response = await asyncio.wait_for(
            llm.ainvoke(messages),
            timeout=120,
        )

        raw_timeline = _parse_llm_response(response.content)
        if raw_timeline is None:
            logger.warning("LLM 回應無法解析為 timeline JSON")
            return None

        # 驗證每筆條目
        result: dict[str, dict] = {}
        for scam_type in scam_types:
            entry = raw_timeline.get(scam_type)
            if entry is None:
                logger.warning("LLM 回應缺少 %s 的條目", scam_type)
                continue
            validated = _validate_entry(entry, year)
            if validated:
                result[scam_type] = validated
            else:
                logger.warning("LLM 回應中 %s 的條目驗證失敗", scam_type)

        if not result:
            return None

        logger.info("LLM 成功生成 %d/%d 種詐騙類型的 timeline", len(result), len(scam_types))
        return result

    except asyncio.TimeoutError:
        logger.warning("LLM 呼叫逾時（timeline 生成）")
        return None
    except Exception as exc:
        logger.warning("LLM 呼叫失敗（timeline 生成）: %s: %s", type(exc).__name__, exc)
        return None


# ── 安全的同步執行 ────────────────────────────────────────────────────────────

def _safe_sync_run(coro):
    """在同步環境中安全執行 async coroutine。"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Streamlit / nest_asyncio 環境
            return loop.run_until_complete(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ── 主要入口 ──────────────────────────────────────────────────────────────────

def generate_current_year_timeline() -> dict[str, list[dict]] | None:
    """生成當年度所有 7 種詐騙類型的 timeline 條目。

    流程：
    1. 檢查磁碟快取是否有效（30 天內）
    2. 若有效，直接回傳快取資料
    3. 若無效，呼叫 LLM 生成新資料
    4. 將結果寫入快取
    5. 回傳 dict[scam_type, [entry]]，每種類型一筆條目

    Returns:
        dict mapping scam_type -> list of timeline entries (each list has 1 entry),
        or None if LLM unavailable.
    """
    current_year = datetime.now().year

    # 1. 嘗試載入快取
    cache = _load_cache()
    if cache is not None and _is_cache_valid(cache):
        cached_timeline = cache.get("timeline", {})
        if cached_timeline:
            logger.info("使用快取的 timeline 資料（年份 %d）", current_year)
            # 轉換為 dict[str, list[dict]] 格式
            return {k: [v] for k, v in cached_timeline.items()}

    # 2. 呼叫 LLM 生成
    logger.info("開始呼叫 LLM 生成 %d 年 timeline...", current_year)
    result = _safe_sync_run(_call_llm_for_timeline(_SCAM_TYPES, current_year))

    if result is None:
        logger.warning("LLM 生成 timeline 失敗，回傳 None")
        return None

    # 3. 寫入快取
    _save_cache({"year": current_year, "timeline": result})

    # 4. 回傳 dict[str, list[dict]] 格式
    return {k: [v] for k, v in result.items()}
