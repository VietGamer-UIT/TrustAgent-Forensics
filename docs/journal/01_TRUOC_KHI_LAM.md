# 📓 NHẬT KÝ #1 — KẾ HOẠCH TRƯỚC KHI LÀM
# Ghi lại ý định, lý do, và những rủi ro TRƯỚC KHI bắt tay vào code
# Quy tắc: Phải điền file này trước khi mở editor

> **Quy ước**: Mỗi khi bắt đầu một task mới (dù nhỏ), ghi vào đây trước.
> Sau khi hoàn thành, chuyển sang `02_DA_HOAN_THANH.md`.

---

## ✍️ CÁCH DÙNG FILE NÀY

Trước khi code bất cứ thứ gì, điền vào template dưới đây:

```
## [YYYY-MM-DD] — Tên task
- Mục tiêu: ...
- Lý do cần làm: ...
- Phương pháp: ...
- Rủi ro / lưu ý kỹ thuật: ...
- Tiêu chí hoàn thành: ...
```

---

## [2026-07-01] — Phase 4: FastAPI Backend + PostgreSQL Audit Trail

**Mục tiêu:**
Xây dựng lớp API và lưu trữ để hệ thống có thể nhận request HTTP từ bên ngoài, thực thi pipeline RAG → Z3, và lưu lại toàn bộ lịch sử kiểm tra vào database bất biến.

**Lý do cần làm:**
- Hiện tại toàn bộ hệ thống chỉ chạy được qua Python code — chưa có REST API
- Doanh nghiệp cần gọi API để tích hợp vào hệ thống nội bộ của họ
- Forensics layer = audit trail không thể xóa → cần PostgreSQL 17 với JSONB

**Phương pháp dự kiến:**

```
src/api/
├── main.py              ← FastAPI app + CORS + startup
├── routes/
│   ├── verify.py        ← POST /api/v1/verify
│   └── audit.py         ← GET  /api/v1/audit/{id}
└── schemas.py           ← Request/Response Pydantic models

src/database/
├── models.py            ← SQLAlchemy ORM (AuditLog table)
├── session.py           ← Async DB session
└── repository.py        ← CRUD functions
```

**Endpoint chính:**
```
POST /api/v1/verify
Body: {"user_input": "Thanh toán tiền mặt 25 triệu..."}

Response 200:
{
  "audit_id": "uuid-...",
  "scenario_type": "vn_payment",
  "z3_status": "UNSAT",
  "is_compliant": false,
  "violations": [...],
  "explanation": "❌ Giao dịch bị từ chối...",
  "duration_ms": 5.2
}
```

**Rủi ro / lưu ý kỹ thuật:**
- PostgreSQL cần chạy (Docker hoặc local install)
- Async SQLAlchemy khác biết với sync — dùng `asyncpg` driver
- pgvector extension cần enable cho Phase 4.5 nếu muốn audit search
- Không được thay đổi `TrustAgentWorkflow.run()` — chỉ gọi nó từ API

**Tiêu chí hoàn thành:**
- [ ] `pytest tests/test_api.py` — tất cả pass (dùng `httpx.AsyncClient`)
- [ ] `POST /api/v1/verify` trả về đúng format
- [ ] Audit log được lưu vào PostgreSQL sau mỗi request
- [ ] Git tag `v0.4.0-fastapi-backend`

---

## [2026-07-01] — Phase 5: Web Dashboard

**Mục tiêu:**
Giao diện web đơn giản để demo hệ thống tại INNOSTAR 2026.

**Phương pháp dự kiến:**
- HTML + CSS + Vanilla JS (không cần framework)
- Trang chính: input box → submit → hiển thị kết quả SAT/UNSAT với animation
- Bảng lịch sử giao dịch (lấy từ `/api/v1/audit`)

**Tiêu chí hoàn thành:**
- [ ] Demo chạy được ở localhost:8080
- [ ] Nhìn đẹp, dễ dùng cho judge tại INNOSTAR

---

## [2026-07-01] — Phase 6: Docker + Demo Package

**Mục tiêu:**
Đóng gói toàn bộ hệ thống vào Docker Compose để chạy 1 lệnh.

**Phương pháp:**
```yaml
# docker-compose.yml
services:
  app:    ← FastAPI (src/)
  db:     ← PostgreSQL 17 + pgvector
  nginx:  ← Static files (dashboard)
```

**Tiêu chí hoàn thành:**
- [ ] `docker-compose up` → hệ thống chạy hoàn toàn
- [ ] README có hướng dẫn deploy 1 lệnh
- [ ] Git tag `v1.0.0-demo`
