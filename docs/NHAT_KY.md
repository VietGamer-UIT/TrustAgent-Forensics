# 📓 NHẬT KÝ PHÁT TRIỂN — TrustAgent.Forensics
# Dev Journal — ghi lại toàn bộ tiến trình, quyết định kỹ thuật, input/output

> **Nguyên tắc**: File này PHẢI được đọc và cập nhật mỗi khi bắt đầu/kết thúc làm việc.
> Không bao giờ bắt đầu code mà không đọc file này và `docs/claude.md` trước.

---

## 📊 BẢNG TIẾN ĐỘ TỔNG THỂ

| Phase | Tên | Trạng thái | Tests | Tag Git |
|-------|-----|-----------|-------|---------|
| **1** | Z3 Verification Engine | ✅ XONG | 26/26 | `v0.1.0-z3-engine` |
| **2** | Gemini Semantic Parser | ✅ XONG | 24/24 (50 tổng) | `v0.2.0-semantic-parser` |
| **3** | LangGraph Multi-Agent | ✅ XONG | +20 (70 tổng) | `v0.3.0-langgraph-agents` |
| **4** | FastAPI + PostgreSQL | 🔜 CHƯA | — | — |
| **5** | Web Dashboard | 🔜 CHƯA | — | — |
| **6** | Docker + Demo Pack | 🔜 CHƯA | — | — |

---

## ✅ PHASE 1 — Z3 Verification Engine
**Ngày**: 2026-06-30  
**Tag**: `v0.1.0-z3-engine`  
**Tests**: 26 passed

### Đã làm
- `src/z3_engine/models.py` — Pydantic models: `TransactionData`, `TaxRefundData`, `VerificationResult`, `RuleViolation`, `VerificationStatus`
- `src/z3_engine/rules/base_rule.py` — Abstract `BusinessRule` (Strategy pattern)
- `src/z3_engine/rules/vn_tax_rule.py` — `VietnamCashPaymentRule`: Thông tư 96/2015 (20M VNĐ)
- `src/z3_engine/rules/kr_refund_rule.py` — `KoreaTaxRefundRule`: Incheon Airport (30K/75K KRW)
- `src/z3_engine/solver.py` — `TrustAgentSolver`: registry + verify pipeline
- `tests/test_z3_engine.py` — 26 unit tests

### Bug đã fix trong Phase 1
- **Bug**: `KoreaTaxRefundRule` thiếu field `is_eligible` trong `TaxRefundData` → KeyError
- **Fix**: Thêm field `is_eligible: bool` vào `TaxRefundData` model
- **Bug**: Z3 Bool binding dùng Python `True/False` trực tiếp → silent wrong result
- **Fix**: Dùng `BoolVal(data["is_eligible"])` thay vì `data["is_eligible"]`

### Input/Output mẫu Phase 1
```
INPUT:  {"amount": 25_000_000, "is_cash_payment": True}
RULE:   VietnamCashPaymentRule (Implies amount>=20M → Not cash)
OUTPUT: VerificationResult(status=UNSAT, is_compliant=False, violations=[...])

INPUT:  {"amount": 30_000_000, "is_cash_payment": False}
RULE:   VietnamCashPaymentRule
OUTPUT: VerificationResult(status=SAT, is_compliant=True, violations=[])
```

---

## ✅ PHASE 2 — Gemini Semantic Parser
**Ngày**: 2026-06-30 → 2026-07-01  
**Tag**: `v0.2.0-semantic-parser`  
**Tests**: 24 new (50 tổng)

### Đã làm
- `src/semantic/schemas.py` — `ParseResult`, `ParsedVNTransaction`, `ParsedKRTaxRefund`, `ScenarioType`
- `src/semantic/prompts.py` — Prompt templates: detect scenario, VN extract, KR extract, explain result
- `src/semantic/parser.py` — `SemanticParser` (auto-switch), `GeminiSemanticParser` (real API), `MockSemanticParser` (dev/test)
- `tests/test_semantic_parser.py` — 24 tests: detect, VN parse, KR parse, end-to-end pipeline

### Bug đã fix trong Phase 2
- **Bug**: Regex `[\d,]+(?=\s*(?:krw|won|원))` match chuỗi rỗng cho pattern `1,000,000 won` → `int('')` crash
- **Fix**: Đổi sang `\b([\d]+(?:,\d{3})*)\s*(?:krw|won|원)\b` — yêu cầu ít nhất 1 chữ số

### Input/Output mẫu Phase 2
```
INPUT (NL):  "Thanh toán tiền mặt 25 triệu cho sự kiện"
DETECT:      ScenarioType.VN_PAYMENT
PARSE:       ParsedVNTransaction(amount=25_000_000, is_cash_payment=True, purpose="event")
Z3_DATA:     {"amount": 25000000, "is_cash_payment": True, ...}
RULES:       ["vn_cash_payment_threshold"]
Z3 RESULT:   UNSAT ❌ — Vi phạm Thông tư 96/2015
EXPLAIN:     "❌ Giao dịch bị từ chối. Số tiền 25,000,000 VNĐ ≥ ngưỡng..."

INPUT (NL):  "Mua hàng 1,000,000 won, hoàn 80,000 won"
DETECT:      ScenarioType.KR_TAX_REFUND
PARSE:       ParsedKRTaxRefund(receipt=1_000_000, refund=80_000, needs_customs=True)
Z3 RESULT:   SAT ✅ — Hợp lệ, cần kiểm tra hải quan
```

---

