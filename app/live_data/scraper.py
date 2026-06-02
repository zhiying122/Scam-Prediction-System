"""
網頁爬蟲資料來源

爬取順序：
  1. 自由時報詐騙統計新聞搜尋（有真實靜態 HTML，可直接 Regex 萃取）
  2. 165.npa.gov.tw 首頁文字萃取
  3. Google News + LLM 解析（備援）

所有函數皆為同步（sync），因為 APScheduler BackgroundScheduler
在獨立線程中執行，沒有 async 事件迴圈。
"""

import logging
import re
from datetime import datetime, timezone

import httpx

from app.live_data.models import (
    AnnualStat,
    NormalizedData,
    ScamTypeStat,
)

logger = logging.getLogger(__name__)

# ── URL 設定 ──────────────────────────────────────────────────────────────────
_LTN_SEARCH_URL = "https://search.ltn.com.tw/list"   # 自由時報搜尋（follow redirect）
_NPA_165_URL = "https://165.npa.gov.tw"
_GOOGLE_NEWS_SEARCH = "https://news.google.com/search"

_SCRAPE_TIMEOUT = 20

# 合法的詐騙類型白名單（與 taiwan_scam_data.py 一致）
_VALID_SCAM_TYPES = {
    "假冒銀行客服", "投資詐騙", "假冒政府機關", "愛情詐騙",
    "購物詐騙", "中獎詐騙", "工作詐騙", "AI 深偽詐騙",
}

# 合法的台灣縣市白名單
_VALID_REGIONS = {
    "台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市",
    "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣",
    "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣",
    "台東縣", "澎湖縣", "金門縣", "連江縣",
}

_SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}

# httpx Client 共用設定：停用 SSL 憑證驗證（政府/新聞網站常有本機憑證鏈問題）
_CLIENT_KWARGS: dict = {
    "timeout": _SCRAPE_TIMEOUT,
    "headers": _SCRAPE_HEADERS,
    "follow_redirects": True,
    "verify": False,
}


# ── 主入口 ────────────────────────────────────────────────────────────────────

def scrape_all_sources() -> NormalizedData | None:
    """依序嘗試所有爬蟲來源，第一個成功即回傳。全部失敗回傳 None。"""
    # 第一層：自由時報詐騙統計新聞（靜態 HTML，Regex 直接萃取）
    result = _scrape_ltn_news()
    if result is not None:
        logger.info("爬蟲成功：自由時報詐騙統計新聞（第一層）")
        return result

    # 第二層：165 官網首頁文字
    result = _scrape_npa_165()
    if result is not None:
        logger.info("爬蟲成功：165.npa.gov.tw（第二層）")
        return result

    # 第三層：Google News + LLM
    result = _scrape_news_with_llm()
    if result is not None:
        logger.info("爬蟲成功：Google News + LLM 解析（第三層）")
        return result

    logger.warning("所有爬蟲來源均失敗")
    return None


# ── 第一層：自由時報詐騙統計新聞 ─────────────────────────────────────────────

def _scrape_ltn_news() -> NormalizedData | None:
    """
    爬取自由時報詐騙統計新聞搜尋結果。

    自由時報搜尋頁有靜態 HTML，文章摘要中直接包含案件數與損失金額，
    例如「2024年全國詐騙案件11萬8535件、財損金額48億」。
    用 Regex 從文字中萃取年度統計數字。
    """
    current_year = datetime.now().year
    # 同時搜目前年和前一年，確保有足夠文章含統計數字
    keyword = f"詐騙 統計 165 {current_year - 1} {current_year}"
    try:
        with httpx.Client(**_CLIENT_KWARGS) as client:
            resp = client.get(_LTN_SEARCH_URL, params={"keyword": keyword})
            if resp.status_code != 200:
                logger.warning("自由時報搜尋回傳 HTTP %d", resp.status_code)
                return None

        return _extract_stats_from_ltn(resp.text, current_year)
    except Exception as exc:
        logger.warning("自由時報爬取失敗：%s", exc)
        return None


