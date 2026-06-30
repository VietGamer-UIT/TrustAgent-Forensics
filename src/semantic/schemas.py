"""
TrustAgent.Forensics — JSON Schema Definitions for Semantic Parsing

These Pydantic schemas define the EXACT structure that the Gemini LLM
must produce when parsing natural language inputs. They act as the
contract between the Neural layer and the Symbolic Z3 layer.

Design principle: The LLM's job is ONLY to map language → JSON.
All business logic stays in Z3. This strict separation prevents
prompt injection from influencing compliance decisions.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ScenarioType(str, Enum):
    """The type of business scenario being parsed."""
    VN_PAYMENT = "vn_payment"       # Vietnamese tax payment
    KR_TAX_REFUND = "kr_tax_refund" # Korean tax refund
    UNKNOWN = "unknown"             # Cannot determine


class ParsedVNTransaction(BaseModel):
    """
    Structured output from Gemini when parsing a Vietnamese payment request.

    Maps to TransactionData in z3_engine/models.py for Z3 verification.
    """
    amount: int = Field(
        ...,
        description="Transaction amount in VND (Vietnamese Dong)",
        ge=0,
        examples=[25_000_000, 15_000_000],
    )
    is_cash_payment: bool = Field(
        ...,
        description="True if payment is in cash (tiền mặt), False for bank transfer/card",
    )
    payment_method: str = Field(
        default="cash",
        description="Payment method: 'cash', 'bank_transfer', 'credit_card', or 'e_wallet'",
    )
    purpose: str = Field(
        default="other",
        description="Purpose category: 'event', 'equipment', 'services', 'salary', 'tax', 'other'",
    )
    description: str = Field(
        default="",
        description="Original description extracted from user input",
    )
    confidence: float = Field(
        default=1.0,
        description="LLM confidence in extraction (0.0–1.0)",
        ge=0.0,
        le=1.0,
    )
    raw_input: str = Field(
        default="",
        description="The original natural language input",
    )


class ParsedKRTaxRefund(BaseModel):
    """
    Structured output from Gemini when parsing a Korean tax refund scenario.

    Maps to TaxRefundData in z3_engine/models.py for Z3 verification.
    """
    receipt_amount: int = Field(
        ...,
        description="Receipt amount in KRW (Korean Won)",
        ge=0,
        examples=[50_000, 100_000],
    )
    refund_amount: int = Field(
        ...,
        description="Tax refund amount in KRW",
        ge=0,
        examples=[5_000, 80_000],
    )
    needs_customs_check: bool = Field(
        default=False,
        description="Whether customs inspection is required (AI-determined from rules)",
    )
    is_eligible: bool = Field(
        default=True,
        description="Whether receipt qualifies for tax refund (>= 30,000 KRW)",
    )
    is_tax_free_shop: bool = Field(
        default=True,
        description="Whether purchase was at a registered tax-free shop",
    )
    confidence: float = Field(
        default=1.0,
        description="LLM confidence in extraction (0.0–1.0)",
        ge=0.0,
        le=1.0,
    )
    raw_input: str = Field(
        default="",
        description="The original natural language input",
    )


class ParseResult(BaseModel):
    """
    Top-level result from the Semantic Parser.

    Contains the detected scenario type and the structured data,
    ready to be passed to the Z3 verification engine.
    """
    scenario_type: ScenarioType = Field(
        ...,
        description="The type of scenario detected in user input",
    )
    vn_transaction: Optional[ParsedVNTransaction] = Field(
        default=None,
        description="Parsed Vietnamese payment data (if scenario_type == VN_PAYMENT)",
    )
    kr_tax_refund: Optional[ParsedKRTaxRefund] = Field(
        default=None,
        description="Parsed Korean tax refund data (if scenario_type == KR_TAX_REFUND)",
    )
    parse_error: Optional[str] = Field(
        default=None,
        description="Error message if parsing failed",
    )

    def to_z3_data(self) -> dict:
        """Convert parsed result to dict for Z3 verification."""
        if self.scenario_type == ScenarioType.VN_PAYMENT and self.vn_transaction:
            return self.vn_transaction.model_dump(
                exclude={"confidence", "raw_input"}
            )
        elif self.scenario_type == ScenarioType.KR_TAX_REFUND and self.kr_tax_refund:
            return self.kr_tax_refund.model_dump(
                exclude={"confidence", "raw_input"}
            )
        return {}

    def get_applicable_rules(self) -> list[str]:
        """Return the rule names to check for this scenario."""
        mapping = {
            ScenarioType.VN_PAYMENT: ["vn_cash_payment_threshold"],
            ScenarioType.KR_TAX_REFUND: ["kr_tax_refund"],
            ScenarioType.UNKNOWN: [],
        }
        return mapping.get(self.scenario_type, [])
