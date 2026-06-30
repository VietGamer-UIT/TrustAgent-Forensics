"""
TrustAgent.Forensics — Prompt Templates for Gemini Semantic Parser

Các prompt này hướng dẫn Gemini 2.0 Flash trích xuất thông tin
từ ngôn ngữ tự nhiên thành JSON có cấu trúc chính xác.

Nguyên tắc thiết kế:
- LLM CHỈ được phép TRÍCH XUẤT dữ liệu, không được ra quyết định tuân thủ
- Mọi quyết định tuân thủ đều do Z3 Theorem Prover xử lý
- Prompt dùng few-shot examples để tăng độ chính xác
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# System prompt dùng chung — giải thích vai trò của LLM
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """Bạn là một bộ phân tích ngữ nghĩa (Semantic Parser) chuyên nghiệp.
Nhiệm vụ DUY NHẤT của bạn là ĐỌC yêu cầu của người dùng và TRÍCH XUẤT thông tin ra JSON.
Bạn KHÔNG được tự đánh giá giao dịch đó có hợp lệ hay không — đó là việc của hệ thống khác.
Chỉ trả về JSON thuần túy, không giải thích, không markdown code block."""


# ---------------------------------------------------------------------------
# Prompt phát hiện loại kịch bản
# ---------------------------------------------------------------------------
DETECT_SCENARIO_PROMPT = """Phân tích câu sau và xác định loại kịch bản:
- "vn_payment": Liên quan đến thanh toán, chi tiêu, chuyển khoản bằng VNĐ tại Việt Nam
- "kr_tax_refund": Liên quan đến hoàn thuế, mua sắm tại Hàn Quốc, KRW, sân bay Incheon
- "unknown": Không thuộc hai loại trên

Câu: "{user_input}"

Trả về JSON: {{"scenario_type": "vn_payment" | "kr_tax_refund" | "unknown"}}"""


# ---------------------------------------------------------------------------
# Prompt trích xuất giao dịch Việt Nam
# ---------------------------------------------------------------------------
VN_PAYMENT_EXTRACT_PROMPT = """Trích xuất thông tin thanh toán từ câu sau thành JSON.

QUY TẮC:
- amount: Số tiền bằng VNĐ (số nguyên, không có dấu chấm/phẩy)
- is_cash_payment: true nếu là "tiền mặt", false nếu "chuyển khoản/ngân hàng/thẻ/ví điện tử"
- payment_method: "cash" | "bank_transfer" | "credit_card" | "e_wallet"
- purpose: "event" | "equipment" | "services" | "salary" | "tax" | "other"
- description: Sao chép nguyên văn mục đích từ câu gốc

VÍ DỤ:
Input: "Thanh toán tiền mặt 25 triệu cho chi phí tổ chức sự kiện"
Output: {{"amount": 25000000, "is_cash_payment": true, "payment_method": "cash", "purpose": "event", "description": "chi phí tổ chức sự kiện", "confidence": 0.98}}

Input: "Chuyển khoản 30.000.000 đồng mua thiết bị văn phòng"
Output: {{"amount": 30000000, "is_cash_payment": false, "payment_method": "bank_transfer", "purpose": "equipment", "description": "mua thiết bị văn phòng", "confidence": 0.97}}

Input: "Chi 15tr tiền mặt văn phòng phẩm"
Output: {{"amount": 15000000, "is_cash_payment": true, "payment_method": "cash", "purpose": "other", "description": "văn phòng phẩm", "confidence": 0.92}}

Input: "Pay 25 million VND cash for event costs"
Output: {{"amount": 25000000, "is_cash_payment": true, "payment_method": "cash", "purpose": "event", "description": "event costs", "confidence": 0.95}}

Bây giờ trích xuất:
Input: "{user_input}"
Output:"""


# ---------------------------------------------------------------------------
# Prompt trích xuất hoàn thuế Hàn Quốc
# ---------------------------------------------------------------------------
KR_REFUND_EXTRACT_PROMPT = """Trích xuất thông tin hoàn thuế Hàn Quốc từ câu sau thành JSON.

QUY TẮC:
- receipt_amount: Giá trị hóa đơn bằng KRW (số nguyên)
- refund_amount: Số tiền được hoàn thuế bằng KRW (số nguyên, thường ~10% receipt)
- is_tax_free_shop: true nếu mua ở cửa hàng miễn thuế (tax-free shop)
- is_eligible: true nếu receipt_amount >= 30000 KRW
- needs_customs_check: true nếu refund_amount >= 75000 KRW
- Nếu chỉ có receipt_amount, tự tính refund_amount = receipt_amount * 0.1 (làm tròn)

VÍ DỤ:
Input: "Mua hàng 50,000 KRW tại duty-free Incheon, hoàn thuế 5,000 KRW"
Output: {{"receipt_amount": 50000, "refund_amount": 5000, "is_tax_free_shop": true, "is_eligible": true, "needs_customs_check": false, "confidence": 0.97}}

Input: "Mua hàng 1,000,000 won, hoàn 80,000 won tại sân bay"
Output: {{"receipt_amount": 1000000, "refund_amount": 80000, "is_tax_free_shop": true, "is_eligible": true, "needs_customs_check": true, "confidence": 0.95}}

Input: "Bought goods worth 20,000 KRW, want tax refund"
Output: {{"receipt_amount": 20000, "refund_amount": 2000, "is_tax_free_shop": true, "is_eligible": false, "needs_customs_check": false, "confidence": 0.90}}

Bây giờ trích xuất:
Input: "{user_input}"
Output:"""


# ---------------------------------------------------------------------------
# Prompt tạo phản hồi thân thiện cho người dùng
# ---------------------------------------------------------------------------
EXPLAIN_RESULT_PROMPT = """Dựa trên kết quả kiểm tra dưới đây, viết một câu phản hồi thân thiện bằng tiếng Việt cho người dùng.
Ngắn gọn (1-3 câu), rõ ràng, không dùng thuật ngữ kỹ thuật phức tạp.

Yêu cầu gốc: "{original_request}"
Kết quả: {status}
Chi tiết vi phạm: {violations}

Nếu APPROVED: Xác nhận giao dịch được phê duyệt và lý do.
Nếu BLOCKED: Giải thích lý do bị chặn và gợi ý giải pháp thay thế."""
