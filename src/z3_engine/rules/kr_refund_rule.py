"""
TrustAgent.Forensics — Korean Tax Refund Rule (Updated: Dynamic Thresholds)

Căn cứ pháp lý: Korean Tax-Free Shopping Regulations (Incheon International Airport)
──────────────────────────────────────────────────────────────────────────────────────
Quy tắc 1: Hóa đơn phải >= 30,000 KRW mới đủ điều kiện hoàn thuế.
Quy tắc 2: Hoàn thuế < 75,000 KRW → dùng kiosk tự động (không cần hải quan).
Quy tắc 3: Hoàn thuế >= 75,000 KRW → bắt buộc kiểm tra hải quan.

Cập nhật Phase 3.5:
    - encode() nhận thêm dynamic_thresholds từ Legal RAG Node
    - KR_MIN_RECEIPT_AMOUNT và KR_CUSTOMS_CHECK_THRESHOLD có thể inject từ RAG
    - Nếu dynamic_thresholds không có → dùng defaults (30K / 75K KRW)
    - Backward compatible với tất cả tests cũ
"""

from __future__ import annotations

from typing import Any

from z3 import Solver, Int, Bool, BoolVal, Implies, Not

from .base_rule import BusinessRule


# Ngưỡng mặc định (fallback khi RAG không available)
KR_MIN_RECEIPT_AMOUNT_DEFAULT = 30_000       # 30,000 KRW — ngưỡng tối thiểu hóa đơn
KR_CUSTOMS_CHECK_THRESHOLD_DEFAULT = 75_000  # 75,000 KRW — ngưỡng bắt buộc hải quan


