<p align="center">
  <h1 align="center">🛡️ TrustAgent.Forensics</h1>
  <p align="center">
    <strong>Nền tảng Quản trị AI — Neuro-Symbolic AI Governance</strong><br/>
    <em>Kiểm chứng hành động AI bằng Z3 Theorem Prover trước khi thực thi</em>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"/>
    <img src="https://img.shields.io/badge/Z3-4.16.0-orange.svg" alt="Z3 4.16"/>
    <img src="https://img.shields.io/badge/Gemini-2.0_Flash-4285F4.svg" alt="Gemini 2.0"/>
    <img src="https://img.shields.io/badge/LangGraph-0.4+-purple.svg" alt="LangGraph 0.4+"/>
    <img src="https://img.shields.io/badge/tests-111%20passed-brightgreen.svg" alt="111 tests"/>
    <img src="https://img.shields.io/badge/INNOSTAR-2026-red.svg" alt="INNOSTAR 2026"/>
  </p>
</p>

---

## 🎯 TrustAgent.Forensics là gì?

**TrustAgent.Forensics** là nền tảng quản trị AI (AI Governance) kết hợp hai thế giới:
- **Neural** (Gemini LLM): Hiểu ngôn ngữ tự nhiên, không thể bị bẻ qua prompt injection
- **Symbolic** (Z3 Theorem Prover): Kiểm tra toán học xác định (deterministic) — không thể sai

Khi AI Agent định thực hiện một giao dịch tài chính tự động, hệ thống sẽ **chặn và kiểm tra** trước — đảm bảo mọi hành động đều tuân thủ pháp luật VN + KR.

### ⚡ Vấn đề đang giải quyết

AI Agents ngày nay đang chuyển từ *Copilot* (hỗ trợ) sang *Autopilot* (tự động hành động). Khi AI tự động thực hiện giao dịch tài chính, một lỗi hallucination có thể gây ra hậu quả pháp lý nghiêm trọng.

**Giải pháp:** Thay vì hỏi LLM "Giao dịch này có hợp lệ không?" (dễ bị lừa), chúng ta dùng **Z3 Theorem Prover** để **chứng minh toán học** rằng giao dịch SAT hoặc UNSAT với luật hiện hành.

```
Người dùng nhập (tiếng Việt / tiếng Anh)
         │
    ┌────▼──────────────────────────┐
    │  🧠 NEURAL LAYER              │  ← Gemini 2.0 Flash
    │   Semantic Parser             │     Hiểu ngôn ngữ → JSON chuẩn hóa
    └────┬──────────────────────────┘
         │ {"amount": 25M, "is_cash": true}
    ┌────▼──────────────────────────┐
    │  📖 LEGAL RAG LAYER           │  ← ChromaDB + Văn bản luật
    │   Threshold Extractor         │     Tra cứu ngưỡng pháp lý động
    └────┬──────────────────────────┘
         │ {"VN_CASH_THRESHOLD": 20_000_000}
    ┌────▼──────────────────────────┐
    │  ⚖️  SYMBOLIC LAYER           │  ← Z3 Theorem Prover (Microsoft)
    │   Formal Verifier             │     Chứng minh toán học, không thể sai
    │   SAT ✅ / UNSAT ❌           │
    └────┬──────────────────────────┘
         │
    ┌────▼──────────────────────────┐
    │  📋 FORENSICS LAYER           │  ← PostgreSQL 17 (Phase 4)
    │   Immutable Audit Trail       │     Mọi quyết định đều có bằng chứng
    └───────────────────────────────┘
```

---

## 🚀 Bắt đầu nhanh

### Yêu cầu
- Python 3.12+

### Cài đặt

```bash
git clone https://github.com/VietGamer-UIT/TrustAgent-Forensics.git
cd TrustAgent-Forensics

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt

cp .env.example .env
# (Tùy chọn) Thêm GEMINI_API_KEY để dùng Gemini thật
```

### Chạy thử ngay

```python
from src.agents.workflow import TrustAgentWorkflow

workflow = TrustAgentWorkflow()

# Ví dụ 1: Giao dịch bị chặn
r = workflow.run("Thanh toán tiền mặt 25 triệu cho sự kiện")
print(r.summary())
# ❌ [UNSAT] Scenario: vn_payment | Tuân thủ: Không | ~5ms

# Ví dụ 2: Giao dịch hợp lệ
r = workflow.run("Chuyển khoản 30 triệu mua thiết bị")
print(r.summary())
# ✅ [SAT] Scenario: vn_payment | Tuân thủ: Có | ~3ms

# Ví dụ 3: Hoàn thuế Hàn Quốc
r = workflow.run("Mua hàng 50,000 KRW tại Incheon, hoàn 5,000 won")
print(r.summary())
# ✅ [SAT] Scenario: kr_tax_refund | Tuân thủ: Có | ~4ms
```

### Chạy Tests

```bash
pytest tests/ -v
# 111 passed in ~0.6s ✅
```

---

## 📁 Cấu trúc dự án

