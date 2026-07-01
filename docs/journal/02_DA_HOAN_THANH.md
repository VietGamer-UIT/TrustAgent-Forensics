# 📓 NHẬT KÝ #2 — ĐÃ HOÀN THÀNH
# Ghi lại những gì ĐÃ làm xong, lỗi đã gặp, cách fix, và kết quả thực tế
# Quy tắc: Chuyển entry từ `01_TRUOC_KHI_LAM.md` vào đây sau khi hoàn thành

> **Mục đích**: AI model đọc file này để biết hệ thống đang ở đâu,
> không bao giờ làm lại thứ đã xong, và kế thừa đúng pattern đã dùng.
> **LUÔN đọc file này trước khi bắt đầu code.**

---

## Tổng quan tiến độ

| Phase | Tên | Ngày xong | Tests | Git Tag |
|-------|-----|-----------|-------|---------|
| **1** | Z3 Verification Engine | 2026-06-30 | 26/26 | `v0.1.0-z3-engine` |
| **2** | Gemini Semantic Parser | 2026-07-01 | +24 (50) | `v0.2.0-semantic-parser` |
| **3** | LangGraph Multi-Agent | 2026-07-01 | +33 (83) | `v0.3.0-langgraph-agents` |
| **3.5** | Legal RAG Module | 2026-07-01 | +28 (111) | `v0.3.5-legal-rag` *(pending)* |

**Tổng tests hiện tại: 111 passed, 0 failed**

---

## ✅ PHASE 1 — Z3 Verification Engine
**Ngày**: 2026-06-30 | **Tag**: `v0.1.0-z3-engine`

### Đã làm
- `src/z3_engine/models.py` — Pydantic models cho toàn hệ thống
- `src/z3_engine/rules/base_rule.py` — Abstract `BusinessRule`
- `src/z3_engine/rules/vn_tax_rule.py` — `VietnamCashPaymentRule`
- `src/z3_engine/rules/kr_refund_rule.py` — `KoreaTaxRefundRule`
- `src/z3_engine/solver.py` — `TrustAgentSolver`
- `tests/test_z3_engine.py` — 26 unit tests

### Lỗi đã gặp & cách fix
| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| Z3 Bool silent wrong result | Dùng `True/False` trực tiếp | Dùng `BoolVal(data["is_eligible"])` |
| KeyError `is_eligible` | Thiếu field trong model | Thêm `is_eligible: bool` vào `TaxRefundData` |

### Input/Output mẫu
```
INPUT:  {"amount": 25_000_000, "is_cash_payment": True}
RULE:   VietnamCashPaymentRule (Thông tư 96/2015)
OUTPUT: VerificationResult(status="unsat", is_compliant=False)

INPUT:  {"receipt_amount": 50_000, "refund_amount": 5_000, ...}
RULE:   KoreaTaxRefundRule
OUTPUT: VerificationResult(status="sat", is_compliant=True)
```

---

## ✅ PHASE 2 — Gemini Semantic Parser
**Ngày**: 2026-07-01 | **Tag**: `v0.2.0-semantic-parser`

### Đã làm
- `src/semantic/schemas.py` — `ParseResult`, `ParsedVNTransaction`, `ParsedKRTaxRefund`, `ScenarioType`
- `src/semantic/prompts.py` — Prompt templates (detect, VN extract, KR extract, explain)
- `src/semantic/parser.py` — `SemanticParser` (auto-switch Gemini/Mock), `MockSemanticParser`
- `tests/test_semantic_parser.py` — 24 tests

### Lỗi đã gặp & cách fix
| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| `int('')` crash khi parse KRW | Regex `[\d,]+(?=won)` match chuỗi rỗng | Đổi sang `\b[\d]+(?:,\d{3})*\b` |
| ScenarioType uppercase mismatch | Enum value là lowercase `"vn_payment"` | Cập nhật tất cả comparisons |

### Quyết định thiết kế quan trọng
- `MockSemanticParser`: Dùng regex thuần, không cần API key → dev/test offline
- `GeminiSemanticParser`: Production mode, cần `GEMINI_API_KEY` trong `.env`
- `SemanticParser.from_config()`: Auto-detect env → chọn đúng implementation

---

## ✅ PHASE 3 — LangGraph Multi-Agent Orchestration
**Ngày**: 2026-07-01 | **Tag**: `v0.3.0-langgraph-agents`

### Đã làm
- `src/agents/state.py` — `AgentState` (TypedDict), field `legal_thresholds` (Phase 3.5)
- `src/agents/nodes.py` — `parse_node`, `legal_rag_node`, `verify_node`, `explain_node`, `route_after_parse`
- `src/agents/graph.py` — `build_graph()` + `_MockGraph` (fallback khi langgraph chưa cài)
- `src/agents/workflow.py` — `TrustAgentWorkflow` + `WorkflowResult` dataclass
- `tests/test_agents.py` — 33 tests

