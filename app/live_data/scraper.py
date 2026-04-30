"""
網頁爬蟲資料來源

從台灣政府開放資料平台、165 反詐騙網站、新聞搜尋等來源
爬取最新詐騙統計資料，並透過 LLM 解析非結構化文本。
所有來源均有 graceful fallback，確保即使網站不可用也不會崩潰。

注意：所有函數皆為同步（sync），因為 APScheduler BackgroundScheduler
在獨立線程中執行，沒有 async 事件迴圈。
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.live_data.models import (
    AnnualStat,
    NormalizedData,
    ScamTypeStat,
)

logger = logging.getLogger(__name__)

_DATA_GOV_SEARCH_URL = "https://data.gov.tw/datasets/search"
_NPA_165_URL = "https://165.npa.gov.tw"
_GOOGLE_NEWS_SEARCH = "https://news.google.com/search"

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


def scrape_all_sources() -> NormalizedData | None:
    """依序嘗試所有爬蟲來源，第一個成功即回傳。全部失敗回傳 None。"""
    result = _scrape_data_gov()
    if result is not None:
        logger.info("爬蟲成功：data.gov.tw")
        return result

    result = _scrape_npa_165()
    if result is not None:
        logger.info("爬蟲成功：165.npa.gov.tw")
        return result

    result = _scrape_news_with_llm()
    if result is not None:
        logger.info("爬蟲成功：新聞搜尋 + LLM 解析")
        return result

    logger.warning("所有爬蟲來源均失敗")
    return None


def _scrape_data_gov() -> NormalizedData | None:
    """爬取 data.gov.tw（同步）"""
    try:
        with httpx.Client(
            timeout=_SCRAPE_TIMEOUT, headers=_SCRAPE_HEADERS, follow_redirects=True
        ) as client:
            resp = client.get(_DATA_GOV_SEARCH_URL, params={"qs": "詐騙統計"})
            if resp.status_code != 200:
                logger.warning("data.gov.tw 回傳 HTTP %d", resp.status_code)
                return None
            return _extract_stats_from_html(resp.text, "data.gov.tw")
    except Exception as exc:
        logger.warning("data.gov.tw 爬取失敗：%s", exc)
        return None


def _scrape_npa_165() -> NormalizedData | None:
    """爬取 165.npa.gov.tw（同步）"""
    try:
        with httpx.Client(
            timeout=_SCRAPE_TIMEOUT, headers=_SCRAPE_HEADERS, follow_redirects=True
        ) as client:
            resp = client.get(_NPA_165_URL)
            if resp.status_code != 200:
                logger.warning("165.npa.gov.tw 回傳 HTTP %d", resp.status_code)
                return None
            return _extract_stats_from_html(resp.text, "165.npa.gov.tw")
    except Exception as exc:
        logger.warning("165.npa.gov.tw 爬取失敗：%s", exc)
        return None


def _scrape_news_with_llm() -> NormalizedData | None:
    """搜尋新聞並用 LLM 解析（同步）"""
    try:
        news_text = _fetch_news_snippets()
        if not news_text:
            return None
        return _llm_extract_stats(news_text)
    except Exception as exc:
        logger.warning("新聞 + LLM 解析失敗：%s", exc)
        return None


def _fetch_news_snippets() -> str | None:
    """從 Google News 搜尋台灣詐騙統計相關新聞（同步）"""
    current_year = datetime.now().year
    query = f"台灣 詐騙 統計 {current_year}"
    try:
        with httpx.Client(
            timeout=_SCRAPE_TIMEOUT, headers=_SCRAPE_HEADERS, follow_redirects=True
        ) as client:
            params = {"q": query, "hl": "zh-TW", "gl": "TW", "ceid": "TW:zh-Hant"}
            resp = client.get(_GOOGLE_NEWS_SEARCH, params=params)
            if resp.status_code != 200:
                logger.warning("Google News 回傳 HTTP %d", resp.status_code)
                return None
            text = _strip_html_tags(resp.text)
            return text[:3000] if text else None
    except Exception as exc:
        logger.warning("Google News 搜尋失敗：%s", exc)
        return None


def _strip_html_tags(html: str) -> str:
    """移除 HTML 標籤"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator=" ", strip=True)
    except ImportError:
        return re.sub(r"<[^>]+>", " ", html)


