# 🤝 Hướng Dẫn Đóng Góp — CONTRIBUTING

> Dành cho sinh viên muốn tham gia đóng góp vào dự án

---

## Môi trường phát triển

### Yêu cầu tối thiểu
- Python 3.12+
- Git

### Cài đặt

```bash
# 1. Fork repo trên GitHub (nhấn nút Fork ở góc trên phải)
# 2. Clone về máy
git clone https://github.com/YOUR_USERNAME/TrustAgent-Forensics.git
cd TrustAgent-Forensics

# 3. Tạo virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# 4. Cài dependencies
pip install -r requirements.txt

# 5. Copy env file
copy .env.example .env  # Windows
# cp .env.example .env   # Linux/Mac

# 6. Chạy tests để confirm môi trường OK
pytest tests/ -v
# → 50 passed ✅
```

---

## Quy trình đóng góp

```
1. Tạo branch mới từ master
   git checkout -b feat/ten-tinh-nang-cua-ban

2. Code + viết tests

3. Chạy tests — đảm bảo 100% pass
   pytest tests/ -v

4. Commit với message rõ ràng
   git commit -m "feat: thêm rule thuế Nhật Bản (JP-01)"

5. Push lên fork của bạn
   git push origin feat/ten-tinh-nang-cua-ban

6. Tạo Pull Request trên GitHub
```

---

## Cách đặt tên commit

```bash
# Tính năng mới
feat: thêm rule hoàn thuế Nhật Bản

# Sửa lỗi
fix: sửa regex parse số tiền KRW có dấu phẩy

# Docs
docs: cập nhật ARCHITECTURE.md

# Tests
test: thêm edge case cho VN threshold 20M

# Refactor
refactor: tách MockParser thành file riêng

# Style/format
style: format code theo ruff

# Build/config
chore: cập nhật dependencies Python 3.13
```

---

## Viết tests đúng cách

```python
# tests/test_z3_engine.py

class TestMyNewRule:
    """Test bộ luật XYZ theo [căn cứ pháp lý]."""

    @pytest.fixture
    def solver(self):
        s = TrustAgentSolver()
        s.register_rule(MyNewRule())
        return s

    def test_valid_case_sat(self, solver):
        """Trường hợp hợp lệ → SAT."""
        result = solver.verify({"amount": 10_000, ...})
        assert result.status == VerificationStatus.SAT
        assert result.is_compliant is True

    def test_violation_case_unsat(self, solver):
        """Trường hợp vi phạm → UNSAT."""
        result = solver.verify({"amount": 99_999, ...})
        assert result.status == VerificationStatus.UNSAT
        assert result.is_compliant is False

    def test_exact_boundary(self, solver):
        """Kiểm tra đúng ngưỡng biên."""
        # Bắt buộc phải test boundary!
        pass
```

---

## Những gì được hoan nghênh đóng góp

| Loại | Ưu tiên |
|------|---------|
| Thêm business rule mới (JP, SG, US...) | ⭐⭐⭐ Cao nhất |
| Cải thiện MockParser nhận dạng ngôn ngữ | ⭐⭐⭐ Cao |
| Thêm test cases edge cases | ⭐⭐ Trung bình |
| Cải thiện documentation | ⭐⭐ Trung bình |
| Tối ưu hiệu năng Z3 | ⭐ Nếu có đo benchmark |

---

## Câu hỏi và hỗ trợ

- **Bug**: Mở [GitHub Issue](https://github.com/VietGamer-UIT/TrustAgent-Forensics/issues/new)
- **Câu hỏi**: Dùng [GitHub Discussions](https://github.com/VietGamer-UIT/TrustAgent-Forensics/discussions)
- **Tài liệu**: Đọc thư mục `docs/` trước khi hỏi