def _extract_stats_from_ltn(html: str, current_year: int) -> NormalizedData | None:
    """從自由時報搜尋結果 HTML 萃取年度詐騙統計。"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(separator="\n", strip=True)
    except Exception:
        text = re.sub(r"<[^>]+>", " ", html)

    # 萃取「XXXX年全國詐騙案件 N 件/萬N件」
    # 例：「2024年全國詐騙案件11萬8535件」「2024年詐騙案件達83,000件」
    annual_stats: dict[str, AnnualStat] = {}

    # 模式 1：「YYYY年…N萬N件」或「N萬件」（尾數可為零）
    for m in re.finditer(
        r"(20\d{2})\s*年[^。\n]{0,30}?(\d+)\s*萬\s*(\d{0,4})\s*件",
        text,
    ):
        year = m.group(1)
        wan = int(m.group(2))
        rest = int(m.group(3)) if m.group(3) else 0
        cases = wan * 10000 + rest
        if 10000 < cases < 500000:
            annual_stats[year] = AnnualStat(total_cases=cases, total_loss_billion=0.0)
            logger.info("LTN 萃取：%s年 %d 件（萬+尾數模式）", year, cases)

    # 模式 2：「YYYY年…N,NNN件」（有逗號）
    for m in re.finditer(
        r"(20\d{2})\s*年[^。\n]{0,30}?(\d{1,3}(?:,\d{3})+)\s*件",
        text,
    ):
        year = m.group(1)
        cases = int(m.group(2).replace(",", ""))
        if 10000 < cases < 500000 and year not in annual_stats:
            annual_stats[year] = AnnualStat(total_cases=cases, total_loss_billion=0.0)
            logger.info("LTN 萃取：%s年 %d 件（逗號模式）", year, cases)

    # 萃取損失金額「YYYY年…N億」配對
    for m in re.finditer(
        r"(20\d{2})\s*年[^。\n]{0,50}?財損[^。\n]{0,20}?(\d+(?:\.\d+)?)\s*億",
        text,
    ):
        year, loss = m.group(1), float(m.group(2))
        if year in annual_stats and loss > 0:
            annual_stats[year] = AnnualStat(
                total_cases=annual_stats[year].total_cases,
                total_loss_billion=loss,
            )
            logger.info("LTN 萃取：%s年損失 %.1f 億", year, loss)

    # 備用：「財損金額NNN億」不帶年份，附加到最大案件數的年份
    if annual_stats:
        latest_year = max(annual_stats.keys())
        if annual_stats[latest_year].total_loss_billion == 0.0:
            loss_matches = re.findall(r"財損[^。\n]{0,20}?(\d+(?:\.\d+)?)\s*億", text)
            if loss_matches:
                annual_stats[latest_year] = AnnualStat(
                    total_cases=annual_stats[latest_year].total_cases,
                    total_loss_billion=float(loss_matches[0]),
                )

    if not annual_stats:
        logger.warning("LTN 未萃取到有效年度統計")
        return None

    # 萃取熱詞（新聞標題中的詐騙關鍵詞）
    hotwords: dict[str, int] = {}
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        for tag in soup.find_all(["h2", "h3", "a"]):
            t = tag.get_text(strip=True)
            for kw in ["假冒", "投資", "詐騙", "釣魚", "AI語音", "深偽", "語音", "洗錢"]:
                if kw in t:
                    hotwords[kw] = hotwords.get(kw, 0) + 1
    except Exception:
        pass

    now = datetime.now(timezone.utc)
    return NormalizedData(
        scam_cases_by_region={},
        scam_type_stats={},
        monthly_trend=[],
        victim_age_distribution={},
        annual_stats=annual_stats,
        source_name="scraper:ltn-news",
        fetched_at=now,
        hotwords=hotwords,
        real_scam_scripts=[],
    )


# ── 第二層：165 官網 ──────────────────────────────────────────────────────────

def _scrape_npa_165() -> NormalizedData | None:
    """爬取 165.npa.gov.tw 首頁，嘗試萃取文字中的統計數字。"""
    try:
        with httpx.Client(**_CLIENT_KWARGS) as client:
            resp = client.get(_NPA_165_URL)
            if resp.status_code != 200:
                logger.warning("165.npa.gov.tw 回傳 HTTP %d", resp.status_code)
                return None
        return _extract_stats_from_html(resp.text, "165.npa.gov.tw")
    except Exception as exc:
        logger.warning("165.npa.gov.tw 爬取失敗：%s", exc)
        return None


def _extract_stats_from_html(html: str, source_name: str) -> NormalizedData | None:
    """通用：從 HTML 頁面中提取詐騙統計數據（適用表格型靜態網頁）。"""
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
                    if num_match and label in _VALID_REGIONS:
                        regions[label] = int(num_match.group(1).replace(",", ""))
                        break
                    if num_match and label in _VALID_SCAM_TYPES:
                        scam_type_stats[label] = ScamTypeStat(
                            cases=int(num_match.group(1).replace(",", "")),
                            avg_loss_ntd=0, trend="穩定",
                        )
                        break

    text = soup.get_text(separator=" ", strip=True)
    numbers = re.findall(r"(\d{1,3}(?:,\d{3})*)\s*(?:件|案|筆)", text)
    amounts = re.findall(r"(\d+(?:\.\d+)?)\s*(?:億)", text)

    hotwords: dict[str, int] = {}
    for tag in soup.find_all(["a", "h1", "h2", "h3", "h4", "strong", "b"]):
        t = tag.get_text(strip=True)
        if 2 <= len(t) <= 10 and any(kw in t for kw in ["詐騙", "投資", "銀行", "客服", "帳戶"]):
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
        annual_stats={
            str(current_year): AnnualStat(total_cases=total_cases, total_loss_billion=total_loss)
        } if total_cases > 0 else {},
        source_name=f"scraper:{source_name}",
        fetched_at=now,
        hotwords=hotwords,
        real_scam_scripts=[],
    )


# ── 第三層：Google News + LLM ─────────────────────────────────────────────────

def _scrape_news_with_llm() -> NormalizedData | None:
    """搜尋 Google News 並用 LLM 解析（同步）。"""
    try:
        news_text = _fetch_news_snippets()
        if not news_text:
            return None
        return _llm_extract_stats(news_text)
    except Exception as exc:
        logger.warning("新聞 + LLM 解析失敗：%s", exc)
        return None


def _fetch_news_snippets() -> str | None:
    """從 Google News 搜尋台灣詐騙統計相關新聞（同步）。"""
    current_year = datetime.now().year
    query = f"台灣 詐騙 統計 {current_year} 億"
    try:
        with httpx.Client(**_CLIENT_KWARGS) as client:
            params = {"q": query, "hl": "zh-TW", "gl": "TW", "ceid": "TW:zh-Hant"}
            resp = client.get(_GOOGLE_NEWS_SEARCH, params=params)
            if resp.status_code != 200:
                logger.warning("Google News 回傳 HTTP %d", resp.status_code)
                return None
            text = _strip_html_tags(resp.text)
            return text[:4000] if text else None
    except Exception as exc:
        logger.warning("Google News 搜尋失敗：%s", exc)
        return None


def _strip_html_tags(html: str) -> str:
    """移除 HTML 標籤。"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator=" ", strip=True)
    except ImportError:
        return re.sub(r"<[^>]+>", " ", html)


