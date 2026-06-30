"""
TrustAgent.Forensics — Data Models for Z3 Verification Engine

Defines the Pydantic models used throughout the verification pipeline:
- TransactionData: Input data extracted from user requests
- TaxRefundData: Input data for Korean tax refund scenarios
- RuleViolation: Details about a specific rule violation
- VerificationResult: Final output of the Z3 verification process
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class VerificationStatus(str, Enum):
    """Result status from Z3 solver."""
    SAT = "SAT"         # Satisfiable — action is compliant
    UNSAT = "UNSAT"     # Unsatisfiable — action violates rules
    UNKNOWN = "UNKNOWN" # Solver timed out or encountered errors


class PaymentMethod(str, Enum):
    """Payment method classification."""
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    E_WALLET = "e_wallet"


class TransactionPurpose(str, Enum):
    """Transaction purpose categories."""
    EVENT = "event"
    EQUIPMENT = "equipment"
    SERVICES = "services"
    SALARY = "salary"
    TAX = "tax"
    OTHER = "other"


class RuleSeverity(str, Enum):
    """Severity level of a rule violation."""
    CRITICAL = "critical"    # Must block — legal/regulatory violation
    WARNING = "warning"      # Should review — policy concern
    INFO = "info"           # Informational — best practice suggestion


# =============================================================================
# Input Models
# =============================================================================

class TransactionData(BaseModel):
    """
    Structured transaction data extracted from natural language input
    by the Gemini Semantic Parser (Neural Layer).

    This is the bridge between the Neural and Symbolic layers.
    """
    amount: int = Field(
        ...,
        description="Transaction amount in the smallest currency unit (VND for Vietnam)",
        ge=0,
        examples=[25_000_000, 15_000_000],
    )
    is_cash_payment: bool = Field(
        ...,
        description="Whether the payment is made in cash",
    )
    payment_method: PaymentMethod = Field(
        default=PaymentMethod.CASH,
        description="Specific payment method used",
    )
    purpose: TransactionPurpose = Field(
        default=TransactionPurpose.OTHER,
        description="Purpose/category of the transaction",
    )
    description: str = Field(
        default="",
        description="Original natural language description",
    )
    currency: str = Field(
        default="VND",
        description="ISO 4217 currency code",
    )


class TaxRefundData(BaseModel):
    """
    Structured data for Korean tax refund verification scenario.

    Models the tax refund rules for foreign tourists shopping in South Korea.
    """
    receipt_amount: int = Field(
        ...,
        description="Receipt amount in KRW (Korean Won)",
        ge=0,
        examples=[50_000, 100_000],
    )
    refund_amount: int = Field(
        ...,
        description="Calculated refund amount in KRW",
        ge=0,
        examples=[5_000, 80_000],
    )
    needs_customs_check: bool = Field(
        default=False,
        description="Whether customs inspection is required",
    )
    is_eligible: bool = Field(
        default=True,
        description="Whether the receipt qualifies for tax refund (>= 30,000 KRW)",
    )
    is_tax_free_shop: bool = Field(
        default=True,
        description="Whether the purchase was made at a registered tax-free shop",
    )


# =============================================================================
# Output Models
# =============================================================================

class RuleViolation(BaseModel):
    """Details about a specific business rule violation detected by Z3."""
    rule_name: str = Field(
        ...,
        description="Technical name of the violated rule",
        examples=["vn_cash_payment_threshold"],
    )
    rule_description: str = Field(
        ...,
        description="Human-readable description of the rule",
        examples=["Circular 96/2015/TT-BTC: Cash payments >= 20M VND are not deductible"],
    )
    severity: RuleSeverity = Field(
        default=RuleSeverity.CRITICAL,
        description="Severity level of the violation",
    )
    violation_detail: str = Field(
        ...,
        description="Specific explanation of how the data violates the rule",
        examples=["Amount 25,000,000 VND >= threshold 20,000,000 VND but payment method is cash"],
    )
    legal_reference: str = Field(
        default="",
        description="Reference to the specific law, regulation, or policy",
        examples=["Circular 96/2015/TT-BTC, Article 4, Section 1, Point c"],
    )


class VerificationResult(BaseModel):
    """
    Complete result of the Z3 formal verification process.

    This is the primary output of the Symbolic Layer, containing
    the mathematical proof result and detailed violation information.
    """
    id: UUID = Field(default_factory=uuid4, description="Unique verification ID")
    status: VerificationStatus = Field(
        ...,
        description="SAT (compliant), UNSAT (violation), or UNKNOWN (error)",
    )
    is_compliant: bool = Field(
        ...,
        description="Whether the transaction is compliant with all rules",
    )
    violations: list[RuleViolation] = Field(
        default_factory=list,
        description="List of rule violations (empty if compliant)",
    )
    rules_checked: list[str] = Field(
        default_factory=list,
        description="Names of all rules that were evaluated",
    )
    verification_time_ms: float = Field(
        default=0.0,
        description="Time taken for Z3 verification in milliseconds",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the verification was performed",
    )
    raw_input: dict = Field(
        default_factory=dict,
        description="Original input data that was verified",
    )
    z3_model: Optional[str] = Field(
        default=None,
        description="String representation of Z3 model (if SAT)",
    )
    explanation: str = Field(
        default="",
        description="Human-readable summary of the verification result",
    )

    def to_audit_dict(self) -> dict:
        """Convert to a dictionary suitable for audit trail storage."""
        return {
            "verification_id": str(self.id),
            "status": self.status.value,
            "is_compliant": self.is_compliant,
            "violations": [v.model_dump() for v in self.violations],
            "rules_checked": self.rules_checked,
            "verification_time_ms": self.verification_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "raw_input": self.raw_input,
            "explanation": self.explanation,
        }
