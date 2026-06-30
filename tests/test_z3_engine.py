"""
TrustAgent.Forensics — Z3 Verification Engine Tests

Comprehensive test suite covering:
1. Vietnamese Tax Cash Payment Rule (Circular 96/2015/TT-BTC)
2. Korean Tax Refund Rule (Incheon Airport)
3. TrustAgentSolver integration
4. Edge cases and boundary conditions
"""

import sys
import os
import time

import pytest

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.z3_engine.solver import TrustAgentSolver
from src.z3_engine.models import VerificationStatus, TransactionData, TaxRefundData
from src.z3_engine.rules.vn_tax_rule import VietnamCashPaymentRule
from src.z3_engine.rules.kr_refund_rule import KoreaTaxRefundRule


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def vn_solver() -> TrustAgentSolver:
    """Create solver with Vietnamese tax rule."""
    solver = TrustAgentSolver(timeout_ms=5000)
    solver.register_rule(VietnamCashPaymentRule())
    return solver


@pytest.fixture
def kr_solver() -> TrustAgentSolver:
    """Create solver with Korean tax refund rule."""
    solver = TrustAgentSolver(timeout_ms=5000)
    solver.register_rule(KoreaTaxRefundRule())
    return solver


@pytest.fixture
def full_solver() -> TrustAgentSolver:
    """Create solver with all rules registered."""
    solver = TrustAgentSolver(timeout_ms=5000)
    solver.register_rule(VietnamCashPaymentRule())
    solver.register_rule(KoreaTaxRefundRule())
    return solver


# =============================================================================
# Vietnamese Tax Rule Tests
# =============================================================================

