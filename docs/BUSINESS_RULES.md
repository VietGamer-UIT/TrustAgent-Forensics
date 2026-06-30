# 📜 Các Quy Tắc Kinh Doanh — Business Rules

> Tài liệu kỹ thuật cho từng bộ luật được mã hóa vào Z3 Theorem Prover

---

## 🇻🇳 VN-01: Quy Tắc Tiền Mặt Việt Nam

**Class**: `VietnamCashPaymentRule`  
**File**: `src/z3_engine/rules/vn_tax_rule.py`  
**Rule ID**: `vn_cash_payment_threshold`  
**Severity**: `critical`

### Căn cứ pháp lý

> Thông tư 96/2015/TT-BTC, Điều 4, Khoản 1, Điểm c  
> *"Mọi khoản chi phí mua hàng hóa, dịch vụ từng lần có giá trị từ 20 triệu đồng trở lên (đã bao gồm thuế GTGT) bắt buộc phải có chứng từ thanh toán không dùng tiền mặt thì mới được ghi nhận là chi phí hợp lý được trừ khi tính thuế."*

### Mã hóa Z3

```python
VN_CASH_THRESHOLD = 20_000_000  # 20 triệu VNĐ

# Logic toán học:
# "Nếu số tiền >= 20M thì PHẢI thanh toán KHÔNG bằng tiền mặt"
Implies(amount >= 20_000_000, Not(is_cash_payment))
```

### Bảng quyết định

| amount (VNĐ) | is_cash_payment | Z3 Result | Lý do |
|-------------|----------------|-----------|-------|
| 25,000,000 | True | `unsat` ❌ | Vi phạm: >= 20M mà dùng tiền mặt |
| 30,000,000 | False | `sat` ✅ | Hợp lệ: >= 20M nhưng chuyển khoản |
| 15,000,000 | True | `sat` ✅ | Hợp lệ: < 20M được dùng tiền mặt |
| 20,000,000 | True | `unsat` ❌ | Vi phạm: đúng bằng ngưỡng |
| 20,000,000 | False | `sat` ✅ | Hợp lệ: đúng bằng ngưỡng + chuyển khoản |
| 19,999,999 | True | `sat` ✅ | Hợp lệ: dưới ngưỡng 1 đồng |
| 0 | True | `sat` ✅ | Hợp lệ: giao dịch 0 đồng |

### Input schema (data dict)

```python
{
    "amount": int,           # >= 0 (VNĐ)
    "is_cash_payment": bool, # True = tiền mặt
    # optional fields (ignored by Z3):
    "payment_method": str,
    "purpose": str,
    "description": str,
    "currency": str,
}
```

---

## 🇰🇷 KR-01: Quy Tắc Hoàn Thuế Hàn Quốc

**Class**: `KoreaTaxRefundRule`  
**File**: `src/z3_engine/rules/kr_refund_rule.py`  
**Rule ID**: `kr_tax_refund`  
**Severity**: `critical`

### Căn cứ pháp lý

> Korean Tax-Free Shopping Regulations (Sân bay Incheon International)
> - Hóa đơn tối thiểu: 30,000 KRW để đủ điều kiện hoàn thuế
> - Hoàn dưới 75,000 KRW: Dùng kiosk tự động tại sân bay
> - Hoàn từ 75,000 KRW trở lên: Bắt buộc qua kiểm tra hải quan

### Mã hóa Z3 (3 ràng buộc liên kết)

```python
KR_MIN_RECEIPT_AMOUNT = 30_000   # 30,000 KRW
KR_CUSTOMS_CHECK_THRESHOLD = 75_000  # 75,000 KRW

# Ràng buộc 1: Điều kiện đủ tư cách hoàn thuế
solver.add(is_eligible == (receipt_amount >= 30_000))

# Ràng buộc 2: Hoàn nhỏ → kiosk tự động (không cần hải quan)
solver.add(Implies(refund_amount < 75_000, Not(needs_customs_check)))

# Ràng buộc 3: Hoàn lớn → bắt buộc hải quan
solver.add(Implies(refund_amount >= 75_000, needs_customs_check))
```

### Bảng quyết định

| receipt (KRW) | refund (KRW) | is_eligible | needs_customs | Z3 Result |
|--------------|-------------|------------|--------------|-----------|
| 50,000 | 5,000 | True | False | `sat` ✅ |
| 1,000,000 | 80,000 | True | True | `sat` ✅ |
| 1,000,000 | 80,000 | True | False | `unsat` ❌ Phải qua hải quan |
| 50,000 | 5,000 | True | True | `unsat` ❌ Không cần hải quan |
| 20,000 | 2,000 | False | False | `unsat` ❌ Hóa đơn < 30K |
| 30,000 | 3,000 | True | False | `sat` ✅ Đúng ngưỡng tối thiểu |
| 75,000 | 7,500 | True | True | `sat` ✅ Đúng ngưỡng hải quan |

### Input schema (data dict)

```python
{
    "receipt_amount": int,       # >= 0 (KRW)
    "refund_amount": int,        # >= 0 (KRW)
    "needs_customs_check": bool, # True = cần hải quan
    "is_eligible": bool,         # True = đủ điều kiện
    # optional:
    "is_tax_free_shop": bool,
}
```

---

## Thêm Rule Mới

### 1. Chọn Rule ID
- Format: `{country_code}_{short_description}` (lowercase, underscore)
- Ví dụ: `jp_consumption_tax`, `us_sales_tax`, `vn_vat_refund`

### 2. Template

```python
"""
Docstring giải thích rule, căn cứ pháp lý
"""
from z3 import Solver, Int, Bool, BoolVal, Implies, Not
from .base_rule import BusinessRule

THRESHOLD = 0  # Hằng số theo quy định pháp luật

class NewRule(BusinessRule):
    @property
    def name(self) -> str:
        return "new_rule_id"  # unique, lowercase

    @property
    def description(self) -> str:
        return "Mô tả ngắn gọn rule này làm gì"

    @property
    def legal_reference(self) -> str:
        return "Số hiệu văn bản, điều khoản cụ thể"

    @property
    def severity(self) -> str:
        return "critical"  # critical | warning | info

    def encode(self, solver: Solver, data: dict) -> None:
        # 1. Khai báo biến Z3
        # 2. Thêm quy tắc
        # 3. Bind dữ liệu (nhớ BoolVal cho bool!)
        pass

    def get_violation_detail(self, data: dict) -> str:
        return "Mô tả cụ thể tại sao vi phạm, gợi ý giải pháp"
```

### 3. Đăng ký và test

```python
# Trong solver
solver.register_rule(NewRule())

# Test SAT (hợp lệ)
result = solver.verify(valid_data, rule_names=["new_rule_id"])
assert result.status == VerificationStatus.SAT

# Test UNSAT (vi phạm)
result = solver.verify(invalid_data, rule_names=["new_rule_id"])
assert result.status == VerificationStatus.UNSAT
```

---

## Thứ tự ưu tiên khi nhiều rule

```python
# TrustAgentSolver chạy TẤT CẢ rules trong cùng 1 Z3 Solver instance
# → Nếu BẤT KỲ rule nào unsat → toàn bộ kết quả là UNSAT

solver.register_rule(VietnamCashPaymentRule())  # rule 1
solver.register_rule(KoreaTaxRefundRule())       # rule 2

# Khi verify, có thể chỉ định rules cụ thể:
result = solver.verify(data, rule_names=["vn_cash_payment_threshold"])
# Hoặc check tất cả:
result = solver.verify(data)  # rule_names=None → check all
```
