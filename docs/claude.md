# 🧠 Hướng dẫn cho Claude AI — `claude.md`

> File này được đọc bởi **Claude AI models** (Claude Sonnet, Claude Opus...)
> khi làm việc với dự án TrustAgent.Forensics.
> **LUÔN đọc file này và `docs/NHAT_KY.md` TRƯỚC KHI bắt đầu bất kỳ task nào.**

---

## Dự án là gì?

**TrustAgent.Forensics** — Nền tảng quản trị AI (AI Governance) dùng kiến trúc Neuro-Symbolic:

- **Mục tiêu**: Đảm bảo AI Agents luôn tuân thủ pháp luật khi thực thi tự động
- **Cách làm**: LLM hiểu ngôn ngữ → Z3 kiểm tra luật toán học → Không thể bypass
- **Đối tượng**: Doanh nghiệp VN + KR dùng AI để xử lý tài chính/kế toán
- **Cuộc thi**: INNOSTAR 2026 (khởi nghiệp sinh viên VN-KR)

**Tech stack 2026**: Python 3.12, Z3 4.16, Gemini 2.0 Flash, LangGraph 0.4, FastAPI 0.115, PostgreSQL 17

---

## Trạng thái hiện tại (cập nhật 2026-07-01)

| Phase | Files chính | Trạng thái | Tests |
|-------|------------|------------|-------|
| **Phase 1** — Z3 Engine | `src/z3_engine/` | ✅ Hoàn thành | 26 |
| **Phase 2** — Semantic Parser | `src/semantic/` | ✅ Hoàn thành | 24 |
| **Phase 3** — LangGraph Agents | `src/agents/` | ✅ Hoàn thành | 20 |
| **Phase 4** — FastAPI + DB | `src/api/`, `src/database/` | 🔜 Chưa làm | — |
| **Phase 5** — Dashboard | `src/dashboard/` | 🔜 Chưa làm | — |
| **Phase 6** — Docker/Demo | Root | 🔜 Chưa làm | — |

**Tổng tests hiện tại**: 70 passed, 0 failed

---

## Luồng dữ liệu toàn hệ thống

```
Người dùng nhập câu (tiếng Việt/Anh)
    │
    ▼ TrustAgentWorkflow.run()           [Phase 3 — LangGraph]
    │
    ├─ parse_node()
    │     └─ SemanticParser.parse()      [Phase 2 — Gemini/Mock]
    │           → ParseResult { scenario_type, vn_transaction | kr_tax_refund }
    │
    ├─ verify_node()
    │     └─ TrustAgentSolver.verify()   [Phase 1 — Z3]
    │           → VerificationResult { status: SAT|UNSAT, violations }
    │
    ├─ explain_node()
    │     └─ SemanticParser.explain_result()
    │           → str (giải thích thân thiện)
    │
    └─ WorkflowResult { tất cả thông tin trên + duration_ms }
```

---

## Codebase Map đầy đủ

```
src/
├── config.py                    # Pydantic Settings — đọc .env
├── z3_engine/                   # ✅ Phase 1
│   ├── models.py                # TransactionData, TaxRefundData,
│   │                            # VerificationResult, RuleViolation, VerificationStatus
│   ├── solver.py                # TrustAgentSolver
│   └── rules/
│       ├── base_rule.py         # BusinessRule (abstract)
│       ├── vn_tax_rule.py       # VietnamCashPaymentRule
│       └── kr_refund_rule.py    # KoreaTaxRefundRule
├── semantic/                    # ✅ Phase 2
│   ├── schemas.py               # ParseResult, ParsedVNTransaction, ParsedKRTaxRefund, ScenarioType
│   ├── prompts.py               # Prompt templates
│   └── parser.py                # SemanticParser → Gemini | Mock
├── agents/                      # ✅ Phase 3
│   ├── state.py                 # AgentState (TypedDict)
│   ├── nodes.py                 # parse_node, verify_node, explain_node, route_node
│   ├── graph.py                 # build_graph() → CompiledGraph
│   └── workflow.py              # TrustAgentWorkflow (public API)
├── api/                         # 🔜 Phase 4
└── database/                    # 🔜 Phase 4
```

---

## Quy tắc quan trọng khi code (KHÔNG BAO GIỜ QUÊN)

### ⚠️ Rule 1: BoolVal() với Z3
```python
# ❌ SAI — Python True/False không hoạt động đúng
solver.add(z3_bool_var == data["is_cash"])

# ✅ ĐÚNG
from z3 import BoolVal
solver.add(z3_bool_var == BoolVal(data["is_cash"]))
```

### ⚠️ Rule 2: Z3 variable name phải match với data dict key
```python
z3_amount = Int("amount")
solver.add(z3_amount == data["amount"])  # key phải là "amount"
```

### ⚠️ Rule 3: Tạo Solver() mới mỗi lần verify — không reuse
```python
# TrustAgentSolver tự làm điều này — không cần lo
```

### ⚠️ Rule 4: LangGraph State là immutable — dùng dict merge
```python
# ✅ ĐÚNG — return dict với keys cần update
def parse_node(state: AgentState) -> dict:
    return {"parse_result": result, "error": None}

# ❌ SAI — không mutate state trực tiếp
state["parse_result"] = result  # SAI
```

---

## APIs quan trọng

### TrustAgentWorkflow (Phase 3 — public API chính)
```python
from src.agents.workflow import TrustAgentWorkflow

workflow = TrustAgentWorkflow()
result = workflow.run("Thanh toán tiền mặt 25 triệu cho sự kiện")
# result.user_input      → str
# result.scenario_type   → "VN_PAYMENT" | "KR_TAX_REFUND" | "UNKNOWN"
# result.z3_status       → "SAT" | "UNSAT" | "UNKNOWN"
# result.is_compliant    → bool
# result.explanation     → str (thân thiện cho user)
# result.violations      → list[dict]
# result.duration_ms     → float
```

### TrustAgentSolver (Phase 1)
```python
solver = TrustAgentSolver()
solver.register_rule(VietnamCashPaymentRule())
result = solver.verify({"amount": 25_000_000, "is_cash_payment": True})
# result.status / result.is_compliant / result.violations
```

### SemanticParser (Phase 2)
```python
parser = SemanticParser(api_key="")  # Mock cho dev
result = parser.parse("Thanh toán tiền mặt 25 triệu")
# result.scenario_type / result.to_z3_data() / result.get_applicable_rules()
```

---

## Không làm những điều này

```python
# ❌ Để LLM ra quyết định tuân thủ
if llm.says_compliant(): approve()

# ❌ Mutate AgentState trực tiếp trong node
state["key"] = value

# ❌ Bỏ qua type hints
def run(input): ...

# ❌ Reuse Solver() giữa các lần verify

# ❌ Raise Exception trực tiếp — dùng logging + UNKNOWN status
```

---

## Phong cách code

```python
# Docstrings: tiếng Việt cho business, tiếng Anh cho technical
# Constants: SCREAMING_SNAKE_CASE + comment pháp lý
VN_CASH_THRESHOLD = 20_000_000  # Thông tư 96/2015/TT-BTC, Điều 4, Khoản 1, Điểm c
# Logging thay vì print
# Type hints bắt buộc cho mọi function
# Line length: max 100 ký tự
```
