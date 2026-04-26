"""
網頁爬蟲資料來源

從台灣政府開放資料平台、165 反詐騙網站、新聞搜尋等來源
爬取最新詐騙統計資料，並透過 LLM 解析非結構化文本。
所有來源均有 graceful fallback，確保即使網站不可用也不會崩潰。
"""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.live_data.models import (
    AnnualStat,
    MonthlyTrendEntry,
    NormalizedData,
    ScamTypeStat,
)

logger = logging.getLogger(__name__)

# 爬取目標 URL
_DATA_GOV_SEARCH_URL = "https://data.gov.tw/datasets/search"
_NPA_165_URL = "https://165.npa.gov.tw"
_GOOGLE_NEWS_SEARCH = "https://news.google.com/search"

# HTTP 請求設定
_SCRAPE_TIMEOUT = 20
_SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


async def scrape_all_sources() -> NormalizedData | None:
    """
    依序嘗試所有爬蟲來源，第一個成功即回傳。

    嘗試順序：
    1. data.gov.tw 開放資料搜尋
    2. 165.npa.gov.tw 統計頁面
    3. Google News 搜尋 + LLM 解析

    全部失敗回傳 None（由上層 fetcher 觸發 fallback）。
    """
    # 來源 1: data.gov.tw
    result = await _scrape_data_gov()
    if result is not None:
        logger.info("爬蟲成功：data.gov.tw")
        return result

    # 來源 2: 165.npa.gov.tw
    result = await _scrape_npa_165()
    if result is not None:
        logger.info("爬蟲成功：165.npa.gov.tw")
        return result

    # 來源 3: Google News + LLM
    result = await _scrape_news_with_llm()
    if result is not None:
        logger.info("爬蟲成功：新聞搜尋 + LLM 解析")
        return result

    logger.warning("所有爬蟲來源均失敗")
    return None


async def _scrape_data_gov() -> NormalizedData | None:
    """爬取 data.gov.tw 搜尋「詐騙統計」的結果頁面"""
    try:
        async with httpx.AsyncClient(
            timeout=_SCRAPE_TIMEOUT, headers=_SCRAPE_HEADERS, follow_redirects=True
        ) as client:
            params = {"qs": "詐騙統計"}
            resp = await client.get(_DATA_GOV_SEARCH_URL, params=params)
            if resp.status_code != 200:
                logger.warning("data.gov.tw 回傳 HTTP %d", resp.status_code)
                return None

            text = resp.text
            data = _extract_stats_from_html(text, "data.gov.tw")
            return data
    except (httpx.TimeoutException, httpx.RequestError, Exception) as exc:
        logger.warning("data.gov.tw 爬取失敗：%s", exc)
        return None


async def _scrape_npa_165() -> NormalizedData | None:
    """爬取 165.npa.gov.tw 首頁或統計頁面"""
    try:
        async with httpx.AsyncClient(
            timeout=_SCRAPE_TIMEOUT, headers=_SCRAPE_HEADERS, follow_redirects=True
        ) as client:
            resp = await client.get(_NPA_165_URL)
            if resp.status_code != 200:
                logger.warning("165.npa.gov.tw 回傳 HTTP %d", resp.status_code)
                return None

            text = resp.text
            data = _extract_stats_from_html(text, "165.npa.gov.tw")
            return data
    except (httpx.TimeoutException, httpx.RequestError, Exception) as exc:
        logger.warning("165.npa.gov.tw 爬取失敗：%s", exc)
        return None


async def _scrape_news_with_llm() -> NormalizedData | None:
    """搜尋新聞並用 LLM 解析統計數據"""
    try:
        news_text = await _fetch_news_snippets()
        if not news_text:
            return None

        data = await _llm_extract_stats(news_text)
        return data
    except Exception as exc:
        logger.warning("新聞 + LLM 解析失敗：%s", exc)
        return None


async def _fetch_news_snippets() -> str | None:
    """從 Google News 搜尋台灣詐騙統計相關新聞"""
    current_year = datetime.now().year
    query = f"台灣 詐騙 統計 {current_year}"
    try:
        async with httpx.AsyncClient(
            timeout=_SCRAPE_TIMEOUT, headers=_SCRAPE_HEADERS, follow_redirects=True
        ) as client:
            params = {"q": query, "hl": "zh-TW", "gl": "TW", "ceid": "TW:zh-Hant"}
            resp = await client.get(_GOOGLE_NEWS_SEARCH, params=params)
            if resp.status_code != 200:
                logger.warning("Google News 回傳 HTTP %d", resp.status_code)
                return None

            # 提取文本片段
            text = _strip_html_tags(resp.text)
            # 取前 3000 字元作為 LLM 輸入
            return text[:3000] if text else None
    except (httpx.TimeoutException, httpx.RequestError, Exception) as exc:
        logger.warning("Google News 搜尋失敗：%s", exc)
        return None


