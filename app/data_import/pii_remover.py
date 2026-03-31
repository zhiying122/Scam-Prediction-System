"""
PII 去識別化處理模組

在報案資料進入分析流程前，自動偵測並移除個人識別資訊（PII），
包含姓名、電話、身分證字號、地址、電子郵件等敏感資訊。

需求：7.3
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ── PII 偵測正規表達式 ────────────────────────────────────────────────────────

# 電子郵件（RFC 5322 簡化版）
_EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

# 台灣手機號碼（09xx-xxxxxx 或 09xxxxxxxx）
_TW_MOBILE_PATTERN = re.compile(
    r"09\d{2}[-\s]?\d{3}[-\s]?\d{3}|09\d{8}",
)

# 台灣市話（02-xxxx-xxxx、03-xxx-xxxx 等）
_TW_PHONE_PATTERN = re.compile(
    r"0[2-8]\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}",
)

# 台灣身分證字號（一個英文字母 + 9 個數字）
_TW_ID_PATTERN = re.compile(
    r"\b[A-Z][12]\d{8}\b",
)

# 電子郵件（已在上方定義，此處為別名）
_EMAIL_RE = _EMAIL_PATTERN

# 台灣地址（含縣市、鄉鎮市區、路街巷弄號）
# 支援「台北市信義區信義路五段7號」等格式
_TW_ADDRESS_PATTERN = re.compile(
    r"(?:台灣|臺灣)?"
    r"(?:[\u4e00-\u9fff]{2,3}(?:縣|市))"
    r"(?:[\u4e00-\u9fff]{2,4}(?:市|區|鄉|鎮))?"
    r"[\u4e00-\u9fff\w]*?(?:路|街|大道|巷|弄)"
    r"(?:[\u4e00-\u9fff\d]+段)?"
    r"\d+號(?:\d+樓)?",
)

# 中文姓名（2~4 個中文字，前後有空白或標點符號）
# 使用較保守的模式，避免誤判一般詞彙
_CN_NAME_PATTERN = re.compile(
    r"(?:姓名[：:是為]?\s*|稱呼[：:是為]?\s*|叫做?\s*|名字[：:是為]?\s*)"
    r"([^\s，。、！？,\.!?]{2,4})",
)

# 替換佔位符
_PLACEHOLDER_EMAIL = "[EMAIL]"
_PLACEHOLDER_PHONE = "[PHONE]"
_PLACEHOLDER_ID = "[ID_NUMBER]"
_PLACEHOLDER_ADDRESS = "[ADDRESS]"
_PLACEHOLDER_NAME = "[NAME]"


class PiiRemover:
    """
    PII 去識別化處理器

    自動偵測並移除文字中的個人識別資訊，
    以佔位符替換敏感資料，並設定 pii_removed 標記。
    """

    def remove_from_text(self, text: str) -> tuple[str, bool]:
        """
        對單一文字欄位執行 PII 去識別化

        Args:
            text: 原始文字內容

        Returns:
            (去識別化後的文字, 是否偵測到 PII)
        """
        if not text:
            return text, False

        original = text
        result = text

        # 依序套用各 PII 偵測規則
        result = _EMAIL_PATTERN.sub(_PLACEHOLDER_EMAIL, result)
        result = _TW_MOBILE_PATTERN.sub(_PLACEHOLDER_PHONE, result)
        result = _TW_PHONE_PATTERN.sub(_PLACEHOLDER_PHONE, result)
        result = _TW_ID_PATTERN.sub(_PLACEHOLDER_ID, result)
        result = _TW_ADDRESS_PATTERN.sub(_PLACEHOLDER_ADDRESS, result)
        result = _CN_NAME_PATTERN.sub(
            lambda m: m.group(0).replace(m.group(1), _PLACEHOLDER_NAME),
            result,
        )

        pii_detected = result != original
        return result, pii_detected

    def remove_from_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """
        對單筆報案資料記錄執行 PII 去識別化

        處理 description、source 等文字欄位，
        並將 pii_removed 設為 True。

        Args:
            record: 原始報案資料記錄字典

        Returns:
            去識別化後的記錄字典（pii_removed 設為 True）
        """
        result = dict(record)
        any_pii_found = False

        # 對所有字串欄位執行去識別化
        text_fields = ["description", "source", "scam_type"]
        for field in text_fields:
            value = result.get(field)
            if isinstance(value, str):
                cleaned, pii_found = self.remove_from_text(value)
                result[field] = cleaned
                if pii_found:
                    any_pii_found = True

        # 設定去識別化標記
        result["pii_removed"] = True

        if any_pii_found:
            logger.info(
                "批次 %s 中偵測到 PII 並已完成去識別化",
                result.get("import_batch_id", "unknown"),
            )

        return result

    def remove_from_batch(
        self, records: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        對整批報案資料執行 PII 去識別化

        Args:
            records: 原始報案資料記錄列表

        Returns:
            去識別化後的記錄列表（所有記錄的 pii_removed 均為 True）
        """
        cleaned = [self.remove_from_record(r) for r in records]
        logger.info("PII 去識別化完成：共處理 %d 筆資料", len(cleaned))
        return cleaned

    def contains_pii(self, text: str) -> bool:
        """
        偵測文字是否包含 PII（不執行替換）

        Args:
            text: 要檢查的文字

        Returns:
            True 若偵測到 PII，否則 False
        """
        if not text:
            return False
        _, detected = self.remove_from_text(text)
        return detected