```
TrustAgent-Forensics/
│
├── 📖 docs/                          ← Tài liệu
│   ├── journal/                      ← Nhật ký phát triển (3 files)
│   │   ├── 01_TRUOC_KHI_LAM.md       ← Kế hoạch trước khi bắt đầu task
│   │   ├── 02_DA_HOAN_THANH.md       ← Ghi lại những gì đã làm xong
│   │   └── 03_TUONG_LAI.md           ← Roadmap chi tiết các phase tới
│   ├── claude.md                     ← Hướng dẫn cho Claude AI models
│   ├── gemini.md                     ← Hướng dẫn cho Gemini AI models
│   ├── ARCHITECTURE.md               ← Kiến trúc tổng thể
│   ├── BUSINESS_RULES.md             ← Các quy tắc kinh doanh
│   ├── WHY.md                        ← Lý do tồn tại của dự án
│   └── Z3_EXPLAINED.md               ← Z3 giải thích dễ hiểu
│
├── 🔬 src/                           ← Source code
│   ├── config.py
│   ├── z3_engine/                    ← ✅ Phase 1: Z3 Engine
│   │   ├── solver.py
│   │   ├── models.py
│   │   └── rules/
│   │       ├── vn_tax_rule.py        ← 🇻🇳 Thông tư 96/2015 (20M VNĐ)
│   │       └── kr_refund_rule.py     ← 🇰🇷 30K/75K KRW
│   ├── semantic/                     ← ✅ Phase 2: Gemini Parser
│   │   ├── parser.py
│   │   ├── schemas.py
│   │   └── prompts.py
│   ├── agents/                       ← ✅ Phase 3: LangGraph
│   │   ├── workflow.py               ← Public API
│   │   ├── nodes.py                  ← 4 node functions
│   │   ├── graph.py                  ← Graph builder
│   │   └── state.py                  ← AgentState TypedDict
│   ├── rag/                          ← ✅ Phase 3.5: Legal RAG
│   │   ├── retriever.py              ← LegalRetriever (ChromaDB/keyword)
│   │   ├── extractor.py              ← ThresholdExtractor (JSON/regex/fallback)
│   │   └── legal_data/
│   │       ├── VN_tax_law.md         ← Thông tư 96/2015
│   │       └── KR_refund_law.md      ← Korea Tax Refund Regulations
│   ├── api/                          ← 🔜 Phase 4: FastAPI
│   └── database/                     ← 🔜 Phase 4: PostgreSQL
│
└── 🧪 tests/                         ← 111 tests, 0 failed
    ├── test_z3_engine.py             ← Phase 1: 26 tests
    ├── test_semantic_parser.py       ← Phase 2: 24 tests
    ├── test_agents.py                ← Phase 3: 33 tests
    └── test_rag.py                   ← Phase 3.5: 28 tests
```

---

## ⚖️ Các quy tắc kinh doanh đã implement

### 🇻🇳 Luật thuế Việt Nam — Thông tư 96/2015/TT-BTC

> *"Chi phí mua hàng hóa từ 20 triệu VNĐ trở lên phải thanh toán không dùng tiền mặt"*

```python
# Z3 encoding — toán học thuần túy, không thể bị lừa
Implies(amount >= VN_CASH_THRESHOLD, Not(is_cash_payment))
# VN_CASH_THRESHOLD được lấy động từ Legal RAG Module
```

| Kịch bản | Số tiền | Phương thức | Kết quả |
|----------|---------|-------------|---------|
| Tiền mặt sự kiện | 25,000,000 VNĐ | Tiền mặt | ❌ UNSAT — BỊ CHẶN |
| Chuyển khoản thiết bị | 30,000,000 VNĐ | Ngân hàng | ✅ SAT — CHO PHÉP |
| Tiền mặt văn phòng phẩm | 15,000,000 VNĐ | Tiền mặt | ✅ SAT — CHO PHÉP |

### 🇰🇷 Hoàn thuế Hàn Quốc — Incheon International Airport

> *"Hóa đơn ≥ 30K KRW. Hoàn ≥ 75K KRW → bắt buộc hải quan."*

```python
solver.add(is_eligible == (receipt_amount >= 30_000))
solver.add(Implies(refund_amount < 75_000,  Not(needs_customs_check)))
solver.add(Implies(refund_amount >= 75_000, needs_customs_check))
```

---

## 🔧 Tech Stack 2026

| Layer | Technology | Version | Mục đích |
|-------|-----------|---------|---------|
| **Neural** | Google Gemini | 2.0 Flash | NL → JSON |
| **Symbolic** | Z3 Theorem Prover | 4.16.0 | Chứng minh toán học |
| **RAG** | ChromaDB | Embedded | Tra cứu văn bản luật |
| **Orchestration** | LangGraph | 0.4+ | Multi-agent workflow |
| **Backend** | FastAPI | 0.115+ | REST API *(Phase 4)* |
| **Database** | PostgreSQL + pgvector | 17 | Audit trail *(Phase 4)* |
| **Validation** | Pydantic | v2 | Type safety |
| **Testing** | pytest | 9.x | 111 tests |

---

## 🗺️ Trạng thái phát triển

| Version | Phase | Trạng thái | Tests |
|---------|-------|-----------|-------|
| `v0.1.0` | Z3 Verification Engine | ✅ Hoàn thành | 26 |
| `v0.2.0` | Gemini Semantic Parser | ✅ Hoàn thành | +24 |
| `v0.3.0` | LangGraph Multi-Agent | ✅ Hoàn thành | +33 |
| `v0.3.5` | Legal RAG Module | ✅ Hoàn thành | +28 |
| `v0.4.0` | FastAPI + PostgreSQL | 🔜 Tiếp theo | — |
| `v0.5.0` | Web Dashboard | 🔜 Kế hoạch | — |
| `v1.0.0` | Docker + Demo (INNOSTAR) | 🔜 Kế hoạch | — |

---

## 👤 Tác giả

**Đoàn Hoàng Việt** (VietGamer)
GitHub: [@VietGamer-UIT](https://github.com/VietGamer-UIT)

Dự án tham gia **INNOSTAR 2026** — *Cuộc thi Ý tưởng Khởi nghiệp Sinh viên VN-KR*
Chủ đề: *"Ứng dụng Khoa học Công nghệ vào Kinh doanh Thời đại số"*

---

## 📜 License

MIT License — xem [LICENSE](LICENSE)
