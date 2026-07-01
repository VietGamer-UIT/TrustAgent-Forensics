# 한국 세금 환급 규정 (Korean Tax Refund Regulations)
# 외국인 관광객 부가가치세 환급 제도
# 근거: 조세특례제한법 제107조 (Tax Restriction Special Cases Act, Article 107)
# 시행: 인천국제공항 면세 쇼핑 (Incheon International Airport Duty-Free)

## 제1조 — 환급 자격 요건 (Eligibility Requirements)

### 최소 구매 금액 (Minimum Purchase Amount)

외국인 관광객이 부가가치세 환급을 받기 위해서는 **1회 구매 금액**이 다음 조건을 충족해야 합니다:

- 단일 매장 1회 구매액 기준: **30,000원** (삼만 원) 이상
- 부가가치세 포함 금액 기준

**최소 구매 기준금액: 30,000 KRW**
**KR_MIN_RECEIPT_AMOUNT = 30000**

구매 금액이 30,000원 미만인 경우 부가가치세 환급 신청 자격이 없습니다 (is_eligible = False).
구매 금액이 30,000원 이상인 경우 부가가치세 환급 신청 자격이 있습니다 (is_eligible = True).

---

## 제2조 — 환급 절차 (Refund Procedures)

### 환급 금액에 따른 처리 방식 (Processing Method by Refund Amount)

#### 2.1 자동 키오스크 환급 (Automated Kiosk Refund)

환급 금액이 **75,000원** (칠만오천 원) **미만**인 경우:
- 인천국제공항 자동 환급 키오스크 이용 가능
- 세관 검사 불필요 (needs_customs_check = False)
- 출국 전 공항 내 키오스크에서 즉시 환급

**소액 환급 키오스크 상한선: 75,000 KRW**
**KR_CUSTOMS_CHECK_THRESHOLD = 75000**

#### 2.2 세관 검사 필수 (Mandatory Customs Inspection)

환급 금액이 **75,000원** (칠만오천 원) **이상**인 경우:
- 반드시 세관 직원의 검사를 받아야 함 (needs_customs_check = True)
- 구매 물품과 영수증을 세관에 제시
- 세관 확인 후 환급 처리

**대액 환급 세관 검사 기준: 75,000 KRW 이상**

---

## 지원 대상 매장 유형 (Eligible Shop Types)

- 면세점 (Duty-Free Shop): is_tax_free_shop = True ✅
- 시내 면세점: is_tax_free_shop = True ✅
- 일반 소매점 (TAX-FREE 가맹점): is_tax_free_shop = True ✅

---

## 기준금액 이력 (Historical Thresholds)

| 규정 | 최소 구매액 | 세관 검사 기준 | 시행일 |
|------|-----------|--------------|--------|
| 현행 규정 (2026) | 30,000 KRW | 75,000 KRW | - |

---

## 시스템 메타데이터 (System Metadata for RAG)

```json
{
  "rule_id": "KR_TAX_REFUND",
  "thresholds": {
    "KR_MIN_RECEIPT_AMOUNT": 30000,
    "KR_CUSTOMS_CHECK_THRESHOLD": 75000
  },
  "unit": "KRW",
  "legal_basis": "조세특례제한법 제107조 (Korean Tax Refund Regulations, Incheon Airport)",
  "country": "KR",
  "scenario": "kr_tax_refund"
}
```