def _strip_html_tags(html: str) -> str:
    """移除 HTML 標籤，保留純文字"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator=" ", strip=True)
    except ImportError:
        # 沒有 bs4 時用 regex 簡單處理
        return re.sub(r"<[^>]+>", " ", html)


def _extract_stats_from_html(html: str, source_name: str) -> NormalizedData | None:
    """
    從 HTML 頁面中提取詐騙統計數據。

    嘗試用 BeautifulSoup 解析表格與數字，
    若無法提取到有意義的數據則回傳 None。
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
    except ImportError:
        logger.warning("beautifulsoup4 未安裝，無法解析 HTML")
        return None

    # 嘗試從 HTML 表格中提取結構化數據
    regions: dict[str, int] = {}
    scam_type_stats: dict[str, ScamTypeStat] = {}

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            cell_texts = [c.get_text(strip=True) for c in cells]
            if len(cell_texts) >= 2:
                label = cell_texts[0]
                # 嘗試匹配縣市名稱 + 數字
                for ct in cell_texts[1:]:
                    num_match = re.search(r"(\d{1,3}(?:,\d{3})*)", ct)
                    if num_match and any(
                        kw in label for kw in ["市", "縣", "區"]
                    ):
                        regions[label] = int(num_match.group(1).replace(",", ""))
                        break
                    # 嘗試匹配詐騙類型
                    if num_match and any(
                        kw in label for kw in ["詐騙", "詐欺", "冒充", "假冒"]
                    ):
                        cases_val = int(num_match.group(1).replace(",", ""))
                        scam_type_stats[label] = ScamTypeStat(
                            cases=cases_val, avg_loss_ntd=0, trend="穩定"
                        )
                        break

    text = soup.get_text(separator=" ", strip=True)

    # 嘗試從文本中提取數字（案件數、金額等）
    numbers = re.findall(r"(\d{1,3}(?:,\d{3})*)\s*(?:件|案|筆)", text)
    amounts = re.findall(r"(\d+(?:\.\d+)?)\s*(?:億|萬)", text)

    # 嘗試提取熱詞（從連結文字、標題等）
    hotwords: dict[str, int] = {}
    for tag in soup.find_all(["a", "h1", "h2", "h3", "h4", "strong", "b"]):
        tag_text = tag.get_text(strip=True)
        if 2 <= len(tag_text) <= 8 and any(
            kw in tag_text for kw in ["詐騙", "詐欺", "投資", "銀行", "客服", "警察", "帳戶"]
        ):
            hotwords[tag_text] = hotwords.get(tag_text, 0) + 1

    if not numbers and not amounts and not regions and not scam_type_stats:
        logger.info("來源 '%s' 未找到可提取的統計數據", source_name)
        return None

    # 建構基本的 NormalizedData
    now = datetime.now(timezone.utc)
    current_year = datetime.now().year

    # 嘗試提取總案件數
    total_cases = 0
    for n in numbers[:5]:
        val = int(n.replace(",", ""))
        if val > total_cases:
            total_cases = val

    # 嘗試提取總金額
    total_loss = 0.0
    for a in amounts[:5]:
        val = float(a)
        if val > total_loss:
            total_loss = val

    if total_cases == 0 and total_loss == 0.0 and not regions and not scam_type_stats:
        return None

    return NormalizedData(
        scam_cases_by_region=regions,
        scam_type_stats=scam_type_stats,
        monthly_trend=[],
        victim_age_distribution={},
        annual_stats={
            str(current_year): AnnualStat(
                total_cases=total_cases,
                total_loss_billion=total_loss,
            )
        } if total_cases > 0 else {},
        source_name=f"scraper:{source_name}",
        fetched_at=now,
        hotwords=hotwords,
        real_scam_scripts=[],
    )