### Kiến trúc graph (Phase 3.5)
```
START → parse_node → [route_after_parse]
                           │
              ┌────────────┤
              │ (known)    │ (UNKNOWN)
              ▼            ▼
        legal_rag_node  explain_node → END
              │
              ▼
         verify_node
              │
              ▼
         explain_node → END
```

### Lỗi đã gặp & cách fix
| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| Routing mismatch | `route_after_parse` trả `"verify"` → cần `"rag"` | Đổi return value sau Phase 3.5 |
| `LangGraph` không cài | Không có `langgraph` trong venv | `_MockGraph` chạy tuần tự thay thế |

---

## ✅ PHASE 3.5 — Legal RAG Module
**Ngày**: 2026-07-01 | **Tag**: `v0.3.5-legal-rag` *(pending commit)*

### Đã làm
- `src/rag/legal_data/VN_tax_law.md` — Văn bản luật VN (Thông tư 96/2015 + JSON metadata)
- `src/rag/legal_data/KR_refund_law.md` — Văn bản luật KR (30K/75K KRW + JSON metadata)
- `src/rag/retriever.py` — `LegalRetriever`: ChromaDB (optional) + keyword fallback
- `src/rag/extractor.py` — `ThresholdExtractor`: JSON block → regex → hardcoded defaults
- `src/rag/__init__.py`
- `tests/test_rag.py` — 28 tests

### Quyết định kiến trúc quan trọng
**ChromaDB vs pgvector?**
- **ChromaDB** → dùng cho RAG (legal docs nhỏ, embedded, zero config, dev-friendly)
- **pgvector** → dùng cho Phase 4 (audit trail, cần ACID, JOIN với dữ liệu quan hệ)
- Hai concerns khác nhau → dùng cả hai, không conflict

### Luồng RAG hoàn chỉnh
```
parse_node → legal_rag_node → verify_node → explain_node

legal_rag_node:
  1. LegalRetriever.get_legal_text("vn_payment") → văn bản luật
  2. ThresholdExtractor.extract("vn_payment", text):
       - Tầng 1: JSON block {"VN_CASH_THRESHOLD": 20000000}
       - Tầng 2: Regex từ text thường
       - Tầng 3: Hardcoded fallback
  3. → state["legal_thresholds"] = {"VN_CASH_THRESHOLD": 20000000}

verify_node:
  solver.verify(data, rules, dynamic_thresholds=state["legal_thresholds"])
  → Z3 dùng ngưỡng từ RAG thay vì hardcode
```

### Cập nhật các file cũ (backward compatible)
| File | Thay đổi |
|------|----------|
| `base_rule.py` | `encode(solver, data, dynamic_thresholds=None)` — optional param |
| `vn_tax_rule.py` | Dùng `dynamic_thresholds.get("VN_CASH_THRESHOLD", default)` |
| `kr_refund_rule.py` | Dùng `dynamic_thresholds.get("KR_MIN_RECEIPT_AMOUNT", default)` |
| `solver.py` | `verify(data, rules, dynamic_thresholds=None)` → truyền vào rule |

### Input/Output mẫu Phase 3.5
```
INPUT:   TrustAgentWorkflow.run("Thanh toán tiền mặt 25 triệu cho sự kiện")

INTERNAL:
  1. parse_node:     ScenarioType.VN_PAYMENT, amount=25M, is_cash=True
  2. legal_rag_node: {"VN_CASH_THRESHOLD": 20000000}  ← từ VN_tax_law.md
  3. verify_node:    Z3 UNSAT (25M >= 20M và is_cash=True → vi phạm)
  4. explain_node:   "❌ Giao dịch bị từ chối..."

OUTPUT:  WorkflowResult(
    scenario_type   = "vn_payment",
    z3_status       = "UNSAT",
    is_compliant    = False,
    violations      = [{"rule_name": "vn_cash_payment_threshold", ...}],
    explanation     = "❌ Giao dịch bị từ chối...",
    total_duration_ms = ~5ms
)
```

---

## 📌 Lỗi hay gặp — ĐỌC TRƯỚC KHI CODE

```
⚠️ 1. Z3 Bool phải dùng BoolVal():
       SALDONG:  solver.add(z3_bool == data["flag"])       ← Silent wrong result
       ĐÚNG:     solver.add(z3_bool == BoolVal(data["flag"]))

⚠️ 2. Z3 variable name phải match key trong data dict:
       z3_amount = Int("amount") → data["amount"]  ← phải là "amount"

⚠️ 3. ScenarioType enum value là lowercase:
       ScenarioType.VN_PAYMENT.value = "vn_payment"  ← không phải "VN_PAYMENT"

⚠️ 4. route_after_parse trả về "rag" (không phải "verify") cho Phase 3.5+

⚠️ 5. Không reuse Solver() — TrustAgentSolver tạo fresh solver mỗi lần verify

⚠️ 6. Không mutate AgentState trực tiếp — trả về dict để LangGraph merge
```
