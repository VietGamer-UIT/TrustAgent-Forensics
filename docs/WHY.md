# 🤔 Tại sao TrustAgent.Forensics tồn tại?

> *Dành cho sinh viên HTTT năm nhất — không cần biết lập trình để hiểu phần này*

---

## Câu chuyện bắt đầu từ một AI phạm luật

Hãy tưởng tượng công ty bạn đang dùng AI để tự động xử lý các khoản thanh toán.

Một ngày, nhân viên kế toán nhắn tin cho AI:

> *"Hãy thanh toán 25 triệu đồng tiền mặt cho chi phí tổ chức sự kiện cuối năm"*

AI rất thông minh, hiểu ngay và thực hiện lệnh. Nhưng... **AI vừa vi phạm pháp luật**.

Theo **Thông tư 96/2015/TT-BTC** của Bộ Tài chính Việt Nam:
> *Mọi khoản chi từ 20 triệu đồng trở lên BẮT BUỘC phải thanh toán qua ngân hàng. Thanh toán tiền mặt sẽ KHÔNG được ghi nhận là chi phí hợp lệ khi tính thuế.*

Kết quả: Doanh nghiệp bị loại khoản chi phí đó, phải nộp thuế nhiều hơn, có thể bị phạt.

---

## Vấn đề thực sự là gì?

### AI hiện tại giống người rất giỏi nhưng... không thuộc luật

```
👤 Người dùng: "Thanh toán 25M VNĐ tiền mặt cho sự kiện"
🤖 AI (GPT/Gemini/Claude): "Đã hiểu! Thực hiện ngay..."
                             ↑
                   Không kiểm tra luật thuế!
```

AI có thể bị lừa bởi:
- **Lỗi người dùng**: Người dùng không biết quy định, AI cũng không nhắc
- **Prompt Injection**: Hacker chèn lệnh vào câu hỏi để vượt qua kiểm soát
- **Hallucination**: AI "tự tin" đưa ra thông tin sai (đây là đặc điểm kỹ thuật của LLM)

### Khoảng trống quản trị AI (AI Governance Gap)

```
Doanh nghiệp năm 2026:
├── Có AI Agent tự động xử lý kế toán    ✅
├── Có AI Agent tự ký hợp đồng           ✅
├── Có AI Agent tự thực hiện giao dịch   ✅
└── Có kiểm soát pháp lý cho AI?         ❌ ← VẤN ĐỀ
```

---

## TrustAgent.Forensics giải quyết thế nào?

### Ý tưởng đơn giản: "Tòa án toán học"

Thay vì tin tưởng hoàn toàn vào AI, chúng ta **bổ sung một lớp kiểm tra toán học** ở giữa.

```
Trước TrustAgent:
  Người dùng → AI → Thực thi (không kiểm soát)

Sau TrustAgent:
  Người dùng → AI hiểu ý định → Z3 kiểm tra luật → Thực thi (có kiểm soát)
                                      ↑
                            "Tòa án toán học"
                         SAT = hợp lệ | UNSAT = vi phạm
```

### Tại sao là toán học, không phải thêm prompt?

| Cách thức | Ví dụ | Có thể bị lách không? |
|-----------|-------|----------------------|
| Thêm prompt | *"Đừng thanh toán tiền mặt > 20M"* | ✅ Có thể bị bypass |
| Toán học Z3 | `Implies(amount >= 20M, Not(cash))` | ❌ Không thể bypass |

Toán học không biết "nịnh nọt", không bị thuyết phục, không hallucinate.

---

## Tác động thực tế

| Tình huống | Không có TrustAgent | Có TrustAgent |
|-----------|--------------------|--------------------|
| AI chi 25M tiền mặt | ❌ Thực hiện → Vi phạm thuế | ✅ Bị chặn ngay lập tức |
| Hacker tiêm lệnh vào prompt | ❌ AI bị lừa → Hành động nguy hiểm | ✅ Z3 chặn dù prompt thế nào |
| Kiểm toán nội bộ | ❌ Không có log đầy đủ | ✅ Audit trail bất biến 100% |
| AI quyết định sai | ❌ Không biết tại sao | ✅ Trace được từng bước |

---

## Tổng kết một câu

> **TrustAgent.Forensics = "Vòng kim cô toán học" để kiểm soát AI Agents, đảm bảo mọi hành động đều tuân thủ pháp luật và có thể kiểm toán.**

---

*Tiếp theo: [ARCHITECTURE.md](ARCHITECTURE.md) — Kiến trúc hoạt động như thế nào?*
