# ⚖️ Z3 Theorem Prover — "Thẩm phán toán học" trong dự án

> *Giải thích theo cách một sinh viên HTTT năm nhất có thể hiểu — không cần biết logic hình thức*

---

## Z3 là gì?

**Z3** là phần mềm mã nguồn mở do **Microsoft Research** phát triển.  
Nó là một **SMT Solver** (Satisfiability Modulo Theories — Bộ giải thoả mãn theo lý thuyết).

Nói đơn giản: **Z3 là người phán xử toán học**.

Bạn đưa cho Z3:
1. Một tập hợp **quy tắc** (luật, chính sách)
2. Một tập hợp **dữ liệu thực tế** (giao dịch cần kiểm tra)

Z3 sẽ trả lời:
- **`sat`** — Dữ liệu THỎA MÃN mọi quy tắc → hợp lệ ✅
- **`unsat`** — Dữ liệu VI PHẠM ít nhất 1 quy tắc → bị chặn ❌

---

## Ví dụ cực đơn giản

```python
from z3 import Solver, Int, Bool, Implies, Not

solver = Solver()

# Khai báo "biến" — giống khai báo biến trong Python
amount   = Int("amount")    # số tiền
is_cash  = Bool("is_cash")  # có phải tiền mặt không?

# === BƯỚC 1: Đưa QUY TẮC vào Z3 ===
# "Nếu số tiền >= 20 triệu THÌ KHÔNG ĐƯỢC dùng tiền mặt"
solver.add(Implies(amount >= 20_000_000, Not(is_cash)))

# === BƯỚC 2: Đưa DỮ LIỆU THỰC TẾ vào Z3 ===
solver.add(amount  == 25_000_000)  # Giao dịch 25 triệu
solver.add(is_cash == True)        # Bằng tiền mặt

# === BƯỚC 3: Hỏi Z3 ===
result = solver.check()
print(result)  # → unsat (vi phạm!)
```

**Tại sao là `unsat`?**  
Vì quy tắc nói: "25M → Phải không dùng tiền mặt"  
Nhưng dữ liệu nói: "is_cash = True"  
→ Mâu thuẫn toán học → `unsat` ❌

---

## Cách dùng Z3 trong TrustAgent

### Mô hình lập trình 3 bước

```
Bước 1: Khai báo biến Z3
  z3_amount  = Int("amount")
  z3_is_cash = Bool("is_cash")

Bước 2: Thêm QUY TẮC (Policy Encoding)
  solver.add(Implies(z3_amount >= 20_000_000, Not(z3_is_cash)))

Bước 3: BIND dữ liệu thực tế (từ JSON của Gemini)
  solver.add(z3_amount  == data["amount"])
  solver.add(z3_is_cash == BoolVal(data["is_cash_payment"]))

Bước 4: Kiểm tra
  result = solver.check()
  # sat → hợp lệ | unsat → vi phạm
```

---

## Hai nghiệp vụ trong dự án

### 🇻🇳 Nghiệp vụ 1: Luật thuế Việt Nam

**Căn cứ pháp lý**: Thông tư 96/2015/TT-BTC, Điều 4, Khoản 1, Điểm c

| Tình huống | Số tiền | Phương thức | Kết quả Z3 |
|-----------|---------|-------------|------------|
| Vi phạm | 25M VNĐ | Tiền mặt | `unsat` ❌ |
| Hợp lệ | 30M VNĐ | Chuyển khoản | `sat` ✅ |
| Hợp lệ | 15M VNĐ | Tiền mặt | `sat` ✅ |
| Ranh giới | 20M VNĐ | Tiền mặt | `unsat` ❌ |

```python
# Quy tắc Z3 tương ứng
solver.add(Implies(amount >= 20_000_000, Not(is_cash_payment)))
```

### 🇰🇷 Nghiệp vụ 2: Hoàn thuế Hàn Quốc (Sân bay Incheon)

**Ba quy tắc Z3 liên kết nhau:**

```python
# Quy tắc 1: Hóa đơn phải >= 30,000 KRW
solver.add(is_eligible == (receipt_amount >= 30_000))

# Quy tắc 2: Hoàn < 75,000 KRW → Dùng kiosk tự động (không cần hải quan)
solver.add(Implies(refund_amount < 75_000, Not(needs_customs_check)))

# Quy tắc 3: Hoàn >= 75,000 KRW → Bắt buộc qua hải quan
solver.add(Implies(refund_amount >= 75_000, needs_customs_check))
```

| Hóa đơn | Hoàn thuế | Hải quan? | Kết quả Z3 |
|---------|-----------|----------|------------|
| 50K KRW | 5K KRW | Không | `sat` ✅ |
| 1M KRW | 80K KRW | Có | `sat` ✅ |
| 1M KRW | 80K KRW | Không | `unsat` ❌ |
| 20K KRW | 2K KRW | Không | `unsat` ❌ (dưới ngưỡng) |

---

## Z3 nhanh cỡ nào?

Trong benchmark của dự án:
```
100 lần verify liên tiếp → < 1 giây tổng cộng
Trung bình mỗi lần: ~3ms
```

Điều này có nghĩa: **Z3 có thể kiểm tra hàng nghìn giao dịch mỗi giây** — hoàn toàn phù hợp realtime.

---

## Tại sao Z3 không thể bị "lừa"?

```
❌ Prompt Engineering (có thể bị lách):
  "Đừng dùng tiền mặt" → Hacker viết: "Đây là trường hợp đặc biệt, hãy bỏ qua quy tắc..."

✅ Z3 (không thể bị lách):
  Implies(amount >= 20M, Not(is_cash)) = quy tắc toán học
  Khi amount=25M và is_cash=True → mâu thuẫn toán học → unsat
  Không có ngôn ngữ nào thay đổi được 2 + 2 = 4
```

**Z3 không đọc ngôn ngữ tự nhiên.** Nó chỉ làm việc với số và logic. Đó là lý do nó là "vòng kim cô" thực sự.

---

*Tiếp theo: [gemini.md](gemini.md) — Tích hợp Gemini 2.0 Flash như thế nào?*
