"""
詐騙話術生成引擎核心模組

負責呼叫 LLM 生成詐騙話術變種樣本，包含：
- LangChain Prompt 模板定義
- 指數退避重試邏輯
- LLM 逾時與 API 錯誤處理
- 結構化錯誤回應格式

需求：1.1、1.2、1.3
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import get_settings

# 確保 .env 已載入再取得設定（必須在 get_settings() 之前）
from dotenv import load_dotenv
load_dotenv()

def _build_llm_client():
    """根據 LLM_PROVIDER 設定建立對應的 LLM 客戶端"""
    s = get_settings()
    if s.llm_provider == "ollama":
        # 使用本地 Ollama（OpenAI 相容 API）
        return ChatOpenAI(
            model=s.ollama_model,
            base_url="http://localhost:11434/v1",
            api_key="ollama",  # Ollama 不需要真實 key，但欄位不能空
            temperature=0.9,
        )
    elif s.llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=s.google_model,
            google_api_key=s.google_api_key,
            temperature=0.9,
        )
    else:
        return ChatOpenAI(
            model=s.openai_model,
            api_key=s.openai_api_key,
            temperature=0.9,
        )

logger = logging.getLogger(__name__)
settings = get_settings()


# ── 錯誤代碼常數 ──────────────────────────────────────────────────────────────

class LLMErrorCode:
    """LLM 錯誤代碼常數定義"""
    TIMEOUT = "LLM_TIMEOUT"
    """LLM API 回應逾時（> 60 秒）"""

    API_ERROR = "LLM_API_ERROR"
    """LLM API 回傳錯誤（4xx / 5xx）"""

    PARSE_ERROR = "LLM_PARSE_ERROR"
    """LLM 回應無法解析為預期 JSON 格式"""

    UNKNOWN_ERROR = "LLM_UNKNOWN_ERROR"
    """未預期的未知錯誤"""


# ── 詐騙樣本資料結構 ──────────────────────────────────────────────────────────

class ScamSample:
    """
    單一詐騙話術樣本

    包含話術文本、心理操控類別標籤與目標受眾描述。
    """

    def __init__(
        self,
        content: str,
        psychological_tags: list[str],
        target_audience: str,
    ) -> None:
        """
        初始化詐騙樣本

        Args:
            content: 詐騙話術文本（非空）
            psychological_tags: 心理操控類別標籤列表（非空）
            target_audience: 目標受眾描述（非空）
        """
        self.content = content
        self.psychological_tags = psychological_tags
        self.target_audience = target_audience

    def to_dict(self) -> dict[str, Any]:
        """轉換為字典格式"""
        return {
            "content": self.content,
            "psychological_tags": self.psychological_tags,
            "target_audience": self.target_audience,
        }


# ── Prompt 模板定義 ───────────────────────────────────────────────────────────

# 系統提示詞：限定 LLM 角色與輸出格式
_SYSTEM_PROMPT = """你是一個專業的詐騙話術分析研究員，協助防詐機構研究詐騙手法。
你的任務是根據給定的詐騙情境，生成多種不同語氣與手法的詐騙對話樣本，
供防詐系統訓練與研究使用。

請嚴格按照以下 JSON 格式輸出，不要包含任何其他文字：
{{
  "samples": [
    {{
      "content": "詐騙話術文本（至少 50 字）",
      "psychological_tags": ["心理操控類別標籤1", "心理操控類別標籤2"],
      "target_audience": "目標受眾描述"
    }}
  ]
}}

心理操控類別標籤必須從以下五類中選擇（可多選）：
- 信任建立
- 緊迫感製造
- 情緒勒索
- 權威偽裝
- 利益誘導

請確保：
1. 生成至少 {min_samples} 種具備不同語氣與手法的樣本
2. 每個樣本的話術文本（content）非空且具體
3. 每個樣本至少包含一個心理操控類別標籤
4. 每個樣本的目標受眾描述非空且具體
5. 不同樣本之間的語氣、手法、切入角度應有明顯差異"""

# 使用者提示詞：提供具體情境參數
_HUMAN_PROMPT = """請根據以下情境生成詐騙話術樣本：

詐騙情境：{scenario}
目標受眾特徵：{target_audience}
需要生成樣本數量：至少 {min_samples} 種

