# 🏗️ Kiến trúc hệ thống TrustAgent.Forensics

> *Hiểu cách 3 tầng hoạt động cùng nhau — có ví dụ minh họa từng bước*

---

## Toàn cảnh 3 tầng

```
┌──────────────────────────────────────────────────────────────┐
│                    👤 Người dùng / AI Agent                   │
│          "Thanh toán tiền mặt 25 triệu cho sự kiện"          │
└─────────────────────────┬────────────────────────────────────┘
                          │ Ngôn ngữ tự nhiên
                          ▼
┌──────────────────────────────────────────────────────────────┐
│              🧠 TẦNG 1 — NEURAL LAYER                         │
│                  Gemini 2.0 Flash                             │
│                                                              │
│  Nhiệm vụ: "HIỂU" ngôn ngữ → tạo ra JSON có cấu trúc        │
│                                                              │
│  Input:  "Thanh toán tiền mặt 25 triệu cho sự kiện"          │
│  Output: {"amount": 25000000, "is_cash_payment": true, ...}  │
└─────────────────────────┬────────────────────────────────────┘
                          │ Structured JSON (không còn ngôn ngữ)
                          ▼
┌──────────────────────────────────────────────────────────────┐
│              ⚖️  TẦNG 2 — SYMBOLIC LAYER                      │
│                  Z3 Theorem Prover                            │
│                                                              │
│  Nhiệm vụ: "KIỂM TRA" dữ liệu theo quy tắc toán học         │
│                                                              │
│  Rule: Implies(amount >= 20M, Not(is_cash))                  │
│  Data: amount=25M, is_cash=True                              │
│  → UNSAT ❌ (Vi phạm toán học — không thể bỏ qua)            │
└─────────────────────────┬────────────────────────────────────┘
                          │ SAT ✅ hoặc UNSAT ❌
                          ▼
┌──────────────────────────────────────────────────────────────┐
│              📋 TẦNG 3 — FORENSICS LAYER                      │
│                  PostgreSQL (JSONB)                           │
│                                                              │
│  Nhiệm vụ: "GHI LẠI" mọi quyết định — không thể sửa/xóa    │
│                                                              │
│  Lưu: {input, parsed_json, z3_result, timestamp, ...}        │
│  Phục vụ: kiểm toán, báo cáo pháp lý, truy vết sự cố        │
└──────────────────────────────────────────────────────────────┘
```

---

## Luồng dữ liệu chi tiết (Happy Path & Blocked Path)

### ✅ Giao dịch hợp lệ — "Chuyển khoản 30M mua thiết bị"

```
Bước 1: User input
  "Chuyển khoản 30 triệu mua thiết bị văn phòng"

Bước 2: Gemini parse
  → {"amount": 30000000, "is_cash_payment": false, "purpose": "equipment"}

Bước 3: Z3 verify
  Rule: Implies(30M >= 20M, Not(false)) = Implies(True, True) = True
  → SAT ✅

Bước 4: Execute
  → Giao dịch được thực hiện

Bước 5: Ghi audit trail
  → {status: "SAT", compliant: true, ...} → PostgreSQL
```

### ❌ Giao dịch bị chặn — "Tiền mặt 25M sự kiện"

```
Bước 1: User input
  "Thanh toán tiền mặt 25 triệu cho sự kiện"

Bước 2: Gemini parse
  → {"amount": 25000000, "is_cash_payment": true, "purpose": "event"}

Bước 3: Z3 verify
  Rule: Implies(25M >= 20M, Not(true)) = Implies(True, False) = False
  → UNSAT ❌

Bước 4: BLOCK — không thực thi
  → Trả về: "Vi phạm Thông tư 96/2015: cần chuyển khoản"

Bước 5: Ghi audit trail
  → {status: "UNSAT", violation: "vn_cash_payment_threshold", ...} → PostgreSQL
```

---

## Tại sao tách Neural và Symbolic?

### Điểm yếu nếu dùng LLM thuần túy

```python
# ❌ Cách sai — LLM ra quyết định
prompt = """
Người dùng muốn thanh toán 25M tiền mặt.
Quy định: Đừng dùng tiền mặt > 20M.
Hãy quyết định xem có nên thực hiện không?
"""
# LLM có thể bị thuyết phục, bị tiêm lệnh, hallucinate...
```

### Thiết kế đúng — LLM chỉ "dịch", Z3 mới "phán xử"

```python
# ✅ Cách đúng — tách biệt trách nhiệm
# LLM chỉ trích xuất dữ liệu
parsed = gemini.parse("Thanh toán tiền mặt 25 triệu")
# → {"amount": 25000000, "is_cash_payment": true}

# Z3 độc lập kiểm tra luật — không thể bị ảnh hưởng bởi ngôn ngữ
result = z3_solver.verify(parsed)
# → UNSAT (toán học không biết nịnh)
```

---

## Cấu trúc module

```
src/
├── z3_engine/          # Tầng 2: Symbolic
│   ├── solver.py       # TrustAgentSolver — wrapper chính
│   ├── models.py       # Pydantic models (TransactionData, VerificationResult...)
│   └── rules/          # Các bộ luật
│       ├── base_rule.py      # Abstract class — blueprint cho mọi rule
│       ├── vn_tax_rule.py    # 🇻🇳 Luật thuế VN (Thông tư 96/2015)
│       └── kr_refund_rule.py # 🇰🇷 Luật hoàn thuế Hàn Quốc
│
├── semantic/           # Tầng 1: Neural
│   ├── parser.py       # SemanticParser — điều phối Gemini/Mock
│   ├── prompts.py      # Prompt templates cho Gemini
│   └── schemas.py      # Pydantic schemas cho JSON output của Gemini
│
├── agents/             # LangGraph orchestration (Phase 3)
├── api/                # FastAPI REST endpoints (Phase 4)
├── database/           # PostgreSQL audit trail (Phase 4)
└── dashboard/          # Web UI (Phase 5)
```

---

## Thêm bộ luật mới như thế nào?

Rất đơn giản — chỉ cần tạo 1 class kế thừa `BusinessRule`:

```python
# src/z3_engine/rules/my_new_rule.py
from z3 import Solver, Int
from .base_rule import BusinessRule

class MyNewRule(BusinessRule):
    @property
    def name(self): return "my_new_rule"

    @property
    def description(self): return "Mô tả rule của tôi"

    @property
    def legal_reference(self): return "Điều XX, Khoản YY"

    def encode(self, solver: Solver, data: dict) -> None:
        # Viết ràng buộc Z3 ở đây
        z3_amount = Int("amount")
        solver.add(z3_amount <= 100_000_000)  # Không quá 100M
        solver.add(z3_amount == data["amount"])

    def get_violation_detail(self, data: dict) -> str:
        return f"Số tiền {data['amount']:,} vượt quá giới hạn 100M"

# Đăng ký vào solver
solver.register_rule(MyNewRule())
```

---

*Tiếp theo: [Z3_EXPLAINED.md](Z3_EXPLAINED.md) — Z3 Theorem Prover là gì và hoạt động thế nào?*