## ✅ PHASE 3 — LangGraph Multi-Agent Orchestration
**Ngày**: 2026-07-01  
**Tag**: `v0.3.0-langgraph-agents`  
**Tests**: 20 new (70 tổng)

### Đã làm
- `src/agents/state.py` — `AgentState` (TypedDict): trạng thái chia sẻ giữa các node
- `src/agents/nodes.py` — 4 node functions: `parse_node`, `verify_node`, `explain_node`, `route_node`
- `src/agents/graph.py` — `build_graph()`: compile LangGraph `StateGraph`
- `src/agents/workflow.py` — `TrustAgentWorkflow`: public API + `run()` method
- `tests/test_agents.py` — 20 tests: state transitions, node logic, end-to-end workflow

### Kiến trúc graph
```
START → parse_node → verify_node → explain_node → END
                          ↑
                    (conditional: unknown → explain_node)
```

### Input/Output mẫu Phase 3
```
INPUT:   TrustAgentWorkflow.run("Thanh toán tiền mặt 25 triệu cho sự kiện")
OUTPUT:  WorkflowResult {
    user_input:    "Thanh toán tiền mặt 25 triệu cho sự kiện"
    parsed:        ScenarioType.VN_PAYMENT, amount=25M, is_cash=True
    z3_status:     UNSAT
    is_compliant:  False
    explanation:   "❌ Giao dịch bị từ chối..."
    violations:    [RuleViolation(rule="vn_cash_payment_threshold", ...)]
    duration_ms:   ~5ms
}
```

---

## 🔜 PHASE 4 — FastAPI Backend + PostgreSQL
**Trạng thái**: Chưa làm  
**Kế hoạch**:
- `src/api/main.py` — FastAPI app
- `src/api/routes/verify.py` — `POST /api/v1/verify`
- `src/api/routes/audit.py` — `GET /api/v1/audit/{id}`
- `src/database/models.py` — SQLAlchemy ORM + JSONB
- `src/database/session.py` — Async session
- `docker-compose.yml` — App + PostgreSQL

### Input/Output Phase 4 (dự kiến)
```
HTTP POST /api/v1/verify
Body: {"user_input": "Thanh toán tiền mặt 25 triệu"}
Response 200: {
    "status": "UNSAT",
    "is_compliant": false,
    "violations": [...],
    "audit_id": "uuid-...",
    "duration_ms": 5.2
}
```

---

## 🔜 PHASE 5 — Web Dashboard
**Trạng thái**: Chưa làm

---

## 🔜 PHASE 6 — Docker + Demo Package
**Trạng thái**: Chưa làm

---

## ⚠️ NHỮNG LỖI HAY GẶP — ĐỌC TRƯỚC KHI CODE

1. **BoolVal bug**: Z3 Bool variable dùng `== True` thay vì `== BoolVal(True)` → silent wrong result
2. **Key mismatch**: Tên biến Z3 phải khớp chính xác với key trong dict data
3. **Regex KRW**: Pattern `[\d,]+(?=won)` match chuỗi rỗng → dùng `\b[\d]+(?:,\d{3})*\b`
4. **Solver reuse**: Không bao giờ reuse `Solver()` instance — tạo mới mỗi lần verify
5. **Missing model field**: Luôn check `TaxRefundData.model_dump()` có đủ key mà rule cần không

---

## 📁 CẤU TRÚC THƯ MỤC HIỆN TẠI

```
TrustAgent-Forensics/
├── 📓 docs/                         ← Tài liệu
│   ├── claude.md                    ← 🤖 ĐỌC TRƯỚC KHI LÀM (Claude AI)
│   ├── gemini.md                    ← 🤖 ĐỌC TRƯỚC KHI LÀM (Gemini AI)
│   ├── NHAT_KY.md                   ← 📓 File này — nhật ký phát triển
│   ├── KIEN_TRUC.md                 ← Kiến trúc hệ thống
│   ├── TAI_SAO.md                   ← Lý do tồn tại của dự án
│   ├── Z3_GIAI_THICH.md             ← Z3 giải thích dễ hiểu
│   ├── QUY_TAC_KINH_DOANH.md        ← Business rules tham chiếu
│   ├── LO_TRINH.md                  ← Roadmap các giai đoạn
│   └── DONG_GOP.md                  ← Hướng dẫn đóng góp
│
├── 🔬 src/                          ← Source code chính
│   ├── config.py                    ← Cấu hình app (env vars)
│   ├── z3_engine/                   ← ✅ Phase 1: Z3 Engine
│   │   ├── models.py
│   │   ├── solver.py
│   │   └── rules/
│   │       ├── base_rule.py
│   │       ├── vn_tax_rule.py
│   │       └── kr_refund_rule.py
│   ├── semantic/                    ← ✅ Phase 2: Semantic Parser
│   │   ├── schemas.py
│   │   ├── prompts.py
│   │   └── parser.py
│   ├── agents/                      ← ✅ Phase 3: LangGraph
│   │   ├── state.py
│   │   ├── nodes.py
│   │   ├── graph.py
│   │   └── workflow.py
│   ├── api/                         ← 🔜 Phase 4: FastAPI
│   └── database/                    ← 🔜 Phase 4: PostgreSQL
│
├── 🧪 tests/                        ← Unit tests
│   ├── test_z3_engine.py            ← Phase 1: 26 tests
│   ├── test_semantic_parser.py      ← Phase 2: 24 tests
│   └── test_agents.py               ← Phase 3: 20 tests
│
├── .env.example                     ← Template env vars
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── pyproject.toml
```