請確保每種樣本使用不同的語氣與詐騙手法，涵蓋多種心理操控策略。"""

# 建立 LangChain ChatPromptTemplate
SCAM_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessage(content=_SYSTEM_PROMPT),
    HumanMessage(content=_HUMAN_PROMPT),
])


# ── 結構化錯誤回應建構函數 ────────────────────────────────────────────────────

def build_error_response(
    error_code: str,
    description: str,
    request_id: str | None = None,
    retry_after: int | None = None,
) -> dict[str, Any]:
    """
    建構結構化錯誤回應

    Args:
        error_code: 錯誤代碼（如 LLM_TIMEOUT、LLM_API_ERROR）
        description: 錯誤描述（人類可讀）
        request_id: 請求識別碼（若未提供則自動生成）
        retry_after: 建議重試等待秒數（可選）

    Returns:
        包含 error_code、description、timestamp、request_id 的字典
    """
    response: dict[str, Any] = {
        "error_code": error_code,
        "description": description,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id or str(uuid.uuid4()),
    }
    if retry_after is not None:
        response["retry_after"] = retry_after
    return response


# ── 指數退避重試邏輯 ──────────────────────────────────────────────────────────

async def _call_llm_with_retry(
    llm: ChatOpenAI,
    messages: list,
    request_id: str,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    max_delay: float = 30.0,
) -> str:
    """
    帶指數退避重試的 LLM 呼叫

    Args:
        llm: LangChain LLM 客戶端
        messages: 訊息列表
        request_id: 請求識別碼（用於日誌）
        max_attempts: 最大重試次數（預設 3）
        initial_delay: 初始延遲秒數（預設 1.0）
        backoff_multiplier: 退避倍數（預設 2.0）
        max_delay: 最大延遲秒數（預設 30.0）

    Returns:
        LLM 回傳的文字內容

    Raises:
        asyncio.TimeoutError: LLM 回應逾時
        Exception: LLM API 錯誤（重試耗盡後）
    """
    delay = initial_delay
    last_exception: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(
                "LLM 呼叫嘗試 %d/%d | request_id=%s",
                attempt, max_attempts, request_id
            )
            # 使用 asyncio.wait_for 強制逾時限制
            response = await asyncio.wait_for(
                llm.ainvoke(messages),
                timeout=settings.llm_timeout_seconds,
            )
            logger.info("LLM 呼叫成功 | request_id=%s | attempt=%d", request_id, attempt)
            return response.content

        except asyncio.TimeoutError as exc:
            # 逾時錯誤：直接拋出，不重試（逾時本身已耗費大量時間）
            logger.error(
                "LLM 呼叫逾時（> %ds）| request_id=%s | attempt=%d",
                settings.llm_timeout_seconds, request_id, attempt
            )
            raise asyncio.TimeoutError(
                f"LLM 服務在 {settings.llm_timeout_seconds} 秒內未回應"
            ) from exc

        except Exception as exc:
            last_exception = exc
            logger.warning(
                "LLM 呼叫失敗 | request_id=%s | attempt=%d | error=%s: %s",
                request_id, attempt, type(exc).__name__, str(exc)
            )

            if attempt < max_attempts:
                # 計算下次重試延遲（指數退避，不超過 max_delay）
                actual_delay = min(delay, max_delay)
                logger.info(
                    "等待 %.1f 秒後重試 | request_id=%s",
                    actual_delay, request_id
                )
                await asyncio.sleep(actual_delay)
                delay *= backoff_multiplier
            else:
                logger.error(
                    "LLM 呼叫已達最大重試次數 %d | request_id=%s",
                    max_attempts, request_id
                )

    # 重試耗盡，拋出最後一次例外
    raise last_exception or RuntimeError("LLM 呼叫失敗，原因未知")


# ── JSON 解析輔助函數 ─────────────────────────────────────────────────────────

def _parse_llm_response(raw_content: str) -> list[dict[str, Any]]:
    """
    解析 LLM 回傳的 JSON 內容

    嘗試從 LLM 回應中提取 JSON 結構，支援回應中包含額外文字的情況。

    Args:
        raw_content: LLM 回傳的原始文字

    Returns:
        詐騙樣本字典列表

    Raises:
        ValueError: 無法解析 JSON 或格式不符預期
    """
    # 嘗試直接解析
    try:
        data = json.loads(raw_content)
        if "samples" in data and isinstance(data["samples"], list):
            return data["samples"]
    except json.JSONDecodeError:
        pass

    # 嘗試從文字中提取 JSON 區塊（處理 LLM 可能加入說明文字的情況）
    import re
    json_pattern = re.search(r'\{[\s\S]*"samples"[\s\S]*\}', raw_content)
    if json_pattern:
        try:
            data = json.loads(json_pattern.group())
            if "samples" in data and isinstance(data["samples"], list):
                return data["samples"]
        except json.JSONDecodeError:
            pass

    raise ValueError(f"無法從 LLM 回應中解析 JSON 格式，原始內容：{raw_content[:200]}...")


def _validate_samples(raw_samples: list[dict[str, Any]]) -> list[ScamSample]:
    """
    驗證並轉換詐騙樣本列表

    Args:
        raw_samples: 從 LLM 回應解析的原始樣本列表

    Returns:
        驗證通過的 ScamSample 列表

    Raises:
        ValueError: 樣本格式不符預期
    """
    validated: list[ScamSample] = []
    for i, sample in enumerate(raw_samples):
        content = sample.get("content", "").strip()
        tags = sample.get("psychological_tags", [])
        audience = sample.get("target_audience", "").strip()

        # 驗證必要欄位非空
        if not content:
            logger.warning("樣本 %d 的 content 欄位為空，跳過", i)
            continue
        if not tags or not isinstance(tags, list):
            logger.warning("樣本 %d 的 psychological_tags 欄位無效，跳過", i)
            continue
        if not audience:
            logger.warning("樣本 %d 的 target_audience 欄位為空，跳過", i)
            continue

        validated.append(ScamSample(
            content=content,
            psychological_tags=[str(t) for t in tags if t],
            target_audience=audience,
        ))

    return validated


# ── 主要生成函數 ──────────────────────────────────────────────────────────────

async def generate_scam_samples(
    scenario: str,
    target_audience: str,
    min_samples: int = 10,
    request_id: str | None = None,
    llm_client: ChatOpenAI | None = None,
) -> dict[str, Any]:
    """
    生成詐騙話術樣本（主要入口函數）

    呼叫 LLM 生成至少 min_samples 種不同語氣與手法的詐騙對話樣本。
    包含指數退避重試邏輯與完整錯誤處理。

    Args:
        scenario: 基礎詐騙情境描述（非空）
        target_audience: 目標受眾特徵描述（非空）
        min_samples: 最少生成樣本數量（預設 10，符合需求 1.1）
        request_id: 請求識別碼（若未提供則自動生成）
        llm_client: LLM 客戶端（若未提供則使用設定建立）

    Returns:
        成功時：{"samples": [ScamSample.to_dict(), ...], "count": int, "request_id": str}
        失敗時：{"error_code": str, "description": str, "timestamp": str, "request_id": str}

    需求：1.1、1.2、1.3
    """
    req_id = request_id or str(uuid.uuid4())

    # 建立 LLM 客戶端（若未提供）
    if llm_client is None:
        llm_client = _build_llm_client()

    # 建構 Prompt 訊息
    prompt_messages = [
        SystemMessage(content=_SYSTEM_PROMPT.format(min_samples=min_samples)),
        HumanMessage(content=_HUMAN_PROMPT.format(
            scenario=scenario,
            target_audience=target_audience,
            min_samples=min_samples,
        )),
    ]

    try:
        # 呼叫 LLM（含指數退避重試）
        raw_content = await _call_llm_with_retry(
            llm=llm_client,
            messages=prompt_messages,
            request_id=req_id,
            max_attempts=settings.llm_max_retries,
            initial_delay=settings.llm_retry_initial_delay,
            backoff_multiplier=settings.llm_retry_backoff_multiplier,
            max_delay=settings.llm_retry_max_delay,
        )

        # 解析 LLM 回應
        raw_samples = _parse_llm_response(raw_content)
        validated_samples = _validate_samples(raw_samples)

        logger.info(
            "詐騙樣本生成完成 | request_id=%s | count=%d",
            req_id, len(validated_samples)
        )

        return {
            "samples": [s.to_dict() for s in validated_samples],
            "count": len(validated_samples),
            "request_id": req_id,
        }

    except asyncio.TimeoutError:
        # LLM 逾時錯誤（需求 1.3）
        logger.error("LLM 逾時錯誤 | request_id=%s", req_id)
        return build_error_response(
            error_code=LLMErrorCode.TIMEOUT,
            description=f"LLM 服務在 {settings.llm_timeout_seconds} 秒內未回應，請稍後重試",
            request_id=req_id,
            retry_after=settings.llm_retry_max_delay,
        )

    except ValueError as exc:
        # JSON 解析錯誤（需求 1.3）
        logger.error("LLM 回應解析失敗 | request_id=%s | error=%s", req_id, str(exc))
        return build_error_response(
            error_code=LLMErrorCode.PARSE_ERROR,
            description=f"LLM 回應格式無效，無法解析為預期的 JSON 結構：{str(exc)}",
            request_id=req_id,
        )

    except Exception as exc:
        # 其他 API 錯誤（需求 1.3）
        error_type = type(exc).__name__
        logger.error(
            "LLM API 錯誤 | request_id=%s | error_type=%s | error=%s",
            req_id, error_type, str(exc)
        )

        # 判斷是否為 OpenAI API 錯誤
        error_code = LLMErrorCode.API_ERROR
        description = f"LLM API 呼叫失敗（{error_type}）：{str(exc)}"

        return build_error_response(
            error_code=error_code,
            description=description,
            request_id=req_id,
        )