class TestVietnamCashPaymentRule:
    """Test cases for Circular 96/2015/TT-BTC compliance."""

    def test_cash_payment_above_threshold_blocked(self, vn_solver: TrustAgentSolver):
        """
        SCENARIO: AI Agent tries to pay 25M VND in cash.
        EXPECTED: UNSAT (BLOCKED) — Violates the 20M VND cash threshold.
        """
        data = TransactionData(
            amount=25_000_000,
            is_cash_payment=True,
            description="Thanh toán tiền mặt 25 triệu cho sự kiện",
        ).model_dump()

        result = vn_solver.verify(data)

        assert result.status == VerificationStatus.UNSAT
        assert result.is_compliant is False
        assert len(result.violations) == 1
        assert result.violations[0].rule_name == "vn_cash_payment_threshold"
        assert "20,000,000" in result.violations[0].violation_detail
        print(f"\n✅ BLOCKED: {result.explanation}")

    def test_bank_transfer_above_threshold_allowed(self, vn_solver: TrustAgentSolver):
        """
        SCENARIO: AI Agent pays 30M VND via bank transfer.
        EXPECTED: SAT (ALLOWED) — Bank transfer is compliant.
        """
        data = TransactionData(
            amount=30_000_000,
            is_cash_payment=False,
            description="Chuyển khoản 30 triệu mua thiết bị",
        ).model_dump()

        result = vn_solver.verify(data)

        assert result.status == VerificationStatus.SAT
        assert result.is_compliant is True
        assert len(result.violations) == 0
        print(f"\n✅ ALLOWED: {result.explanation}")

    def test_cash_payment_below_threshold_allowed(self, vn_solver: TrustAgentSolver):
        """
        SCENARIO: AI Agent pays 15M VND in cash.
        EXPECTED: SAT (ALLOWED) — Below 20M threshold, cash is fine.
        """
        data = TransactionData(
            amount=15_000_000,
            is_cash_payment=True,
            description="Chi tiền mặt 15 triệu cho văn phòng phẩm",
        ).model_dump()

        result = vn_solver.verify(data)

        assert result.status == VerificationStatus.SAT
        assert result.is_compliant is True
        print(f"\n✅ ALLOWED: {result.explanation}")

    def test_exact_threshold_cash_blocked(self, vn_solver: TrustAgentSolver):
        """
        SCENARIO: AI Agent pays exactly 20M VND in cash.
        EXPECTED: UNSAT (BLOCKED) — "từ 20 triệu trở lên" includes 20M.
        """
        data = TransactionData(
            amount=20_000_000,
            is_cash_payment=True,
            description="Chi tiền mặt đúng 20 triệu",
        ).model_dump()

        result = vn_solver.verify(data)

        assert result.status == VerificationStatus.UNSAT
        assert result.is_compliant is False
        print(f"\n✅ BLOCKED at exact threshold: {result.explanation}")

    def test_exact_threshold_bank_transfer_allowed(self, vn_solver: TrustAgentSolver):
        """
        SCENARIO: AI Agent pays exactly 20M VND via bank transfer.
        EXPECTED: SAT (ALLOWED) — Non-cash at threshold is compliant.
        """
        data = TransactionData(
            amount=20_000_000,
            is_cash_payment=False,
            description="Chuyển khoản đúng 20 triệu",
        ).model_dump()

        result = vn_solver.verify(data)

        assert result.status == VerificationStatus.SAT
        assert result.is_compliant is True
        print(f"\n✅ ALLOWED: {result.explanation}")

    def test_just_below_threshold_cash_allowed(self, vn_solver: TrustAgentSolver):
        """
        SCENARIO: AI Agent pays 19,999,999 VND in cash.
        EXPECTED: SAT (ALLOWED) — Just below threshold.
        """
        data = TransactionData(
            amount=19_999_999,
            is_cash_payment=True,
            description="Chi tiền mặt 19,999,999 VNĐ",
        ).model_dump()

        result = vn_solver.verify(data)

        assert result.status == VerificationStatus.SAT
        assert result.is_compliant is True
        print(f"\n✅ ALLOWED: Just below threshold")

    def test_very_large_cash_payment_blocked(self, vn_solver: TrustAgentSolver):
        """
        SCENARIO: AI Agent tries to pay 500M VND in cash.
        EXPECTED: UNSAT (BLOCKED) — Way above threshold.
        """
        data = TransactionData(
            amount=500_000_000,
            is_cash_payment=True,
            description="Chi tiền mặt 500 triệu",
        ).model_dump()

        result = vn_solver.verify(data)

        assert result.status == VerificationStatus.UNSAT
        assert result.is_compliant is False
        print(f"\n✅ BLOCKED: Large cash payment blocked")

    def test_zero_amount_allowed(self, vn_solver: TrustAgentSolver):
        """
        SCENARIO: Zero-value transaction.
        EXPECTED: SAT (ALLOWED) — 0 < 20M threshold.
        """
        data = TransactionData(
            amount=0,
            is_cash_payment=True,
            description="Zero transaction",
        ).model_dump()

        result = vn_solver.verify(data)

        assert result.status == VerificationStatus.SAT
        assert result.is_compliant is True


# =============================================================================
# Korean Tax Refund Rule Tests
# =============================================================================