def _extract_stats_from_html(html: str, source_name: str) -> NormalizedData | None:
    """從 HTML 頁面中提取詐騙統計數據"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
    except ImportError:
        logger.warning("beautifulsoup4 未安裝")
        return None

    regions: dict[str, int] = {}
    scam_type_stats: dict[str, ScamTypeStat] = {}

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) >= 2:
                label = cells[0]
                for ct in cells[1:]:
                    num_match = re.search(r"(\d{1,3}(?:,\d{3})*)", ct)
                    if num_match and any(kw in label for kw in ["市", "縣", "區"]):
                        regions[label] = int(num_match.group(1).replace(",", ""))
                        break
                    if num_match and any(kw in label for kw in ["詐騙", "詐欺", "冒充", "假冒"]):
                        scam_type_stats[label] = ScamTypeStat(
                            cases=int(num_match.group(1).replace(",", "")),
                            avg_loss_ntd=0, trend="穩定",
                        )
                        break

    text = soup.get_text(separator=" ", strip=True)
    numbers = re.findall(r"(\d{1,3}(?:,\d{3})*)\s*(?:件|案|筆)", text)
    amounts = re.findall(r"(\d+(?:\.\d+)?)\s*(?:億|萬)", text)

    hotwords: dict[str, int] = {}
    for tag in soup.find_all(["a", "h1", "h2", "h3", "h4", "strong", "b"]):
        t = tag.get_text(strip=True)
        if 2 <= len(t) <= 8 and any(kw in t for kw in ["詐騙", "投資", "銀行", "客服", "帳戶"]):
            hotwords[t] = hotwords.get(t, 0) + 1

    if not numbers and not amounts and not regions and not scam_type_stats:
        return None

    now = datetime.now(timezone.utc)
    current_year = datetime.now().year
    total_cases = max((int(n.replace(",", "")) for n in numbers[:5]), default=0)
    total_loss = max((float(a) for a in amounts[:5]), default=0.0)

    if total_cases == 0 and total_loss == 0.0 and not regions and not scam_type_stats:
        return None

    return NormalizedData(
        scam_cases_by_region=regions,
        scam_type_stats=scam_type_stats,
        monthly_trend=[],
        victim_age_distribution={},
        annual_stats={str(current_year): AnnualStat(total_cases=total_cases, total_loss_billion=total_loss)} if total_cases > 0 else {},
        source_name=f"scraper:{source_name}",
        fetched_at=now,
        hotwords=hotwords,
        real_scam_scripts=[],
    )


def _llm_extract_stats(news_text: str) -> NormalizedData | None:
    """使用 LLM 從新聞文本中提取統計數據（同步）"""
    try:
        import json as _json
        from app.config import get_settings

        settings = get_settings()
        current_year = datetime.now().year

        prompt = (
            f"以下是關於台灣詐騙統計的新聞摘要。請從中提取以下資訊並以 JSON 格式回傳：\n"
            f"1. total_cases: 總案件數（整數）\n"
            f"2. total_loss_billion: 總損失金額（億元，浮點數）\n"
            f"3. scam_types: 各詐騙類型案件數（字典）\n"
            f"4. regions: 各縣市案件數（字典）\n\n"
            f"只回傳 JSON。\n\n新聞摘要：\n{news_text[:2000]}"
        )

        llm_response = None

        if settings.llm_provider == "ollama":
            llm_response = _call_ollama_direct_sync(settings.ollama_model, prompt)
        elif settings.llm_provider == "openai" and settings.openai_api_key:
            try:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0)
                llm_response = llm.invoke(prompt).content
            except Exception as exc:
                logger.warning("OpenAI LLM 呼叫失敗：%s", exc)

        if not llm_response:
            return None

        return _parse_llm_json_response(llm_response, current_year)
    except Exception as exc:
        logger.warning("LLM 統計提取失敗：%s", exc)
        return None


def _call_ollama_direct_sync(model: str, prompt: str) -> str | None:
    """直接透過同步 HTTP 呼叫 Ollama API"""
    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            if resp.status_code == 200:
                return resp.json().get("response", "")
    except Exception as exc:
        logger.warning("Ollama 直接呼叫失敗：%s", exc)
    return None


def _parse_llm_json_response(response: str, current_year: int) -> NormalizedData | None:
    """解析 LLM 回傳的 JSON"""
    import json as _json

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

    scam_type_stats: dict[str, ScamTypeStat] = {}
    for name, cases in (data.get("scam_types") or {}).items():
        if isinstance(cases, (int, float)) and cases > 0:
            scam_type_stats[name] = ScamTypeStat(cases=int(cases), avg_loss_ntd=0, trend="穩定")

    regions: dict[str, int] = {}
    for name, cases in (data.get("regions") or {}).items():
        if isinstance(cases, (int, float)) and cases > 0:
            regions[name] = int(cases)

    annual_stats = {str(current_year): AnnualStat(total_cases=int(total_cases), total_loss_billion=float(total_loss))} if total_cases > 0 else {}

    if not regions and not scam_type_stats and not annual_stats:
        return None

    return NormalizedData(
        scam_cases_by_region=regions, scam_type_stats=scam_type_stats,
        monthly_trend=[], victim_age_distribution={}, annual_stats=annual_stats,
        source_name="scraper:news+llm", fetched_at=now, hotwords={}, real_scam_scripts=[],
    )
