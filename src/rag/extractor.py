"""
TrustAgent.Forensics — Threshold Extractor từ văn bản luật (RAG Module)

Nhiệm vụ: Đọc văn bản luật và trích xuất các con số ngưỡng (threshold)
thành dict Python để đưa vào Z3 BusinessRule.

Chiến lược extraction 3 tầng:
  1. JSON block extraction (regex từ markdown) — nhanh, 100% reliable
  2. Pattern-based extraction (regex từ text thường) — fallback khi không có JSON
  3. Hardcoded defaults — không bao giờ fail

Tại sao không dùng LLM cho extraction?
  - Các legal docs đã được structed với JSON metadata block rõ ràng
  - Regex đáng tin cậy hơn LLM cho việc extract số từ văn bản có cấu trúc
  - LLM extraction có thể dùng nếu muốn (xem GeminiThresholdExtractor bên dưới)
  - Tránh dependency vào API key cho một chức năng có thể làm bằng regex
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Default thresholds — dùng khi extraction fail ở mọi tầng
# ─────────────────────────────────────────────────────────────────────────────
FALLBACK_THRESHOLDS: dict[str, dict[str, int]] = {
    "vn_payment": {
        "VN_CASH_THRESHOLD": 20_000_000,      # Thông tư 96/2015/TT-BTC
    },
    "kr_tax_refund": {
        "KR_MIN_RECEIPT_AMOUNT": 30_000,       # Korea Tax Refund, 30,000 KRW
        "KR_CUSTOMS_CHECK_THRESHOLD": 75_000,  # Korea Tax Refund, 75,000 KRW
    },
}

# Các pattern regex để extract threshold từ text thường (nếu không có JSON block)
_VN_REGEX_PATTERNS: list[tuple[str, str]] = [
    # Pattern: "VN_CASH_THRESHOLD = 20000000" hoặc "20,000,000 VNĐ"
    (r"VN_CASH_THRESHOLD\s*=\s*(\d[\d,]*)", "VN_CASH_THRESHOLD"),
    (r"Ngưỡng.*?:\s*([\d,]+)\s*VN[ĐD]", "VN_CASH_THRESHOLD"),
    (r"(\d{2,}[\d,]*)\s*(?:triệu|million).*?tiền mặt", "VN_CASH_THRESHOLD"),
]

_KR_REGEX_PATTERNS: list[tuple[str, str]] = [
    (r"KR_MIN_RECEIPT_AMOUNT\s*=\s*(\d[\d,]*)", "KR_MIN_RECEIPT_AMOUNT"),
    (r"KR_CUSTOMS_CHECK_THRESHOLD\s*=\s*(\d[\d,]*)", "KR_CUSTOMS_CHECK_THRESHOLD"),
    (r"최소 구매 기준금액:\s*([\d,]+)\s*KRW", "KR_MIN_RECEIPT_AMOUNT"),
    (r"세관 검사 기준:\s*([\d,]+)\s*KRW", "KR_CUSTOMS_CHECK_THRESHOLD"),
]


class ThresholdExtractor:
    """
    Trích xuất các giá trị ngưỡng từ văn bản luật đã được RAG retrieve.

    Input:  Văn bản luật (str) + scenario_type (str)
    Output: dict[str, int] — ví dụ: {"VN_CASH_THRESHOLD": 20000000}

    Sử dụng:
        extractor = ThresholdExtractor()
        thresholds = extractor.extract("vn_payment", legal_text)
        # → {"VN_CASH_THRESHOLD": 20000000}
    """

    def extract(self, scenario_type: str, legal_text: str) -> dict[str, int]:
        """
        Trích xuất threshold từ văn bản luật.

        Args:
            scenario_type: "vn_payment" | "kr_tax_refund"
            legal_text: Văn bản luật từ RAG retriever

        Returns:
            dict với tên threshold → giá trị int
            Luôn trả về dict hợp lệ (dùng fallback nếu cần)
        """
        if not legal_text or not legal_text.strip():
            logger.warning(f"[Extractor] Văn bản rỗng cho {scenario_type} → dùng fallback")
            return self._get_fallback(scenario_type)

        # Tầng 1: JSON block extraction
        result = self._extract_from_json_block(legal_text, scenario_type)
        if result:
            logger.info(f"[Extractor] JSON extraction thành công cho {scenario_type}: {result}")
            return result

        # Tầng 2: Pattern-based regex extraction
        result = self._extract_from_patterns(legal_text, scenario_type)
        if result:
            logger.info(f"[Extractor] Regex extraction thành công cho {scenario_type}: {result}")
            return result

        # Tầng 3: Fallback defaults
        logger.warning(f"[Extractor] Không extract được → dùng hardcoded fallback cho {scenario_type}")
        return self._get_fallback(scenario_type)

    # ─────────────────────────────────────────────────────────────────────────
    # Tầng 1: JSON block extraction
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_from_json_block(self, text: str, scenario_type: str) -> dict[str, int] | None:
        """
        Tìm ```json {...} ``` block trong markdown và parse thresholds từ đó.

        Đây là phương pháp đáng tin cậy nhất — legal docs được thiết kế
        với JSON metadata block rõ ràng.
        """
        # Tìm tất cả JSON blocks trong document
        json_blocks = re.findall(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)

        for block_str in json_blocks:
            try:
                data: dict[str, Any] = json.loads(block_str)
            except json.JSONDecodeError:
                continue

            extracted: dict[str, int] = {}

            if scenario_type == "vn_payment":
                # Tìm VN_CASH_THRESHOLD
                value = self._find_nested_value(data, "VN_CASH_THRESHOLD")
                if value is not None:
                    extracted["VN_CASH_THRESHOLD"] = int(value)
                elif "threshold_value" in data and data.get("scenario") == "vn_payment":
                    extracted["VN_CASH_THRESHOLD"] = int(data["threshold_value"])

            elif scenario_type == "kr_tax_refund":
                # Tìm KR thresholds (có thể nested trong "thresholds" key)
                thresholds_obj = data.get("thresholds", data)
                kr_min = self._find_nested_value(thresholds_obj, "KR_MIN_RECEIPT_AMOUNT")
                kr_customs = self._find_nested_value(thresholds_obj, "KR_CUSTOMS_CHECK_THRESHOLD")
                if kr_min is not None:
                    extracted["KR_MIN_RECEIPT_AMOUNT"] = int(kr_min)
                if kr_customs is not None:
                    extracted["KR_CUSTOMS_CHECK_THRESHOLD"] = int(kr_customs)

            if extracted:
                return extracted

        return None

    # ─────────────────────────────────────────────────────────────────────────
    # Tầng 2: Pattern-based regex extraction
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_from_patterns(self, text: str, scenario_type: str) -> dict[str, int] | None:
        """
        Dùng regex patterns để extract threshold từ text thường.
        Xử lý được dấu phẩy trong số (ví dụ: "20,000,000").
        """
        patterns = []
        if scenario_type == "vn_payment":
            patterns = _VN_REGEX_PATTERNS
        elif scenario_type == "kr_tax_refund":
            patterns = _KR_REGEX_PATTERNS

        extracted: dict[str, int] = {}
        for pattern, key in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
            if match:
                raw = match.group(1).replace(",", "").replace(".", "")
                try:
                    extracted[key] = int(raw)
                except ValueError:
                    continue

        # Chỉ trả về nếu có ít nhất 1 giá trị
        return extracted if extracted else None

    # ─────────────────────────────────────────────────────────────────────────
    # Tầng 3: Fallback defaults
    # ─────────────────────────────────────────────────────────────────────────

    def _get_fallback(self, scenario_type: str) -> dict[str, int]:
        """Trả về hardcoded defaults. Không bao giờ raise Exception."""
        defaults = FALLBACK_THRESHOLDS.get(scenario_type, {})
        if not defaults:
            logger.error(f"[Extractor] Không có fallback cho scenario: {scenario_type}")
        return dict(defaults)  # copy để tránh mutation

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _find_nested_value(obj: dict | Any, key: str) -> int | None:
        """Tìm key trong dict, hỗ trợ nested dict."""
        if isinstance(obj, dict):
            if key in obj:
                return obj[key]
            for v in obj.values():
                result = ThresholdExtractor._find_nested_value(v, key)
                if result is not None:
                    return result
        return None
