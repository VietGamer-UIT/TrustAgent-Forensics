"""
TrustAgent.Forensics — Vietnamese Tax Cash Payment Rule (Updated: Dynamic Thresholds)

Căn cứ pháp lý: Thông tư 96/2015/TT-BTC, Điều 4, Khoản 1, Điểm c
───────────────────────────────────────────────────────────────────
"Mọi khoản chi phí mua hàng hóa, dịch vụ từng lần có giá trị
từ 20 triệu đồng trở lên (đã bao gồm thuế GTGT) bắt buộc phải
có chứng từ thanh toán không dùng tiền mặt thì mới được ghi nhận
là chi phí hợp lý được trừ khi tính thuế."

Z3 Encoding:
    Implies(amount >= VN_CASH_THRESHOLD, Not(is_cash_payment))
    Giá trị VN_CASH_THRESHOLD được inject từ Legal RAG Module.

Cập nhật Phase 3.5:
    - encode() nhận thêm dynamic_thresholds từ Legal RAG Node
    - Nếu dynamic_thresholds không có → dùng VN_CASH_THRESHOLD mặc định (20M VNĐ)
    - Backward compatible: các test cũ không cần truyền dynamic_thresholds
"""

from __future__ import annotations

from typing import Any

from z3 import Solver, Int, Bool, BoolVal, Implies, Not

from .base_rule import BusinessRule


# Ngưỡng mặc định (fallback khi RAG không available)
# Định nghĩa bởi Thông tư 96/2015/TT-BTC, Điều 4, Khoản 1, Điểm c
VN_CASH_THRESHOLD_DEFAULT = 20_000_000  # 20 triệu VNĐ


class VietnamCashPaymentRule(BusinessRule):
    """
    Kiểm chứng quy định thanh toán tiền mặt của Việt Nam.

    Bất kỳ giao dịch nào >= VN_CASH_THRESHOLD VNĐ mà dùng tiền mặt
    sẽ bị đánh dấu UNSAT (không tuân thủ).

    Ngưỡng có thể được inject động từ Legal RAG Module thay vì hardcode.
    """

    @property
    def name(self) -> str:
        return "vn_cash_payment_threshold"

    @property
    def description(self) -> str:
        return (
            f"Thông tư 96/2015/TT-BTC: Chi phí mua hàng hóa/dịch vụ từ "
            f"{VN_CASH_THRESHOLD_DEFAULT:,} VNĐ trở lên phải thanh toán "
            f"không dùng tiền mặt để được ghi nhận là chi phí được trừ thuế."
        )

    @property
    def legal_reference(self) -> str:
        return "Thông tư 96/2015/TT-BTC, Điều 4, Khoản 1, Điểm c"

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
        Mã hóa quy tắc thanh toán tiền mặt vào Z3.

        Công thức toán học:
            ∀ giao dịch: amount ≥ VN_CASH_THRESHOLD ⟹ ¬is_cash_payment

        Args:
            solver: Z3 Solver instance
            data: Dict giao dịch, cần có key 'amount' (int) và 'is_cash_payment' (bool)
            dynamic_thresholds: Dict từ Legal RAG Node.
                                Key: 'VN_CASH_THRESHOLD', Value: int (VNĐ)
                                None → dùng VN_CASH_THRESHOLD_DEFAULT (20M VNĐ)

        ⚠️ Lưu ý Z3 type safety:
            - Z3 Int variable so sánh với Python int: OK trực tiếp
            - Z3 Bool variable phải dùng BoolVal() — không dùng Python bool trực tiếp
        """
        # Lấy threshold từ RAG hoặc dùng fallback
        threshold: int = int(
            (dynamic_thresholds or {}).get("VN_CASH_THRESHOLD", VN_CASH_THRESHOLD_DEFAULT)
        )

        # Bước 1: Khai báo biến Z3 symbolic
        z3_amount = Int("amount")
        z3_is_cash = Bool("is_cash")

        # Bước 2: Mã hóa quy tắc pháp lý
        # "Nếu số tiền >= threshold, thì KHÔNG được dùng tiền mặt"
        solver.add(Implies(z3_amount >= threshold, Not(z3_is_cash)))

        # Bước 3: Bind dữ liệu thực tế
        # ✅ Int so sánh với Python int: Z3 tự xử lý
        solver.add(z3_amount == data["amount"])
        # ✅ Bool phải dùng BoolVal() — đây là gotcha của Z3
        solver.add(z3_is_cash == BoolVal(data["is_cash_payment"]))

    def get_violation_detail(self, data: dict[str, Any]) -> str:
        """Tạo giải thích vi phạm thân thiện với ngưỡng thực tế."""
        amount = data.get("amount", 0)
        return (
            f"Số tiền {amount:,} VNĐ ≥ ngưỡng {VN_CASH_THRESHOLD_DEFAULT:,} VNĐ "
            f"nhưng phương thức thanh toán là tiền mặt. "
            f"Theo Thông tư 96/2015/TT-BTC, khoản chi này sẽ KHÔNG được "
            f"ghi nhận là chi phí được trừ khi tính thuế TNDN. "
            f"Yêu cầu chuyển sang thanh toán qua ngân hàng."
        )