class KoreaTaxRefundRule(BusinessRule):
    """
    Kiểm chứng quy định hoàn thuế cho khách du lịch nước ngoài tại Hàn Quốc.

    Xác thực 3 ràng buộc liên kết nhau:
    1. Điều kiện đủ tư cách: receipt >= KR_MIN_RECEIPT_AMOUNT
    2. Kiosk tự động: refund < KR_CUSTOMS_CHECK_THRESHOLD → không cần hải quan
    3. Hải quan bắt buộc: refund >= KR_CUSTOMS_CHECK_THRESHOLD → cần hải quan

    Ngưỡng có thể được inject động từ Legal RAG Module.
    """

    @property
    def name(self) -> str:
        return "kr_tax_refund"

    @property
    def description(self) -> str:
        return (
            f"Korean Tax Refund: Receipts must be ≥ {KR_MIN_RECEIPT_AMOUNT_DEFAULT:,} KRW. "
            f"Refunds < {KR_CUSTOMS_CHECK_THRESHOLD_DEFAULT:,} KRW use automated kiosk. "
            f"Refunds ≥ {KR_CUSTOMS_CHECK_THRESHOLD_DEFAULT:,} KRW require customs inspection."
        )

    @property
    def legal_reference(self) -> str:
        return "Korean Tax-Free Shopping Regulations (Incheon International Airport)"

    @property
    def severity(self) -> str:
        return "critical"

    def encode(
        self,
        solver: Solver,
        data: dict[str, Any],
        dynamic_thresholds: dict[str, int] | None = None,
    ) -> None:
        """
        Mã hóa 3 quy tắc hoàn thuế Hàn Quốc vào Z3.

        Args:
            solver: Z3 Solver instance
            data: Dict giao dịch, cần có:
                  - 'receipt_amount' (int, KRW)
                  - 'refund_amount' (int, KRW)
                  - 'needs_customs_check' (bool)
                  - 'is_eligible' (bool)
            dynamic_thresholds: Dict từ Legal RAG Node.
                                Keys: 'KR_MIN_RECEIPT_AMOUNT', 'KR_CUSTOMS_CHECK_THRESHOLD'
                                None → dùng defaults (30K / 75K KRW)

        ⚠️ Lưu ý Z3 type safety:
            - Tất cả Bool variable PHẢI dùng BoolVal() — không dùng Python bool trực tiếp
            - Int variable có thể so sánh với Python int trực tiếp: Z3 tự convert
        """
        # Lấy thresholds từ RAG hoặc dùng fallback
        thresholds = dynamic_thresholds or {}
        min_receipt: int = int(thresholds.get("KR_MIN_RECEIPT_AMOUNT", KR_MIN_RECEIPT_AMOUNT_DEFAULT))
        customs_threshold: int = int(thresholds.get("KR_CUSTOMS_CHECK_THRESHOLD", KR_CUSTOMS_CHECK_THRESHOLD_DEFAULT))

        # Bước 1: Khai báo biến Z3 symbolic
        z3_receipt_amount = Int("receipt_amount")
        z3_refund_amount = Int("refund_amount")
        z3_needs_customs_check = Bool("needs_customs_check")
        z3_is_eligible = Bool("is_eligible")

        # Bước 2: Mã hóa 3 quy tắc pháp lý

        # Quy tắc 1: Điều kiện đủ tư cách ↔ (receipt >= min_receipt)
        solver.add(z3_is_eligible == (z3_receipt_amount >= min_receipt))

        # Quy tắc 2: Hoàn nhỏ → kiosk tự động, KHÔNG cần hải quan
        solver.add(
            Implies(z3_refund_amount < customs_threshold, Not(z3_needs_customs_check))
        )

        # Quy tắc 3: Hoàn lớn → BẮT BUỘC hải quan
        solver.add(
            Implies(z3_refund_amount >= customs_threshold, z3_needs_customs_check)
        )

        # Bước 3: Bind dữ liệu thực tế
        # ✅ Int so sánh với Python int: Z3 tự xử lý
        solver.add(z3_receipt_amount == data["receipt_amount"])
        solver.add(z3_refund_amount == data["refund_amount"])
        # ✅ Bool PHẢI dùng BoolVal()
        solver.add(z3_needs_customs_check == BoolVal(data["needs_customs_check"]))
        solver.add(z3_is_eligible == BoolVal(data["is_eligible"]))

    def get_violation_detail(self, data: dict[str, Any]) -> str:
        """Tạo giải thích vi phạm thân thiện."""
        receipt = data.get("receipt_amount", 0)
        refund = data.get("refund_amount", 0)
        needs_customs = data.get("needs_customs_check", False)
        is_eligible = data.get("is_eligible", False)

        parts: list[str] = []

        if is_eligible and receipt < KR_MIN_RECEIPT_AMOUNT_DEFAULT:
            parts.append(
                f"Hóa đơn {receipt:,} KRW < tối thiểu {KR_MIN_RECEIPT_AMOUNT_DEFAULT:,} KRW, "
                f"nhưng is_eligible được đánh dấu True."
            )
        elif not is_eligible and receipt >= KR_MIN_RECEIPT_AMOUNT_DEFAULT:
            parts.append(
                f"Hóa đơn {receipt:,} KRW ≥ tối thiểu {KR_MIN_RECEIPT_AMOUNT_DEFAULT:,} KRW, "
                f"nhưng is_eligible được đánh dấu False."
            )

        if refund < KR_CUSTOMS_CHECK_THRESHOLD_DEFAULT and needs_customs:
            parts.append(
                f"Hoàn {refund:,} KRW < {KR_CUSTOMS_CHECK_THRESHOLD_DEFAULT:,} KRW "
                f"không cần hải quan, nhưng needs_customs_check = True."
            )
        elif refund >= KR_CUSTOMS_CHECK_THRESHOLD_DEFAULT and not needs_customs:
            parts.append(
                f"Hoàn {refund:,} KRW ≥ {KR_CUSTOMS_CHECK_THRESHOLD_DEFAULT:,} KRW "
                f"phải kiểm tra hải quan, nhưng needs_customs_check = False."
            )

        return " | ".join(parts) if parts else "Vi phạm quy định hoàn thuế Hàn Quốc."
