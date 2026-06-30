# 🧠 Hướng dẫn cho Claude AI — `claude.md`

> File này được đọc bởi **Claude AI models** (Claude Sonnet, Claude Opus...)  
> khi làm việc với dự án TrustAgent.Forensics.

---

## Dự án là gì?

**TrustAgent.Forensics** — Nền tảng quản trị AI (AI Governance) dùng kiến trúc Neuro-Symbolic:

- **Mục tiêu**: Đảm bảo AI Agents luôn tuân thủ pháp luật khi thực thi tự động
- **Cách làm**: LLM hiểu ngôn ngữ → Z3 kiểm tra luật toán học → Không thể bypass
- **Đối tượng**: Doanh nghiệp VN + KR dùng AI để xử lý tài chính/kế toán
- **Cuộc thi**: INNOSTAR 2026 (khởi nghiệp sinh viên VN-KR)

**Tech stack 2026**: Python 3.12, Z3 4.16, Gemini 2.0 Flash, LangGraph 0.4, FastAPI 0.115, PostgreSQL 17

---

## Trạng thái hiện tại

| Phase | Files chính | Trạng thái |
|-------|------------|------------|
| **Phase 1** — Z3 Engine | `src/z3_engine/` | ✅ Hoàn thành, 26 tests |
| **Phase 2** — Semantic Parser | `src/semantic/` | ✅ Hoàn thành, 24 tests |
| **Phase 3** — LangGraph | `src/agents/` | 🔜 Chưa làm |
| **Phase 4** — FastAPI + DB | `src/api/`, `src/database/` | 🔜 Chưa làm |
| **Phase 5** — Dashboard | `src/dashboard/` | 🔜 Chưa làm |
| **Phase 6** — Docker/Demo | Root | 🔜 Chưa làm |

**Tổng tests hiện tại**: 50 passed, 0 failed

---

## Codebase Map quan trọng

### Z3 Engine (Symbolic Layer)

```
src/z3_engine/
├── models.py        # Pydantic models: TransactionData, TaxRefundData,
│                    # VerificationResult, RuleViolation, VerificationStatus
├── solver.py        # TrustAgentSolver — đăng ký/thực thi rule
└── rules/
    ├── base_rule.py        # BusinessRule (abstract) — template cho mọi rule
    ├── vn_tax_rule.py      # VietnamCashPaymentRule: >= 20M VND phải chuyển khoản
    └── kr_refund_rule.py   # KoreaTaxRefundRule: 30K/75K KRW thresholds
```

### Semantic Layer (Neural Layer)

```
src/semantic/
├── schemas.py   # ParseResult, ParsedVNTransaction, ParsedKRTaxRefund, ScenarioType
├── prompts.py   # SYSTEM_PROMPT, DETECT_SCENARIO_PROMPT, VN/KR extract prompts
└── parser.py    # SemanticParser → GeminiSemanticParser | MockSemanticParser
```

---

## Những quy tắc cực kỳ quan trọng khi code

### ⚠️ Rule 1: BoolVal() với Z3

```python
# ❌ SAI — Python True/False không hoạt động đúng với Z3 Bool khi dùng ==
solver.add(z3_bool_var == data["is_cash"])  # Có thể gây lỗi ngầm

# ✅ ĐÚNG — luôn wrap bằng BoolVal()
from z3 import BoolVal
solver.add(z3_bool_var == BoolVal(data["is_cash"]))
```

### ⚠️ Rule 2: Z3 variable name phải match với data dict key

```python
# Trong rule: tên biến Z3 là "amount"
z3_amount = Int("amount")
solver.add(z3_amount == data["amount"])  # data phải có key "amount"

# Trong TaxRefundData model: field là "receipt_amount"
z3_receipt = Int("receipt_amount")
solver.add(z3_receipt == data["receipt_amount"])  # match!
```

### ⚠️ Rule 3: Mỗi verify() dùng Solver mới

```python
# ✅ TrustAgentSolver tạo Solver() mới cho mỗi lần verify
# Không bao giờ reuse Solver() — tránh state leakage
```

---

## API quan trọng

### TrustAgentSolver

```python
from src.z3_engine.solver import TrustAgentSolver
from src.z3_engine.rules.vn_tax_rule import VietnamCashPaymentRule

solver = TrustAgentSolver()
solver.register_rule(VietnamCashPaymentRule())

result = solver.verify(
    data={"amount": 25_000_000, "is_cash_payment": True},
    rule_names=["vn_cash_payment_threshold"],  # None = check all
)
# result.status: VerificationStatus.SAT | UNSAT
# result.is_compliant: bool
# result.violations: list[RuleViolation]
# result.verification_time_ms: float
```

### SemanticParser

```python
from src.semantic.parser import SemanticParser

parser = SemanticParser(api_key="")  # Mock (dev)
# parser = SemanticParser.from_config()  # Real Gemini (production)

result = parser.parse("Thanh toán tiền mặt 25 triệu cho sự kiện")
# result.scenario_type: ScenarioType.VN_PAYMENT
# result.to_z3_data(): {"amount": 25000000, "is_cash_payment": True, ...}
# result.get_applicable_rules(): ["vn_cash_payment_threshold"]
```

### End-to-End Pipeline

```python
# 1. Parse
parse_result = parser.parse(user_input)

# 2. Verify
verify_result = solver.verify(
    parse_result.to_z3_data(),
    rule_names=parse_result.get_applicable_rules()
)

# 3. Explain
explanation = parser.explain_result(
    user_input,
    verify_result.status.value,
    verify_result.violations
)
```

---

## Thêm rule mới (checklist)

- [ ] Tạo `src/z3_engine/rules/<country>_<name>_rule.py`
- [ ] Kế thừa `BusinessRule`, implement 4 properties + `encode()` + `get_violation_detail()`
- [ ] Thêm Z3 variables với tên khớp data keys
- [ ] Thêm `BoolVal()` cho mọi boolean binding
- [ ] Cập nhật `TaxRefundData` hoặc tạo model mới trong `models.py` nếu cần field mới
- [ ] Thêm `ScenarioType` mới trong `schemas.py` nếu cần
- [ ] Viết tests trong `tests/test_z3_engine.py` — cả SAT lẫn UNSAT cases
- [ ] Cập nhật `docs/BUSINESS_RULES.md`

---

## Phong cách code của dự án

```python
# Docstring: tiếng Việt cho business context
"""
Thực thi quy tắc thanh toán VN theo Thông tư 96/2015.
Các giao dịch >= 20M VND phải dùng phương thức phi tiền mặt.
"""

# Hằng số: comment giải thích ngữ cảnh pháp lý
VN_CASH_THRESHOLD = 20_000_000  # Thông tư 96/2015/TT-BTC, Điều 4, Khoản 1, Điểm c

# Logging thay vì print
import logging
logger = logging.getLogger(__name__)
logger.info("Rule registered")  # không phải print()

# Type hints bắt buộc
def verify(self, data: dict[str, Any], rule_names: list[str] | None = None) -> VerificationResult:
```

---

## Không làm những điều này

```python
# ❌ Không để LLM ra quyết định tuân thủ
if llm.says_compliant(transaction): approve()  # SAI KIẾN TRÚC

# ❌ Không bỏ qua type hints
def verify(data, rules):  # Thiếu type hints

# ❌ Không reuse Solver() giữa các lần verify
self.solver = Solver()  # Tạo trong __init__ và reuse — SAI

# ❌ Không raise Exception trực tiếp ra user
raise Exception("Z3 error")  # Dùng logging + return UNKNOWN status thay thế
```