async def _llm_extract_stats(news_text: str) -> NormalizedData | None:
    """
    使用 LLM（Ollama / LangChain）從新聞文本中提取結構化統計數據。

    回傳 NormalizedData 或 None（LLM 不可用或解析失敗時）。
    """
    try:
        import json as _json
        from app.config import get_settings

        settings = get_settings()
        current_year = datetime.now().year

        prompt = (
            f"以下是關於台灣詐騙統計的新聞摘要。請從中提取以下資訊並以 JSON 格式回傳：\n"
            f"1. total_cases: 總案件數（整數）\n"
            f"2. total_loss_billion: 總損失金額（億元，浮點數）\n"
            f"3. scam_types: 各詐騙類型案件數（字典，key 為類型名稱）\n"
            f"4. regions: 各縣市案件數（字典，key 為縣市名稱）\n\n"
            f"如果某項資訊無法從文本中提取，請設為 null。\n"
            f"只回傳 JSON，不要其他文字。\n\n"
            f"新聞摘要：\n{news_text[:2000]}"
        )

        llm_response = None

        if settings.llm_provider == "ollama":
            try:
                from langchain_community.llms import Ollama
                llm = Ollama(model=settings.ollama_model, temperature=0)
                llm_response = llm.invoke(prompt)
            except ImportError:
                # 嘗試直接用 httpx 呼叫 Ollama API
                llm_response = await _call_ollama_direct(
                    settings.ollama_model, prompt
                )
            except Exception as exc:
                logger.warning("Ollama LangChain 呼叫失敗：%s", exc)
                llm_response = await _call_ollama_direct(
                    settings.ollama_model, prompt
                )
        elif settings.llm_provider == "openai" and settings.openai_api_key:
            try:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model=settings.openai_model,
                    api_key=settings.openai_api_key,
                    temperature=0,
                )
                result = llm.invoke(prompt)
                llm_response = result.content
            except Exception as exc:
                logger.warning("OpenAI LLM 呼叫失敗：%s", exc)
        elif settings.llm_provider == "google" and settings.google_api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model=settings.google_model,
                    google_api_key=settings.google_api_key,
                    temperature=0,
                )
                result = llm.invoke(prompt)
                llm_response = result.content
            except Exception as exc:
                logger.warning("Google LLM 呼叫失敗：%s", exc)

        if not llm_response:
            return None

        return _parse_llm_json_response(llm_response, current_year)

    except Exception as exc:
        logger.warning("LLM 統計提取失敗：%s", exc)
        return None


async def _call_ollama_direct(model: str, prompt: str) -> str | None:
    """直接透過 HTTP 呼叫 Ollama API"""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "")
    except Exception as exc:
        logger.warning("Ollama 直接呼叫失敗：%s", exc)
    return None


def _parse_llm_json_response(
    response: str, current_year: int
) -> NormalizedData | None:
    """解析 LLM 回傳的 JSON 字串為 NormalizedData"""
    import json as _json

    # 嘗試從回應中提取 JSON
    json_match = re.search(r"\{[\s\S]*\}", response)
    if not json_match:
        return None

    try:
        data = _json.loads(json_match.group())
    except _json.JSONDecodeError:
        return None

    now = datetime.now(timezone.utc)

    total_cases = data.get("total_cases") or 0
    total_loss = data.get("total_loss_billion") or 0.0

    # 解析詐騙類型
    scam_type_stats: dict[str, ScamTypeStat] = {}
    raw_types = data.get("scam_types") or {}
    if isinstance(raw_types, dict):
        for name, cases in raw_types.items():
            if isinstance(cases, (int, float)) and cases > 0:
                scam_type_stats[name] = ScamTypeStat(
                    cases=int(cases), avg_loss_ntd=0, trend="穩定"
                )

    # 解析地區
    regions: dict[str, int] = {}
    raw_regions = data.get("regions") or {}
    if isinstance(raw_regions, dict):
        for name, cases in raw_regions.items():
            if isinstance(cases, (int, float)) and cases > 0:
                regions[name] = int(cases)

    annual_stats: dict[str, AnnualStat] = {}
    if total_cases > 0:
        annual_stats[str(current_year)] = AnnualStat(
            total_cases=int(total_cases),
            total_loss_billion=float(total_loss),
        )

    if not regions and not scam_type_stats and not annual_stats:
        return None

    return NormalizedData(
        scam_cases_by_region=regions,
        scam_type_stats=scam_type_stats,
        monthly_trend=[],
        victim_age_distribution={},
        annual_stats=annual_stats,
        source_name="scraper:news+llm",
        fetched_at=now,
        hotwords={},
        real_scam_scripts=[],
    )