class TestKoreaTaxRefundRule:
    """Test cases for Korean tax refund compliance."""

    def test_eligible_small_refund_kiosk(self, kr_solver: TrustAgentSolver):
        """
        SCENARIO: Tourist buys 50,000 KRW item, refund 5,000 KRW.
        EXPECTED: SAT — Eligible, small refund, use kiosk (no customs).
        """
        data = TaxRefundData(
            receipt_amount=50_000,
            refund_amount=5_000,
            needs_customs_check=False,
            is_eligible=True,
        ).model_dump()

        result = kr_solver.verify(data)

        assert result.status == VerificationStatus.SAT
        assert result.is_compliant is True
        print(f"\n✅ ALLOWED: Small refund via kiosk")

    def test_eligible_large_refund_customs(self, kr_solver: TrustAgentSolver):
        """
        SCENARIO: Tourist buys 1,000,000 KRW item, refund 80,000 KRW.
        EXPECTED: SAT — Eligible, large refund, customs check required.
        """
        data = TaxRefundData(
            receipt_amount=1_000_000,
            refund_amount=80_000,
            needs_customs_check=True,
            is_eligible=True,
        ).model_dump()

        result = kr_solver.verify(data)

        assert result.status == VerificationStatus.SAT
        assert result.is_compliant is True
        print(f"\n✅ ALLOWED: Large refund with customs check")

    def test_large_refund_without_customs_blocked(self, kr_solver: TrustAgentSolver):
        """
        SCENARIO: Refund 80,000 KRW but skipping customs check.
        EXPECTED: UNSAT (BLOCKED) — Must have customs inspection.
        """
        data = TaxRefundData(
            receipt_amount=1_000_000,
            refund_amount=80_000,
            needs_customs_check=False,  # ← VIOLATION: should be True
            is_eligible=True,
        ).model_dump()

        result = kr_solver.verify(data)

        assert result.status == VerificationStatus.UNSAT
        assert result.is_compliant is False
        assert len(result.violations) == 1
        print(f"\n✅ BLOCKED: {result.violations[0].violation_detail}")

    def test_small_refund_with_unnecessary_customs_blocked(self, kr_solver: TrustAgentSolver):
        """
        SCENARIO: Refund 50,000 KRW but requesting customs check.
        EXPECTED: UNSAT (BLOCKED) — Small refund should use kiosk.
        """
        data = TaxRefundData(
            receipt_amount=100_000,
            refund_amount=50_000,
            needs_customs_check=True,  # ← VIOLATION: should be False
            is_eligible=True,
        ).model_dump()

        result = kr_solver.verify(data)

        assert result.status == VerificationStatus.UNSAT
        assert result.is_compliant is False
        print(f"\n✅ BLOCKED: Unnecessary customs check flagged")

    def test_ineligible_receipt_below_minimum(self, kr_solver: TrustAgentSolver):
        """
        SCENARIO: Receipt 20,000 KRW but marked eligible.
        EXPECTED: UNSAT (BLOCKED) — Below 30,000 KRW minimum.
        """
        data = TaxRefundData(
            receipt_amount=20_000,
            refund_amount=2_000,
            needs_customs_check=False,
            is_eligible=True,  # ← VIOLATION: receipt < 30,000
        ).model_dump()

        result = kr_solver.verify(data)

        assert result.status == VerificationStatus.UNSAT
        assert result.is_compliant is False
        print(f"\n✅ BLOCKED: Receipt below minimum")

    def test_eligible_receipt_marked_ineligible_blocked(self, kr_solver: TrustAgentSolver):
        """
        SCENARIO: Receipt 50,000 KRW but marked as NOT eligible.
        EXPECTED: UNSAT (BLOCKED) — Should be eligible.
        """
        data = TaxRefundData(
            receipt_amount=50_000,
            refund_amount=5_000,
            needs_customs_check=False,
            is_eligible=False,  # ← VIOLATION: receipt >= 30,000 = eligible
        ).model_dump()

        result = kr_solver.verify(data)

        assert result.status == VerificationStatus.UNSAT
        assert result.is_compliant is False
        print(f"\n✅ BLOCKED: Eligible receipt marked ineligible")

    def test_exact_customs_threshold_requires_check(self, kr_solver: TrustAgentSolver):
        """
        SCENARIO: Refund exactly 75,000 KRW with customs check.
        EXPECTED: SAT — At threshold, customs is required.
        """
        data = TaxRefundData(
            receipt_amount=500_000,
            refund_amount=75_000,
            needs_customs_check=True,
            is_eligible=True,
        ).model_dump()

        result = kr_solver.verify(data)

        assert result.status == VerificationStatus.SAT
        assert result.is_compliant is True
        print(f"\n✅ ALLOWED: Exact threshold with customs")

    def test_just_below_customs_threshold_kiosk(self, kr_solver: TrustAgentSolver):
        """
        SCENARIO: Refund 74,999 KRW, using kiosk (no customs).
        EXPECTED: SAT — Just below customs threshold.
        """
        data = TaxRefundData(
            receipt_amount=500_000,
            refund_amount=74_999,
            needs_customs_check=False,
            is_eligible=True,
        ).model_dump()

        result = kr_solver.verify(data)

        assert result.status == VerificationStatus.SAT
        assert result.is_compliant is True
        print(f"\n✅ ALLOWED: Just below customs threshold")


# =============================================================================
# Solver Integration Tests
# =============================================================================

