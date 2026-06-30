# 🗺️ Lộ Trình Phát Triển — ROADMAP

> Kế hoạch 15 ngày từ ý tưởng đến sản phẩm demo INNOSTAR 2026

---

## Tổng quan

```
Phase 1 ──── Phase 2 ──── Phase 3 ──── Phase 4 ──── Phase 5 ──── Phase 6
   ✅            ✅          🔜           🔜           🔜           🔜
Z3 Engine   Semantic    LangGraph    FastAPI +    Dashboard    Docker +
+ Rules      Parser     Multi-Agent  PostgreSQL    Web UI      Demo Pack
 (Day 1-2)  (Day 3-4)  (Day 5-7)   (Day 8-10)  (Day 11-12)  (Day 13-15)
```

---

## ✅ Phase 1 — Z3 Verification Engine *(HOÀN THÀNH)*

**Mục tiêu**: Xây dựng lõi kiểm chứng toán học

**Đã làm**:
- [x] `TrustAgentSolver` — wrapper Z3, rule registry pattern
- [x] `VietnamCashPaymentRule` — Thông tư 96/2015 (20M VNĐ cash threshold)
- [x] `KoreaTaxRefundRule` — Incheon Airport (30K/75K KRW thresholds)
- [x] Pydantic models: `TransactionData`, `TaxRefundData`, `VerificationResult`
- [x] Abstract `BusinessRule` base class (Strategy pattern)
- [x] **26 unit tests** — 100% pass

**Kết quả**: SAT/UNSAT trong < 3ms, deterministic, không thể bypass

---

## ✅ Phase 2 — Gemini Semantic Parser *(HOÀN THÀNH)*

**Mục tiêu**: Cầu nối ngôn ngữ tự nhiên ↔ JSON có cấu trúc

**Đã làm**:
- [x] `SemanticParser` — auto-switch Gemini/Mock
- [x] `GeminiSemanticParser` — dùng Gemini 2.0 Flash API thật
- [x] `MockSemanticParser` — regex-based, không cần API key (dev/test)
- [x] Prompt templates: detect scenario, extract VN/KR data, explain result
- [x] Pydantic schemas: `ParseResult`, `ParsedVNTransaction`, `ParsedKRTaxRefund`
- [x] **24 unit tests** + end-to-end pipeline tests — 100% pass

**Kết quả**: 50 tổng tests pass, pipeline NL → Z3 hoạt động end-to-end

---

## 🔜 Phase 3 — LangGraph Multi-Agent *(Ngày 5-7)*

**Mục tiêu**: Orchestration thông minh với vòng lặp tự sửa lỗi

**Kế hoạch**:
- [ ] Thiết kế LangGraph workflow graph
- [ ] `ParserAgent` — gọi SemanticParser
- [ ] `VerifierAgent` — gọi TrustAgentSolver
- [ ] `ExplainerAgent` — tạo phản hồi thân thiện
- [ ] Self-correction loop — nếu confidence thấp → parse lại
- [ ] Human-in-the-loop — giao dịch lớn cần phê duyệt thủ công
- [ ] Tests cho workflow

**Files sẽ tạo**:
```
src/agents/
├── __init__.py
├── graph.py          # LangGraph StateGraph definition
├── nodes.py          # ParserAgent, VerifierAgent, ExplainerAgent
├── state.py          # AgentState Pydantic model
└── workflow.py       # Compiled graph + run() function
tests/
└── test_agents.py
```

---

## 🔜 Phase 4 — FastAPI Backend + PostgreSQL *(Ngày 8-10)*

**Mục tiêu**: REST API production-ready + audit trail bất biến

**Kế hoạch**:
- [ ] FastAPI app với async endpoints
- [ ] `POST /api/v1/verify` — pipeline chính
- [ ] `GET /api/v1/audit/{id}` — tra cứu kết quả cũ
- [ ] `GET /api/v1/rules` — liệt kê rules đang active
- [ ] PostgreSQL schema với JSONB cho raw_input + result
- [ ] SQLAlchemy async models + Alembic migrations
- [ ] Swagger UI tự động

**Files sẽ tạo**:
```
src/
├── api/
│   ├── main.py         # FastAPI app
│   ├── routes/
│   │   ├── verify.py   # POST /verify
│   │   └── audit.py    # GET /audit
│   └── middleware.py   # CORS, rate limit
├── database/
│   ├── models.py       # SQLAlchemy models
│   ├── session.py      # Async session
│   └── migrations/     # Alembic
docker-compose.yml       # PostgreSQL + App
```

---

## 🔜 Phase 5 — Web Dashboard *(Ngày 11-12)*

**Mục tiêu**: Giao diện trực quan để demo INNOSTAR

**Kế hoạch**:
- [ ] Single-page app (HTML + vanilla JS)
- [ ] Input box để nhập câu yêu cầu
- [ ] Real-time hiển thị: Parse result → Z3 result → Explanation
- [ ] Bảng audit trail với filter/search
- [ ] Biểu đồ thống kê (SAT vs UNSAT rate)
- [ ] Dark mode design phù hợp demo

---

## 🔜 Phase 6 — Docker + Demo Package *(Ngày 13-15)*

**Mục tiêu**: Sản phẩm hoàn chỉnh, một lệnh chạy được

**Kế hoạch**:
- [ ] `Dockerfile` cho backend
- [ ] `docker-compose.yml` — app + postgres + dashboard
- [ ] `README` cập nhật với hướng dẫn cài đặt 5 phút
- [ ] Demo script chạy 10 kịch bản mẫu
- [ ] Presentation deck (slide) cho INNOSTAR
- [ ] Video demo 3 phút

---

## Metrics mục tiêu cho INNOSTAR

| Metric | Mục tiêu | Hiện tại |
|--------|----------|----------|
| Tests | > 80 | 50 ✅ |
| Verification speed | < 10ms | ~3ms ✅ |
| API response time | < 500ms | N/A (Phase 4) |
| Code coverage | > 80% | ~85% ✅ |
| Supported rules | >= 2 quốc gia | 2 ✅ |
| Languages supported | VN + EN | ✅ |
