"""
TrustAgent.Forensics — Gemini Semantic Parser

Đây là cầu nối giữa lớp Neural (LLM) và lớp Symbolic (Z3).

Luồng xử lý:
  1. Nhận câu yêu cầu bằng ngôn ngữ tự nhiên (tiếng Việt / Anh)
  2. Gọi Gemini 2.0 Flash để phát hiện loại kịch bản
  3. Gọi Gemini lần 2 để trích xuất dữ liệu có cấu trúc (JSON)
  4. Validate JSON bằng Pydantic
  5. Trả về ParseResult sẵn sàng đưa vào Z3 kiểm chứng

Khi GEMINI_API_KEY chưa có: tự động dùng MockParser để test.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .prompts import (
    SYSTEM_PROMPT,
    DETECT_SCENARIO_PROMPT,
    VN_PAYMENT_EXTRACT_PROMPT,
    KR_REFUND_EXTRACT_PROMPT,
    EXPLAIN_RESULT_PROMPT,
)
from .schemas import (
    ParseResult,
    ParsedVNTransaction,
    ParsedKRTaxRefund,
    ScenarioType,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: trích xuất JSON từ chuỗi text trả về bởi LLM
# ---------------------------------------------------------------------------
def _extract_json(text: str) -> dict[str, Any]:
    """
    Trích xuất JSON từ chuỗi text của LLM.
    LLM đôi khi wrap JSON trong ```json ... ``` hoặc thêm text thừa.
    """
    # Thử parse thẳng trước
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Tìm JSON block trong markdown
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Tìm bất kỳ { ... } nào
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Không thể trích xuất JSON từ: {text[:200]}")


# ---------------------------------------------------------------------------
# Mock Parser — dùng khi không có API key (cho dev/test)
# ---------------------------------------------------------------------------
class MockSemanticParser:
    """
    Giả lập Gemini bằng rule-based parsing đơn giản.
    Dùng cho môi trường dev khi chưa có GEMINI_API_KEY.
    Hỗ trợ nhận diện các từ khóa phổ biến trong tiếng Việt và tiếng Anh.
    """

    def detect_scenario(self, user_input: str) -> ScenarioType:
        text = user_input.lower()
        kr_keywords = ["krw", "won", "hàn quốc", "korea", "incheon", "hoàn thuế", "tax refund", "duty-free", "tax-free"]
        if any(kw in text for kw in kr_keywords):
            return ScenarioType.KR_TAX_REFUND

        vn_keywords = ["vnd", "vnđ", "triệu", "đồng", "tiền mặt", "chuyển khoản", "thanh toán", "chi phí", "million vnd", "cash"]
        if any(kw in text for kw in vn_keywords):
            return ScenarioType.VN_PAYMENT

        return ScenarioType.UNKNOWN

    def _parse_amount_vnd(self, text: str) -> int:
        """Trích xuất số tiền VNĐ từ văn bản."""
        text_lower = text.lower()

        # Tìm số + "triệu" hoặc "tr"
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:triệu|tr\b|million)", text_lower)
        if match:
            return int(float(match.group(1).replace(",", ".")) * 1_000_000)

        # Tìm số thuần (>=6 chữ số → đơn vị VNĐ)
        match = re.search(r"(\d{6,})", text.replace(".", "").replace(",", ""))
        if match:
            return int(match.group(1))

        # Số nhỏ hơn
        match = re.search(r"(\d+)", text)
        if match:
            return int(match.group(1))

        return 0

    def parse_vn_transaction(self, user_input: str) -> ParsedVNTransaction:
        text = user_input.lower()
        amount = self._parse_amount_vnd(user_input)

        # Phát hiện tiền mặt
        cash_keywords = ["tiền mặt", "cash", "mặt"]
        transfer_keywords = ["chuyển khoản", "ngân hàng", "bank", "transfer", "thẻ", "card", "ví", "wallet"]
        is_cash = any(kw in text for kw in cash_keywords) and not any(kw in text for kw in transfer_keywords)
        if any(kw in text for kw in transfer_keywords):
            is_cash = False
            method = "bank_transfer"
        else:
            method = "cash" if is_cash else "other"

        # Phát hiện mục đích
        purpose_map = {
            "event": ["sự kiện", "event", "hội nghị", "tiệc"],
            "equipment": ["thiết bị", "equipment", "máy", "đồ"],
            "services": ["dịch vụ", "service", "tư vấn"],
            "salary": ["lương", "salary", "thưởng"],
            "tax": ["thuế", "tax"],
        }
        purpose = "other"
        for p, keywords in purpose_map.items():
            if any(kw in text for kw in keywords):
                purpose = p
                break

        return ParsedVNTransaction(
            amount=amount,
            is_cash_payment=is_cash,
            payment_method=method,
            purpose=purpose,
            description=user_input[:100],
            confidence=0.75,
            raw_input=user_input,
        )

    def parse_kr_tax_refund(self, user_input: str) -> ParsedKRTaxRefund:
        text = user_input.lower()

        # Tìm số TRƯỚC "krw / won / 원" — yêu cầu ít nhất 1 chữ số
        before_kw = re.findall(r"\b([\d]+(?:,\d{3})*)\s*(?:krw|won|원)\b", text)
        # Tìm số SAU "krw / won / 원" — yêu cầu ít nhất 1 chữ số
        after_kw = re.findall(r"(?:krw|won|원)\s+([\d]+(?:,\d{3})*)\b", text)

        raw_amounts = before_kw + after_kw
        # Lọc chuỗi rỗng và convert sang int
        amounts = sorted(
            {int(m.replace(",", "")) for m in raw_amounts if m.strip()},
            reverse=True,
        )

        receipt_amount = amounts[0] if len(amounts) >= 1 else 0
        refund_amount = amounts[1] if len(amounts) >= 2 else int(receipt_amount * 0.1)

        is_eligible = receipt_amount >= 30_000
        needs_customs = refund_amount >= 75_000

        return ParsedKRTaxRefund(
            receipt_amount=receipt_amount,
            refund_amount=refund_amount,
            needs_customs_check=needs_customs,
            is_eligible=is_eligible,
            is_tax_free_shop=True,
            confidence=0.70,
            raw_input=user_input,
        )

    def explain_result(self, original_request: str, status: str, violations: list) -> str:
        if status == "SAT":
            return f"✅ Giao dịch được phê duyệt. Tất cả quy định đã được kiểm tra và thỏa mãn."
        violation_text = violations[0].violation_detail if violations else "Vi phạm quy định"
        return f"❌ Giao dịch bị từ chối. {violation_text}"


# ---------------------------------------------------------------------------
# Gemini Parser — dùng khi có GEMINI_API_KEY
# ---------------------------------------------------------------------------
class GeminiSemanticParser:
    """
    Parser thực sự dùng Gemini 2.0 Flash API.
    Tự động fallback sang MockParser nếu API lỗi.
    """

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self._model_name = model
        self._mock = MockSemanticParser()  # fallback
        self._client = None

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._client = genai.GenerativeModel(
                model_name=model,
                system_instruction=SYSTEM_PROMPT,
                generation_config={"temperature": 0.0, "response_mime_type": "application/json"},
            )
            logger.info(f"Gemini parser initialized: {model}")
        except ImportError:
            logger.warning("google-generativeai not installed. Using MockParser.")
        except Exception as e:
            logger.warning(f"Gemini init failed: {e}. Using MockParser.")

    def _call_gemini(self, prompt: str) -> dict[str, Any]:
        """Gọi Gemini API và trả về dict JSON."""
        if self._client is None:
            raise RuntimeError("Gemini client not available")
        response = self._client.generate_content(prompt)
        return _extract_json(response.text)

    def detect_scenario(self, user_input: str) -> ScenarioType:
        """Dùng Gemini phát hiện loại kịch bản."""
        if self._client is None:
            return self._mock.detect_scenario(user_input)
        try:
            prompt = DETECT_SCENARIO_PROMPT.format(user_input=user_input)
            data = self._call_gemini(prompt)
            return ScenarioType(data.get("scenario_type", "unknown"))
        except Exception as e:
            logger.warning(f"Gemini detect_scenario failed: {e}. Falling back to mock.")
            return self._mock.detect_scenario(user_input)

    def parse_vn_transaction(self, user_input: str) -> ParsedVNTransaction:
        """Dùng Gemini trích xuất giao dịch VN."""
        if self._client is None:
            return self._mock.parse_vn_transaction(user_input)
        try:
            prompt = VN_PAYMENT_EXTRACT_PROMPT.format(user_input=user_input)
            data = self._call_gemini(prompt)
            data["raw_input"] = user_input
            return ParsedVNTransaction(**data)
        except Exception as e:
            logger.warning(f"Gemini parse_vn failed: {e}. Falling back to mock.")
            return self._mock.parse_vn_transaction(user_input)

    def parse_kr_tax_refund(self, user_input: str) -> ParsedKRTaxRefund:
        """Dùng Gemini trích xuất hoàn thuế KR."""
        if self._client is None:
            return self._mock.parse_kr_tax_refund(user_input)
        try:
            prompt = KR_REFUND_EXTRACT_PROMPT.format(user_input=user_input)
            data = self._call_gemini(prompt)
            data["raw_input"] = user_input
            return ParsedKRTaxRefund(**data)
        except Exception as e:
            logger.warning(f"Gemini parse_kr failed: {e}. Falling back to mock.")
            return self._mock.parse_kr_tax_refund(user_input)

    def explain_result(self, original_request: str, status: str, violations: list) -> str:
        """Dùng Gemini tạo phản hồi thân thiện."""
        if self._client is None:
            return self._mock.explain_result(original_request, status, violations)
        try:
            violation_text = "; ".join(v.violation_detail for v in violations) if violations else "Không có vi phạm"
            prompt = EXPLAIN_RESULT_PROMPT.format(
                original_request=original_request,
                status=status,
                violations=violation_text,
            )
            response = self._client.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini explain failed: {e}. Falling back to mock.")
            return self._mock.explain_result(original_request, status, violations)


# ---------------------------------------------------------------------------
# SemanticParser — public interface (tự chọn Gemini hoặc Mock)
# ---------------------------------------------------------------------------
class SemanticParser:
    """
    Public interface của Semantic Parsing Layer.

    Tự động chọn:
    - GeminiSemanticParser nếu có GEMINI_API_KEY
    - MockSemanticParser nếu không có key (để dev/test không cần API)

    Sử dụng:
        parser = SemanticParser.from_config()
        result = parser.parse("Thanh toán tiền mặt 25 triệu cho sự kiện")
        # result.scenario_type == ScenarioType.VN_PAYMENT
        # result.to_z3_data() == {"amount": 25000000, "is_cash_payment": True, ...}
    """

    def __init__(self, api_key: str = "", model: str = "gemini-2.0-flash") -> None:
        if api_key:
            self._backend: GeminiSemanticParser | MockSemanticParser = GeminiSemanticParser(api_key, model)
        else:
            logger.info("No GEMINI_API_KEY — using MockSemanticParser for development")
            self._backend = MockSemanticParser()

    @classmethod
    def from_config(cls) -> "SemanticParser":
        """Tạo parser từ environment variables / config."""
        try:
            from src.config import get_settings
            settings = get_settings()
            return cls(api_key=settings.gemini_api_key, model=settings.gemini_model)
        except Exception:
            return cls()

    def parse(self, user_input: str) -> ParseResult:
        """
        Pipeline chính: NL input → ParseResult có cấu trúc.

        Args:
            user_input: Câu yêu cầu bằng ngôn ngữ tự nhiên

        Returns:
            ParseResult với scenario_type và dữ liệu đã trích xuất
        """
        if not user_input or not user_input.strip():
            return ParseResult(
                scenario_type=ScenarioType.UNKNOWN,
                parse_error="Input rỗng",
            )

        try:
            # Bước 1: Phát hiện loại kịch bản
            scenario = self._backend.detect_scenario(user_input)

            # Bước 2: Trích xuất dữ liệu tương ứng
            if scenario == ScenarioType.VN_PAYMENT:
                vn_data = self._backend.parse_vn_transaction(user_input)
                return ParseResult(
                    scenario_type=ScenarioType.VN_PAYMENT,
                    vn_transaction=vn_data,
                )
            elif scenario == ScenarioType.KR_TAX_REFUND:
                kr_data = self._backend.parse_kr_tax_refund(user_input)
                return ParseResult(
                    scenario_type=ScenarioType.KR_TAX_REFUND,
                    kr_tax_refund=kr_data,
                )
            else:
                return ParseResult(
                    scenario_type=ScenarioType.UNKNOWN,
                    parse_error="Không nhận diện được loại kịch bản",
                )

        except Exception as e:
            logger.error(f"SemanticParser.parse failed: {e}")
            return ParseResult(
                scenario_type=ScenarioType.UNKNOWN,
                parse_error=str(e),
            )

    def explain_result(self, original_request: str, status: str, violations: list) -> str:
        """Tạo câu phản hồi thân thiện từ kết quả Z3."""
        return self._backend.explain_result(original_request, status, violations)
