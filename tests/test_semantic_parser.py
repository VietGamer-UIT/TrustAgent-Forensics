"""
TrustAgent.Forensics — Tests cho Semantic Parser (Phase 2)

Dùng MockSemanticParser (không cần API key) để test pipeline đầy đủ:
- Phát hiện kịch bản (VN / KR / unknown)
- Trích xuất dữ liệu từ tiếng Việt và tiếng Anh
- End-to-End: NL Input → Parse → Z3 Verify → Result
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.semantic.parser import SemanticParser, MockSemanticParser
from src.semantic.schemas import ScenarioType
from src.z3_engine.solver import TrustAgentSolver
from src.z3_engine.rules.vn_tax_rule import VietnamCashPaymentRule
from src.z3_engine.rules.kr_refund_rule import KoreaTaxRefundRule
from src.z3_engine.models import VerificationStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_parser() -> SemanticParser:
    """Parser không dùng API key → dùng MockParser."""
    return SemanticParser(api_key="")


@pytest.fixture
def full_solver() -> TrustAgentSolver:
    """Solver đầy đủ với cả 2 bộ luật."""
    solver = TrustAgentSolver()
    solver.register_rule(VietnamCashPaymentRule())
    solver.register_rule(KoreaTaxRefundRule())
    return solver


# ---------------------------------------------------------------------------
# Test phát hiện kịch bản
# ---------------------------------------------------------------------------

class TestScenarioDetection:
    """Test MockParser nhận diện đúng loại kịch bản."""

    def test_detect_vn_payment_viet(self, mock_parser):
        result = mock_parser.parse("Thanh toán tiền mặt 25 triệu cho sự kiện")
        assert result.scenario_type == ScenarioType.VN_PAYMENT

    def test_detect_vn_payment_english(self, mock_parser):
        result = mock_parser.parse("Pay 25 million VND cash for event")
        assert result.scenario_type == ScenarioType.VN_PAYMENT

    def test_detect_vn_chuyen_khoan(self, mock_parser):
        result = mock_parser.parse("Chuyển khoản 30 triệu mua thiết bị")
        assert result.scenario_type == ScenarioType.VN_PAYMENT

    def test_detect_kr_tax_refund_viet(self, mock_parser):
        result = mock_parser.parse("Hoàn thuế 50,000 KRW tại Incheon")
        assert result.scenario_type == ScenarioType.KR_TAX_REFUND

    def test_detect_kr_tax_refund_won(self, mock_parser):
        result = mock_parser.parse("Mua hàng 100,000 won tại Hàn Quốc")
        assert result.scenario_type == ScenarioType.KR_TAX_REFUND

    def test_detect_kr_english(self, mock_parser):
        result = mock_parser.parse("Tax refund 5000 KRW at duty-free shop")
        assert result.scenario_type == ScenarioType.KR_TAX_REFUND

    def test_detect_unknown(self, mock_parser):
        result = mock_parser.parse("Hôm nay thời tiết đẹp quá")
        assert result.scenario_type == ScenarioType.UNKNOWN

    def test_empty_input(self, mock_parser):
        result = mock_parser.parse("")
        assert result.scenario_type == ScenarioType.UNKNOWN
        assert result.parse_error is not None


# ---------------------------------------------------------------------------
# Test trích xuất dữ liệu VN
# ---------------------------------------------------------------------------

class TestVNTransactionParsing:
    """Test trích xuất đúng dữ liệu từ câu tiếng Việt."""

    def test_parse_25_million_cash(self, mock_parser):
        result = mock_parser.parse("Thanh toán tiền mặt 25 triệu cho sự kiện")
        assert result.vn_transaction is not None
        assert result.vn_transaction.amount == 25_000_000
        assert result.vn_transaction.is_cash_payment is True

    def test_parse_30_million_bank_transfer(self, mock_parser):
        result = mock_parser.parse("Chuyển khoản 30 triệu mua thiết bị văn phòng")
        assert result.vn_transaction is not None
        assert result.vn_transaction.amount == 30_000_000
        assert result.vn_transaction.is_cash_payment is False

    def test_parse_15_million_cash(self, mock_parser):
        result = mock_parser.parse("Chi 15tr tiền mặt văn phòng phẩm")
        assert result.vn_transaction is not None
        assert result.vn_transaction.amount == 15_000_000
        assert result.vn_transaction.is_cash_payment is True

    def test_parse_english_cash(self, mock_parser):
        result = mock_parser.parse("Pay 25 million VND cash for event costs")
        assert result.vn_transaction is not None
        assert result.vn_transaction.amount == 25_000_000
        assert result.vn_transaction.is_cash_payment is True

    def test_z3_data_keys(self, mock_parser):
        """Kiểm tra to_z3_data() có đúng keys cho Z3."""
        result = mock_parser.parse("Thanh toán tiền mặt 25 triệu")
        z3_data = result.to_z3_data()
        assert "amount" in z3_data
        assert "is_cash_payment" in z3_data

    def test_applicable_rules_vn(self, mock_parser):
        result = mock_parser.parse("Thanh toán tiền mặt 25 triệu")
        assert "vn_cash_payment_threshold" in result.get_applicable_rules()


# ---------------------------------------------------------------------------
# Test trích xuất dữ liệu KR
# ---------------------------------------------------------------------------

class TestKRTaxRefundParsing:
    """Test trích xuất đúng dữ liệu hoàn thuế Hàn Quốc."""

    def test_parse_small_refund(self, mock_parser):
        result = mock_parser.parse("Mua hàng 50,000 KRW tại duty-free Incheon, hoàn 5,000 KRW")
        assert result.kr_tax_refund is not None
        assert result.kr_tax_refund.receipt_amount == 50_000
        assert result.kr_tax_refund.refund_amount == 5_000
        assert result.kr_tax_refund.is_eligible is True
        assert result.kr_tax_refund.needs_customs_check is False

    def test_parse_large_refund(self, mock_parser):
        result = mock_parser.parse("Mua hàng 1,000,000 won, hoàn 80,000 won")
        assert result.kr_tax_refund is not None
        assert result.kr_tax_refund.receipt_amount == 1_000_000
        assert result.kr_tax_refund.refund_amount == 80_000
        assert result.kr_tax_refund.needs_customs_check is True

    def test_parse_ineligible_receipt(self, mock_parser):
        result = mock_parser.parse("Mua 20,000 KRW want tax refund")
        assert result.kr_tax_refund is not None
        assert result.kr_tax_refund.receipt_amount == 20_000
        assert result.kr_tax_refund.is_eligible is False

    def test_applicable_rules_kr(self, mock_parser):
        result = mock_parser.parse("Hoàn thuế 5,000 KRW tại Hàn Quốc")
        assert "kr_tax_refund" in result.get_applicable_rules()


# ---------------------------------------------------------------------------
# End-to-End: NL → Parse → Z3 → Result
# ---------------------------------------------------------------------------

class TestEndToEndPipeline:
    """Test toàn bộ pipeline Neural → Symbolic."""

    def test_vn_cash_25m_blocked(self, mock_parser, full_solver):
        """'Thanh toán tiền mặt 25 triệu' → UNSAT."""
        parse_result = mock_parser.parse("Thanh toán tiền mặt 25 triệu cho sự kiện")
        z3_data = parse_result.to_z3_data()
        rules = parse_result.get_applicable_rules()

        verify_result = full_solver.verify(z3_data, rule_names=rules)

        assert verify_result.status == VerificationStatus.UNSAT
        assert verify_result.is_compliant is False
        print(f"\n🔴 BLOCKED: {verify_result.explanation}")

    def test_vn_transfer_30m_allowed(self, mock_parser, full_solver):
        """'Chuyển khoản 30 triệu' → SAT."""
        parse_result = mock_parser.parse("Chuyển khoản 30 triệu mua thiết bị")
        z3_data = parse_result.to_z3_data()
        rules = parse_result.get_applicable_rules()

        verify_result = full_solver.verify(z3_data, rule_names=rules)

        assert verify_result.status == VerificationStatus.SAT
        assert verify_result.is_compliant is True
        print(f"\n🟢 ALLOWED: {verify_result.explanation}")

    def test_vn_cash_15m_allowed(self, mock_parser, full_solver):
        """'Tiền mặt 15 triệu' → SAT (dưới ngưỡng 20M)."""
        parse_result = mock_parser.parse("Chi 15tr tiền mặt văn phòng phẩm")
        z3_data = parse_result.to_z3_data()
        rules = parse_result.get_applicable_rules()

        verify_result = full_solver.verify(z3_data, rule_names=rules)

        assert verify_result.status == VerificationStatus.SAT
        print(f"\n🟢 ALLOWED: {verify_result.explanation}")

    def test_kr_small_refund_no_customs(self, mock_parser, full_solver):
        """Hoàn 5,000 KRW → SAT, không cần hải quan."""
        parse_result = mock_parser.parse("Mua hàng 50,000 KRW, hoàn 5,000 won")
        z3_data = parse_result.to_z3_data()
        rules = parse_result.get_applicable_rules()

        verify_result = full_solver.verify(z3_data, rule_names=rules)

        assert verify_result.status == VerificationStatus.SAT
        print(f"\n🟢 ALLOWED: {verify_result.explanation}")

    def test_explain_result_blocked(self, mock_parser, full_solver):
        """Kiểm tra giải thích thân thiện cho kết quả BLOCKED."""
        original = "Thanh toán tiền mặt 25 triệu cho sự kiện"
        parse_result = mock_parser.parse(original)
        verify_result = full_solver.verify(
            parse_result.to_z3_data(),
            rule_names=parse_result.get_applicable_rules(),
        )
        explanation = mock_parser.explain_result(
            original,
            verify_result.status.value,
            verify_result.violations,
        )
        assert len(explanation) > 0
        print(f"\n💬 Explanation: {explanation}")

    def test_explain_result_approved(self, mock_parser, full_solver):
        """Kiểm tra giải thích thân thiện cho kết quả APPROVED."""
        original = "Chuyển khoản 30 triệu mua thiết bị"
        parse_result = mock_parser.parse(original)
        verify_result = full_solver.verify(
            parse_result.to_z3_data(),
            rule_names=parse_result.get_applicable_rules(),
        )
        explanation = mock_parser.explain_result(
            original,
            verify_result.status.value,
            verify_result.violations,
        )
        assert "✅" in explanation or len(explanation) > 0
        print(f"\n💬 Explanation: {explanation}")
