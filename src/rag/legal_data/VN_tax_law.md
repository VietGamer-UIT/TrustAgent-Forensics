# THÔNG TƯ 96/2015/TT-BTC
# Hướng dẫn về thuế thu nhập doanh nghiệp
# Ban hành ngày 22 tháng 6 năm 2015
# Có hiệu lực từ ngày 06/08/2015

## Điều 4. Các khoản chi không được trừ khi xác định thu nhập chịu thuế

### 1. Các khoản chi không đáp ứng đủ các điều kiện quy định tại Khoản 1 Điều 3 Thông tư này.

### Khoản 1. Điểm c — Thanh toán bằng tiền mặt

Phần chi phí mua hàng hóa, dịch vụ từng lần có giá trị từ **20 triệu đồng** (hai mươi triệu đồng) trở lên
(đã bao gồm thuế giá trị gia tăng) mà tại thời điểm mua hàng hóa, dịch vụ doanh nghiệp không thực
hiện thanh toán qua ngân hàng, đến thời điểm lập hồ sơ quyết toán thuế doanh nghiệp vẫn chưa
thực hiện thanh toán qua ngân hàng thì không được tính vào chi phí được trừ khi xác định thu nhập
chịu thuế.

**Ngưỡng thanh toán tiền mặt tối đa: 20,000,000 VNĐ**
**VN_CASH_THRESHOLD = 20000000**

Trường hợp mua hàng hóa, dịch vụ từng lần có giá trị từ 20 triệu đồng trở lên ghi trên hóa đơn mà
doanh nghiệp thanh toán bằng tiền mặt thì khoản chi này KHÔNG được ghi nhận là chi phí được trừ
khi xác định thu nhập chịu thuế (TNDN).

---

## Phương thức thanh toán được chấp nhận (>= 20 triệu VNĐ)

Các phương thức thanh toán không dùng tiền mặt được chấp nhận bao gồm:
- Chuyển khoản ngân hàng (bank transfer)
- Thẻ tín dụng / thẻ ghi nợ (credit card / debit card)
- Ví điện tử được ngân hàng xác nhận (e-wallet with bank confirmation)
- Séc (cheque)

---

## Lịch sử thay đổi ngưỡng

| Văn bản pháp luật | Ngưỡng tiền mặt | Hiệu lực |
|-------------------|----------------|----------|
| Thông tư 96/2015/TT-BTC | 20,000,000 VNĐ | 06/08/2015 |
| Thông tư 78/2014/TT-BTC | 20,000,000 VNĐ | 02/08/2014 |

**Ngưỡng hiện hành (2026): 20,000,000 VNĐ (hai mươi triệu đồng)**

---

## Chú thích kỹ thuật (cho hệ thống RAG)

```json
{
  "rule_id": "VN_CASH_PAYMENT_THRESHOLD",
  "threshold_key": "VN_CASH_THRESHOLD",
  "threshold_value": 20000000,
  "unit": "VND",
  "legal_basis": "Thông tư 96/2015/TT-BTC, Điều 4, Khoản 1, Điểm c",
  "effective_date": "2015-08-06",
  "country": "VN",
  "scenario": "vn_payment"
}
```
