# 🤖 Hướng dẫn cho Gemini AI — `gemini.md`

> File này được đọc bởi **Gemini AI models** (Gemini 2.0 Flash, Gemini 1.5 Pro...)  
> khi làm việc với dự án TrustAgent.Forensics.

---

## Tổng quan dự án

**TrustAgent.Forensics** là một nền tảng AI Governance Neuro-Symbolic:
- **Neural Layer**: Gemini 2.0 Flash — hiểu ngôn ngữ tự nhiên → JSON
- **Symbolic Layer**: Z3 Theorem Prover — kiểm tra tuân thủ pháp luật
- **Forensics Layer**: PostgreSQL — lưu audit trail bất biến

**Ngôn ngữ**: Python 3.12+  
**Repo**: https://github.com/VietGamer-UIT/TrustAgent-Forensics

---

## Kiến trúc module

```
src/
├── z3_engine/          # Phase 1 ✅ DONE
│   ├── solver.py       # TrustAgentSolver
│   ├── models.py       # Pydantic models
│   └── rules/          # VN + KR business rules
├── semantic/           # Phase 2 ✅ DONE
│   ├── parser.py       # SemanticParser (Gemini + Mock)
│   ├── prompts.py      # Prompt templates
│   └── schemas.py      # Output schemas
├── agents/             # Phase 3 🔜
├── api/                # Phase 4 🔜
├── database/           # Phase 4 🔜
└── dashboard/          # Phase 5 🔜
```

---

## Các quy ước lập trình quan trọng

### 1. Naming Conventions
```python
# Classes: PascalCase
class TrustAgentSolver: ...
class VietnamCashPaymentRule: ...

# Functions/variables: snake_case
def verify(self, data: dict) -> VerificationResult: ...
rule_name = "vn_cash_payment_threshold"

# Constants: SCREAMING_SNAKE_CASE
VN_CASH_THRESHOLD = 20_000_000
KR_MIN_RECEIPT_AMOUNT = 30_000
```

### 2. Z3 Pattern — luôn dùng 3 bước
```python
def encode(self, solver: Solver, data: dict) -> None:
    # Bước 1: Khai báo biến Z3
    z3_amount = Int("amount")
    z3_is_cash = Bool("is_cash")

    # Bước 2: Thêm quy tắc
    solver.add(Implies(z3_amount >= VN_CASH_THRESHOLD, Not(z3_is_cash)))

    # Bước 3: Bind dữ liệu
    solver.add(z3_amount == data["amount"])
    solver.add(z3_is_cash == BoolVal(data["is_cash_payment"]))
    # ⚠️ QUAN TRỌNG: Bool values phải dùng BoolVal(), không dùng Python True/False trực tiếp
```

### 3. Thêm Business Rule mới
```python
# 1. Tạo file mới trong src/z3_engine/rules/
# 2. Kế thừa BusinessRule
# 3. Implement 4 properties + encode() + get_violation_detail()
# 4. Đăng ký vào solver

from src.z3_engine.rules.base_rule import BusinessRule

class NewCountryRule(BusinessRule):
    @property
    def name(self) -> str: return "new_country_rule"

    @property
    def description(self) -> str: return "Mô tả rule"

    @property
    def legal_reference(self) -> str: return "Số hiệu văn bản pháp luật"

    @property
    def severity(self) -> str: return "critical"  # critical | warning | info

    def encode(self, solver: Solver, data: dict) -> None:
        # Implement Z3 constraints here
        pass

    def get_violation_detail(self, data: dict) -> str:
        return "Mô tả vi phạm cụ thể"
```

### 4. SemanticParser — không có API key → dùng MockParser
```python
# Dev/test không cần API key
parser = SemanticParser(api_key="")  # → MockSemanticParser tự động

# Production — dùng env var
parser = SemanticParser.from_config()  # đọc GEMINI_API_KEY từ .env
```

---

## Data Flow cần nhớ

```
User Input (str)
    ↓ SemanticParser.parse()
ParseResult {
    scenario_type: ScenarioType.VN_PAYMENT | KR_TAX_REFUND | UNKNOWN
    vn_transaction: ParsedVNTransaction | None
    kr_tax_refund: ParsedKRTaxRefund | None
}
    ↓ .to_z3_data()  →  dict (keys phải match với Z3 variable names!)
    ↓ .get_applicable_rules()  →  list[str] (tên rule)
    ↓ TrustAgentSolver.verify(data, rule_names)
VerificationResult {
    status: VerificationStatus.SAT | UNSAT | UNKNOWN
    is_compliant: bool
    violations: list[RuleViolation]
    verification_time_ms: float
    ...
}
```

### ⚠️ Key mismatch là bug thường gặp nhất

```python
# Trong Z3 rule, biến được khai báo:
z3_amount = Int("amount")            # key = "amount"
z3_is_cash = Bool("is_cash")         # key = "is_cash"

# Trong ParsedVNTransaction model, field là:
amount: int                          # ✅ match
is_cash_payment: bool                # ❌ "is_cash_payment" ≠ "is_cash" ← BUG!

# Fix: trong vn_tax_rule.py, bind đúng key:
solver.add(z3_is_cash == BoolVal(data["is_cash_payment"]))  # ✅
```

---

## Testing

```bash
# Chạy toàn bộ tests
pytest tests/ -v

# Chỉ Phase 1
pytest tests/test_z3_engine.py -v

# Chỉ Phase 2
pytest tests/test_semantic_parser.py -v

# Kết quả hiện tại (Phase 1 + 2)
# 50 passed in ~0.40s
```

---

## Lộ trình phát triển

| Phase | Trạng thái | Mô tả |
|-------|-----------|-------|
| 1 | ✅ DONE | Z3 Engine + VN/KR Rules (26 tests) |
| 2 | ✅ DONE | Gemini Semantic Parser + Mock (50 tests) |
| 3 | 🔜 NEXT | LangGraph Multi-Agent Orchestration |
| 4 | 🔜 | FastAPI REST + PostgreSQL |
| 5 | 🔜 | Web Dashboard |
| 6 | 🔜 | Docker + INNOSTAR Demo |

---

## Phong cách code

- **Docstrings**: tiếng Việt cho business logic, tiếng Anh cho technical
- **Comments**: giải thích "WHY" không phải "WHAT"
- **Error handling**: dùng logging, không raise raw exceptions ra ngoài
- **Type hints**: bắt buộc cho mọi function signature
- **Line length**: max 100 ký tự (xem pyproject.toml)