def _llm_extract_stats(news_text: str) -> NormalizedData | None:
    """使用 LLM 從新聞文本中提取統計數據（同步）。"""
    try:
        from app.config import get_settings
        settings = get_settings()
        current_year = datetime.now().year

        prompt = (
            f"以下是關於台灣詐騙統計的新聞摘要。請只從文字中提取明確出現的數字，"
            f"不要推測或捏造，以 JSON 格式回傳：\n"
            f"1. total_cases: 某年度總案件數（整數，需超過 10000）\n"
            f"2. total_loss_billion: 某年度總損失金額（億元，浮點數）\n"
            f"3. year: 對應年份（如 2024）\n"
            f"找不到請填 0 或 null，只回傳 JSON。\n\n"
            f"新聞摘要：\n{news_text[:3000]}"
        )

        llm_response = None
        if settings.llm_provider == "ollama":
            llm_response = _call_ollama_direct_sync(settings.ollama_model, prompt)
        elif settings.llm_provider == "openai" and settings.openai_api_key:
            try:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model=settings.openai_model,
                    api_key=settings.openai_api_key,
                    temperature=0,
                )
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
    """直接透過同步 HTTP 呼叫 Ollama API。"""
    try:
        with httpx.Client(timeout=60, verify=False) as client:
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
    """解析 LLM 回傳的 JSON，只接受合理範圍的數字。"""
    import json as _json

    json_match = re.search(r"\{[\s\S]*?\}", response)
    if not json_match:
        return None

    try:
        data = _json.loads(json_match.group())
    except _json.JSONDecodeError:
        return None

    now = datetime.now(timezone.utc)
    total_cases = data.get("total_cases") or 0
    total_loss = data.get("total_loss_billion") or 0.0
    year = str(data.get("year") or current_year)

    # 合理性驗證：案件數必須在合理範圍
    if not (10000 < int(total_cases) < 500000):
        total_cases = 0

    annual_stats: dict[str, AnnualStat] = {}
    if total_cases > 0:
        annual_stats[year] = AnnualStat(
            total_cases=int(total_cases),
            total_loss_billion=float(total_loss),
        )

    if not annual_stats:
        return None

    return NormalizedData(
        scam_cases_by_region={},
        scam_type_stats={},
        monthly_trend=[],
        victim_age_distribution={},
        annual_stats=annual_stats,
        source_name="scraper:news+llm",
        fetched_at=now,
        hotwords={},
        real_scam_scripts=[],
    )
