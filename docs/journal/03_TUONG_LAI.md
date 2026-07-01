# 📓 NHẬT KÝ #3 — KẾ HOẠCH TƯƠNG LAI
# Roadmap chi tiết cho các phase chưa làm
# Quy tắc: Cập nhật file này mỗi khi có quyết định mới về hướng đi

> **Mục đích**: Bất kỳ AI model hay developer nào đọc file này
> đều biết ngay bước tiếp theo là gì mà không cần hỏi lại.

---

## 📊 Tổng quan Roadmap

```
v0.1.0  ✅  Z3 Engine
v0.2.0  ✅  Semantic Parser (Gemini)
v0.3.0  ✅  LangGraph Multi-Agent
v0.3.5  ✅  Legal RAG Module
v0.4.0  🔜  FastAPI + PostgreSQL        ← BẮT ĐẦU TIẾP THEO
v0.5.0  🔜  Web Dashboard
v1.0.0  🔜  Docker + Demo (INNOSTAR)
```

---

## 🔜 PHASE 4 — FastAPI Backend + PostgreSQL
**Ưu tiên: CAO — Cần hoàn thành để có thể demo**

### Mục tiêu
Biến hệ thống thành một REST API hoàn chỉnh với audit trail bất biến.

### Các file cần tạo

```
src/api/
├── __init__.py
├── main.py              ← FastAPI app instance, CORS, startup events
├── dependencies.py      ← Dependency injection (DB session, workflow)
├── schemas.py           ← Request/Response Pydantic models
└── routes/
    ├── __init__.py
    ├── verify.py        ← POST /api/v1/verify
    └── audit.py         ← GET /api/v1/audit/{id}, GET /api/v1/audit (list)

src/database/
├── __init__.py
├── models.py            ← SQLAlchemy ORM (AuditLog table + JSONB columns)
├── session.py           ← AsyncSession factory (asyncpg driver)
└── repository.py        ← CRUD: save_audit(), get_audit_by_id()
```

### Thiết kế Database

```sql
-- AuditLog table (PostgreSQL 17, JSONB)
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    -- Input
    user_input      TEXT NOT NULL,

    -- Parse result
    scenario_type   VARCHAR(50),
    parse_confidence FLOAT,

    -- RAG thresholds used
    legal_thresholds JSONB,   -- {"VN_CASH_THRESHOLD": 20000000}

    -- Z3 result
    z3_status       VARCHAR(20),   -- SAT | UNSAT | UNKNOWN
    is_compliant    BOOLEAN,
    violations      JSONB,         -- [{rule_name, violation_detail, ...}]

    -- Response
    explanation     TEXT,
    duration_ms     FLOAT
);
```

### API Endpoints

| Method | Path | Mô tả |
|--------|------|-------|
| `POST` | `/api/v1/verify` | Kiểm tra giao dịch |
| `GET` | `/api/v1/audit/{id}` | Xem chi tiết 1 lần kiểm tra |
| `GET` | `/api/v1/audit` | Danh sách lịch sử (paginated) |
| `GET` | `/health` | Health check |
| `GET` | `/` | API info |

### Request/Response mẫu

```json
// POST /api/v1/verify
// Request:
{"user_input": "Thanh toán tiền mặt 25 triệu"}

// Response 200:
{
  "audit_id": "550e8400-e29b-41d4-a716-446655440000",
  "scenario_type": "vn_payment",
  "z3_status": "UNSAT",
  "is_compliant": false,
  "violations": [
    {
      "rule_name": "vn_cash_payment_threshold",
      "violation_detail": "Số tiền 25,000,000 VNĐ ≥ ngưỡng 20,000,000 VNĐ...",
      "legal_reference": "Thông tư 96/2015/TT-BTC"
    }
  ],
  "explanation": "❌ Giao dịch bị từ chối...",
  "duration_ms": 5.2
}
```

### Yêu cầu môi trường
```env
# .env (thêm vào .env.example)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/trustagent
```

### Tests cần viết
- `tests/test_api.py` — dùng `httpx.AsyncClient` + `pytest-asyncio`
- Mock DB session để test không cần PostgreSQL thật

### Tiêu chí hoàn thành
- [ ] 111 + N tests pass (N tests mới cho API)
- [ ] `POST /api/v1/verify` hoạt động đúng
- [ ] Audit record được lưu vào DB sau mỗi request
- [ ] Git tag `v0.4.0-fastapi-backend`

---

## 🔜 PHASE 5 — Web Dashboard
**Ưu tiên: TRUNG BÌNH — Cần để INNOSTAR demo**

### Mục tiêu
Giao diện web đẹp để demo trực tiếp cho ban giám khảo INNOSTAR 2026.

### Thiết kế UI

```
┌─────────────────────────────────────────────────┐
│  🛡️ TrustAgent.Forensics                        │
│  AI Governance Platform                          │
├─────────────────────────────────────────────────┤
│  📝 Nhập yêu cầu:                               │
│  ┌─────────────────────────────────────────┐     │
│  │ "Thanh toán tiền mặt 25 triệu..."       │     │
│  └─────────────────────────────────────────┘     │
│  [🔍 Kiểm tra]                                   │
├─────────────────────────────────────────────────┤
│  ❌ UNSAT — Giao dịch bị từ chối                │
│  Lý do: Vi phạm Thông tư 96/2015...            │
│  Thời gian: 5.2ms                               │
├─────────────────────────────────────────────────┤
│  📋 Lịch sử kiểm tra (10 gần nhất)             │
│  [...]                                           │
└─────────────────────────────────────────────────┘
```

### Stack
- Vanilla HTML + CSS + JavaScript (không cần framework)
- Gọi API: `fetch('/api/v1/verify', {method: 'POST', ...})`
- Animation: CSS transitions + keyframes

### Tiêu chí hoàn thành
- [ ] Demo chạy được ở `http://localhost:8000`
- [ ] Đẹp, responsive, ấn tượng với ban giám khảo

---

## 🔜 PHASE 6 — Docker + Demo Package
**Ưu tiên: CAO — Submit cho INNOSTAR**

### Mục tiêu
1 lệnh → toàn bộ hệ thống chạy.

### docker-compose.yml

```yaml
version: "3.9"
services:
  db:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_DB: trustagent
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data

  app:
    build: .
    ports: ["8000:8000"]
    depends_on: [db]
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/trustagent

volumes:
  pgdata:
```

### Tiêu chí hoàn thành
- [ ] `docker-compose up --build` → `http://localhost:8000` hoạt động
- [ ] README có hướng dẫn deploy 1 lệnh
- [ ] Git tag `v1.0.0-demo`

---

## 💡 Ghi chú kỹ thuật cho tương lai

### pgvector trong Phase 4+
Phase 4 dùng PostgreSQL + pgvector cho **audit trail search**
(tìm kiếm các giao dịch tương tự trong lịch sử):
```sql
-- Sau Phase 4, có thể thêm:
ALTER TABLE audit_logs ADD COLUMN embedding vector(768);
CREATE INDEX ON audit_logs USING ivfflat (embedding vector_cosine_ops);
```

### Mở rộng legal corpus
Khi thêm luật mới (ví dụ Nghị định 123/2020/NĐ-CP):
1. Thêm file `.md` vào `src/rag/legal_data/`
2. Thêm entry vào `_SCENARIO_TO_FILE` trong `retriever.py`
3. Thêm default vào `FALLBACK_THRESHOLDS` trong `extractor.py`
4. Tạo `BusinessRule` class mới
5. Đăng ký rule trong `nodes.py`