class TestTrustAgentSolver:
    """Integration tests for the TrustAgentSolver wrapper."""

    def test_register_rule(self):
        """Test rule registration."""
        solver = TrustAgentSolver()
        solver.register_rule(VietnamCashPaymentRule())
        assert "vn_cash_payment_threshold" in solver.get_registered_rules()

    def test_register_duplicate_rule_raises(self):
        """Test that registering duplicate rule raises ValueError."""
        solver = TrustAgentSolver()
        solver.register_rule(VietnamCashPaymentRule())
        with pytest.raises(ValueError, match="already registered"):
            solver.register_rule(VietnamCashPaymentRule())

    def test_unregister_rule(self):
        """Test rule unregistration."""
        solver = TrustAgentSolver()
        solver.register_rule(VietnamCashPaymentRule())
        solver.unregister_rule("vn_cash_payment_threshold")
        assert "vn_cash_payment_threshold" not in solver.get_registered_rules()

    def test_verify_unknown_rule_raises(self):
        """Test that verifying with unknown rule raises ValueError."""
        solver = TrustAgentSolver()
        with pytest.raises(ValueError, match="Unknown rules"):
            solver.verify({}, rule_names=["nonexistent_rule"])

    def test_verify_no_rules_returns_sat(self):
        """Test that verifying with no rules returns SAT."""
        solver = TrustAgentSolver()
        result = solver.verify({"amount": 100})
        assert result.status == VerificationStatus.SAT
        assert result.is_compliant is True

    def test_selective_rule_check(self, full_solver: TrustAgentSolver):
        """Test verifying against specific rules only."""
        # This data is VN-relevant but not KR-relevant
        data = TransactionData(
            amount=25_000_000,
            is_cash_payment=True,
        ).model_dump()

        result = full_solver.verify(data, rule_names=["vn_cash_payment_threshold"])

        assert result.status == VerificationStatus.UNSAT
        assert len(result.rules_checked) == 1
        assert "vn_cash_payment_threshold" in result.rules_checked

    def test_verification_timing(self, vn_solver: TrustAgentSolver):
        """Test that Z3 verification completes within performance target."""
        data = TransactionData(
            amount=25_000_000,
            is_cash_payment=True,
        ).model_dump()

        result = vn_solver.verify(data)

        # Target: < 50ms (generous for CI environments)
        assert result.verification_time_ms < 50, (
            f"Verification took {result.verification_time_ms}ms, target is < 50ms"
        )
        print(f"\n⚡ Verification time: {result.verification_time_ms:.3f}ms")

    def test_result_contains_audit_data(self, vn_solver: TrustAgentSolver):
        """Test that results include complete audit metadata."""
        data = TransactionData(
            amount=25_000_000,
            is_cash_payment=True,
        ).model_dump()

        result = vn_solver.verify(data)

        # Check audit fields
        assert result.id is not None
        assert result.timestamp is not None
        assert result.raw_input == data
        assert len(result.rules_checked) > 0

        # Test audit dict conversion
        audit = result.to_audit_dict()
        assert "verification_id" in audit
        assert "status" in audit
        assert "violations" in audit
        assert "timestamp" in audit
        print(f"\n📋 Audit record: {audit['verification_id']}")

    def test_solver_repr(self, full_solver: TrustAgentSolver):
        """Test string representation."""
        repr_str = repr(full_solver)
        assert "TrustAgentSolver" in repr_str
        assert "vn_cash_payment_threshold" in repr_str
        assert "kr_tax_refund" in repr_str


# =============================================================================
# Performance Benchmark
# =============================================================================

class TestPerformance:
    """Performance benchmarks for Z3 verification."""

    def test_batch_verification_performance(self, vn_solver: TrustAgentSolver):
        """Benchmark: 100 verifications should complete under 1 second."""
        data = TransactionData(
            amount=25_000_000,
            is_cash_payment=True,
        ).model_dump()

        start = time.perf_counter()
        for _ in range(100):
            vn_solver.verify(data)
        elapsed = time.perf_counter() - start

        avg_ms = (elapsed / 100) * 1000
        print(f"\n⚡ Batch benchmark: 100 verifications in {elapsed:.3f}s "
              f"(avg {avg_ms:.3f}ms per verification)")
        assert elapsed < 1.0, f"100 verifications took {elapsed:.3f}s (target: < 1s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
