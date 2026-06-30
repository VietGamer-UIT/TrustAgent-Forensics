"""
TrustAgent.Forensics — Vietnamese Tax Cash Payment Rule

Legal Basis: Circular 96/2015/TT-BTC, Article 4, Section 1, Point c
─────────────────────────────────────────────────────────────────────
"Mọi khoản chi phí mua hàng hóa, dịch vụ từng lần có giá trị
từ 20 triệu đồng trở lên (đã bao gồm thuế GTGT) bắt buộc phải
có chứng từ thanh toán không dùng tiền mặt thì mới được ghi nhận
là chi phí hợp lý được trừ khi tính thuế."

Translation: Any single purchase of goods/services valued at 20 million
VND or more (VAT inclusive) MUST have non-cash payment documentation
to be recognized as a deductible business expense for tax purposes.

Z3 Encoding:
    Implies(amount >= 20,000,000, Not(is_cash_payment))
    "If amount >= 20M VND, then payment must NOT be cash"
"""

from __future__ import annotations

from typing import Any

from z3 import Solver, Int, Bool, Implies, Not

from .base_rule import BusinessRule


# Threshold defined by Vietnamese tax regulation (VND)
VN_CASH_THRESHOLD = 20_000_000


class VietnamCashPaymentRule(BusinessRule):
    """
    Enforces the Vietnamese tax regulation on cash payments.

    Any transaction >= 20,000,000 VND paid in cash will be flagged
    as UNSAT (non-compliant), as it would not be tax-deductible.
    """

    @property
    def name(self) -> str:
        return "vn_cash_payment_threshold"

    @property
    def description(self) -> str:
        return (
            "Thông tư 96/2015/TT-BTC: Chi phí mua hàng hóa/dịch vụ từ "
            f"{VN_CASH_THRESHOLD:,} VNĐ trở lên phải thanh toán không dùng tiền mặt "
            "để được ghi nhận là chi phí được trừ thuế."
        )

    @property
    def legal_reference(self) -> str:
        return "Thông tư 96/2015/TT-BTC, Điều 4, Khoản 1, Điểm c"

    @property
    def severity(self) -> str:
        return "critical"

    def encode(self, solver: Solver, data: dict[str, Any]) -> None:
        """
        Encode the 20M VND cash payment threshold rule into Z3.

        Mathematical formulation:
            ∀ transaction: amount ≥ 20,000,000 ⟹ ¬is_cash_payment

        This means: "For any transaction where the amount is at least
        20 million VND, it is implied that cash payment is NOT used."

        If the actual data has amount=25M and is_cash=True, Z3 will
        find that these constraints are contradictory → UNSAT.
        """
        # Step 1: Declare Z3 symbolic variables
        z3_amount = Int("amount")
        z3_is_cash = Bool("is_cash")

        # Step 2: Encode the legal rule as a Z3 constraint
        # "If amount >= 20M, then payment must NOT be cash"
        solver.add(Implies(z3_amount >= VN_CASH_THRESHOLD, Not(z3_is_cash)))

        # Step 3: Bind actual transaction data from the AI Agent
        solver.add(z3_amount == data["amount"])
        solver.add(z3_is_cash == data["is_cash_payment"])

    def get_violation_detail(self, data: dict[str, Any]) -> str:
        """Generate a human-readable violation explanation."""
        amount = data.get("amount", 0)
        return (
            f"Số tiền {amount:,} VNĐ ≥ ngưỡng {VN_CASH_THRESHOLD:,} VNĐ "
            f"nhưng phương thức thanh toán là tiền mặt. "
            f"Theo Thông tư 96/2015/TT-BTC, khoản chi này sẽ KHÔNG được "
            f"ghi nhận là chi phí được trừ khi tính thuế TNDN. "
            f"Yêu cầu chuyển sang thanh toán qua ngân hàng."
        )
