"""
TrustAgent.Forensics — Korean Tax Refund Rule for Foreign Tourists

Legal Basis: Korean Tax-Free Shopping Regulations
──────────────────────────────────────────────────
Rule 1: Receipts must be at least 30,000 KRW to qualify for tax refund.
Rule 2: If refund amount < 75,000 KRW → can use automated kiosk (no customs check).
Rule 3: If refund amount >= 75,000 KRW → must get customs officer inspection.

This rule demonstrates the international (Vietnam-Korea) connection
for the INNOSTAR 2026 competition, showing cross-border compliance.

Z3 Encoding:
    is_eligible == (receipt_amount >= 30,000)
    Implies(refund_amount < 75,000, Not(needs_customs_check))
    Implies(refund_amount >= 75,000, needs_customs_check)
"""

from __future__ import annotations

from typing import Any

from z3 import Solver, Int, Bool, BoolVal, Implies, Not

from .base_rule import BusinessRule


# Thresholds defined by Korean tax refund regulations (KRW)
KR_MIN_RECEIPT_AMOUNT = 30_000       # Minimum receipt for eligibility
KR_CUSTOMS_CHECK_THRESHOLD = 75_000  # Refund amount requiring customs inspection


class KoreaTaxRefundRule(BusinessRule):
    """
    Enforces Korean tax refund regulations for foreign tourists.

    Validates three interconnected rules:
    1. Receipt eligibility (>= 30,000 KRW)
    2. Automated kiosk path (refund < 75,000 KRW → no customs)
    3. Customs inspection path (refund >= 75,000 KRW → customs required)
    """

    @property
    def name(self) -> str:
        return "kr_tax_refund"

    @property
    def description(self) -> str:
        return (
            f"Korean Tax Refund: Receipts must be ≥ {KR_MIN_RECEIPT_AMOUNT:,} KRW. "
            f"Refunds < {KR_CUSTOMS_CHECK_THRESHOLD:,} KRW use automated kiosk. "
            f"Refunds ≥ {KR_CUSTOMS_CHECK_THRESHOLD:,} KRW require customs inspection."
        )

    @property
    def legal_reference(self) -> str:
        return "Korean Tax-Free Shopping Regulations (Incheon International Airport)"

    @property
    def severity(self) -> str:
        return "critical"

    def encode(self, solver: Solver, data: dict[str, Any]) -> None:
        """
        Encode Korean tax refund rules into Z3 constraints.

        Three mathematical constraints are added:
        1. is_eligible ↔ (receipt_amount ≥ 30,000)
        2. refund < 75,000 ⟹ ¬needs_customs_check
        3. refund ≥ 75,000 ⟹ needs_customs_check
        """
        # Step 1: Declare Z3 symbolic variables
        z3_receipt_amount = Int("receipt_amount")
        z3_refund_amount = Int("refund_amount")
        z3_needs_customs_check = Bool("needs_customs_check")
        z3_is_eligible = Bool("is_eligible")

        # Step 2: Encode business rules

        # Rule 1: Eligibility — receipt must be >= 30,000 KRW
        solver.add(z3_is_eligible == (z3_receipt_amount >= KR_MIN_RECEIPT_AMOUNT))

        # Rule 2: Small refund — use automated kiosk, no customs needed
        solver.add(
            Implies(z3_refund_amount < KR_CUSTOMS_CHECK_THRESHOLD, Not(z3_needs_customs_check))
        )

        # Rule 3: Large refund — customs inspection mandatory
        solver.add(
            Implies(z3_refund_amount >= KR_CUSTOMS_CHECK_THRESHOLD, z3_needs_customs_check)
        )

        # Step 3: Bind actual data
        solver.add(z3_receipt_amount == data["receipt_amount"])
        solver.add(z3_refund_amount == data["refund_amount"])
        solver.add(z3_needs_customs_check == BoolVal(data["needs_customs_check"]))
        solver.add(z3_is_eligible == BoolVal(data["is_eligible"]))

    def get_violation_detail(self, data: dict[str, Any]) -> str:
        """Generate a human-readable violation explanation."""
        receipt = data.get("receipt_amount", 0)
        refund = data.get("refund_amount", 0)
        needs_customs = data.get("needs_customs_check", False)
        is_eligible = data.get("is_eligible", False)

        parts = []

        # Check eligibility violation
        if is_eligible and receipt < KR_MIN_RECEIPT_AMOUNT:
            parts.append(
                f"Receipt amount {receipt:,} KRW < minimum {KR_MIN_RECEIPT_AMOUNT:,} KRW, "
                f"but is_eligible is marked as True."
            )
        elif not is_eligible and receipt >= KR_MIN_RECEIPT_AMOUNT:
            parts.append(
                f"Receipt amount {receipt:,} KRW ≥ minimum {KR_MIN_RECEIPT_AMOUNT:,} KRW, "
                f"but is_eligible is marked as False."
            )

        # Check customs violation
        if refund < KR_CUSTOMS_CHECK_THRESHOLD and needs_customs:
            parts.append(
                f"Refund amount {refund:,} KRW < {KR_CUSTOMS_CHECK_THRESHOLD:,} KRW "
                f"does not require customs check, but needs_customs_check is True."
            )
        elif refund >= KR_CUSTOMS_CHECK_THRESHOLD and not needs_customs:
            parts.append(
                f"Refund amount {refund:,} KRW ≥ {KR_CUSTOMS_CHECK_THRESHOLD:,} KRW "
                f"requires customs inspection, but needs_customs_check is False."
            )

        return " | ".join(parts) if parts else "Tax refund rule violation detected."
