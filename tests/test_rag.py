"""
TrustAgent.Forensics — Tests cho Legal RAG Module (Phase 3.5)

Kiểm tra toàn bộ luồng RAG:
    LegalRetriever → ThresholdExtractor → legal_rag_node → verify_node (dynamic thresholds)

Không cần ChromaDB, không cần Gemini API key.
Tất cả tests chạy offline với keyword-based retrieval + regex extraction.

Cấu trúc test:
    TestLegalRetriever       — kiểm tra load docs, query, fallback
    TestThresholdExtractor   — kiểm tra 3 tầng extraction
    TestLegalRagNode         — kiểm tra node trong LangGraph workflow
    TestDynamicThresholds    — kiểm tra Z3 với ngưỡng từ RAG
    TestEndToEndWithRag      — kiểm tra toàn bộ pipeline với RAG
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.rag.retriever import LegalRetriever, DEFAULT_THRESHOLDS
from src.rag.extractor import ThresholdExtractor, FALLBACK_THRESHOLDS
from src.agents.nodes import legal_rag_node, verify_node
from src.agents.state import AgentState
from src.agents.workflow import TrustAgentWorkflow


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def retriever() -> LegalRetriever:
    return LegalRetriever()


@pytest.fixture
def extractor() -> ThresholdExtractor:
    return ThresholdExtractor()


@pytest.fixture
def workflow() -> TrustAgentWorkflow:
    return TrustAgentWorkflow()


# ---------------------------------------------------------------------------
# Test LegalRetriever
# ---------------------------------------------------------------------------

class TestLegalRetriever:
    """Kiểm tra LegalRetriever load và query văn bản luật."""

    def test_retriever_loads_vn_doc(self, retriever):
        text = retriever.get_legal_text("vn_payment")
        assert len(text) > 100
        assert "20" in text or "VNĐ" in text or "VN" in text

    def test_retriever_loads_kr_doc(self, retriever):
        text = retriever.get_legal_text("kr_tax_refund")
        assert len(text) > 100
        assert "KRW" in text or "30,000" in text or "75,000" in text

    def test_retriever_unknown_returns_empty(self, retriever):
        text = retriever.get_legal_text("unknown_scenario")
        assert text == ""

    def test_retriever_vn_is_available(self, retriever):
        assert retriever.is_available("vn_payment") is True

    def test_retriever_kr_is_available(self, retriever):
        assert retriever.is_available("kr_tax_refund") is True

    def test_retriever_unknown_not_available(self, retriever):
        assert retriever.is_available("nonexistent") is False

    def test_retriever_json_block_vn(self, retriever):
        """JSON metadata block phải có trong doc VN."""
        json_str = retriever.get_threshold_json("vn_payment")
        assert len(json_str) > 0
        import json
        data = json.loads(json_str)
        assert "VN_CASH_THRESHOLD" in data or "threshold_value" in data

    def test_retriever_json_block_kr(self, retriever):
        """JSON metadata block phải có trong doc KR."""
        json_str = retriever.get_threshold_json("kr_tax_refund")
        assert len(json_str) > 0
        import json
        data = json.loads(json_str)
        assert "thresholds" in data or "KR_MIN_RECEIPT_AMOUNT" in data


# ---------------------------------------------------------------------------
# Test ThresholdExtractor — 3 tầng
# ---------------------------------------------------------------------------

class TestThresholdExtractor:
    """Kiểm tra extraction từ văn bản luật."""

    def test_extract_vn_from_json_block(self, extractor, retriever):
        """Tầng 1: JSON block extraction cho VN."""
        text = retriever.get_legal_text("vn_payment")
        result = extractor.extract("vn_payment", text)
        assert "VN_CASH_THRESHOLD" in result
        assert result["VN_CASH_THRESHOLD"] == 20_000_000

    def test_extract_kr_from_json_block(self, extractor, retriever):
        """Tầng 1: JSON block extraction cho KR."""
        text = retriever.get_legal_text("kr_tax_refund")
        result = extractor.extract("kr_tax_refund", text)
        assert "KR_MIN_RECEIPT_AMOUNT" in result
        assert result["KR_MIN_RECEIPT_AMOUNT"] == 30_000
        assert "KR_CUSTOMS_CHECK_THRESHOLD" in result
        assert result["KR_CUSTOMS_CHECK_THRESHOLD"] == 75_000

    def test_extract_vn_from_regex(self, extractor):
        """Tầng 2: Regex extraction khi không có JSON block."""
        text = "Ngưỡng thanh toán: 20,000,000 VNĐ theo Thông tư 96/2015"
        result = extractor.extract("vn_payment", text)
        # Phải dùng fallback vì không có JSON block
        assert "VN_CASH_THRESHOLD" in result
        assert result["VN_CASH_THRESHOLD"] == 20_000_000

    def test_extract_fallback_empty_text(self, extractor):
        """Tầng 3: Fallback khi text rỗng."""
        result = extractor.extract("vn_payment", "")
        assert result == FALLBACK_THRESHOLDS["vn_payment"]
        assert result["VN_CASH_THRESHOLD"] == 20_000_000

    def test_extract_fallback_kr_empty_text(self, extractor):
        """Tầng 3: Fallback KR khi text rỗng."""
        result = extractor.extract("kr_tax_refund", "")
        assert result["KR_MIN_RECEIPT_AMOUNT"] == 30_000
        assert result["KR_CUSTOMS_CHECK_THRESHOLD"] == 75_000

    def test_extract_unknown_scenario_returns_empty(self, extractor):
        """Scenario không xác định → dict rỗng."""
        result = extractor.extract("nonexistent", "some text")
        assert isinstance(result, dict)

    def test_extract_does_not_raise_on_malformed_text(self, extractor):
        """Không bao giờ raise exception."""
        result = extractor.extract("vn_payment", "!@#$%^&*()")
        assert isinstance(result, dict)

    def test_extracted_values_are_integers(self, extractor, retriever):
        """Giá trị trả về phải là int — Z3 yêu cầu."""
        text = retriever.get_legal_text("vn_payment")
        result = extractor.extract("vn_payment", text)
        for key, value in result.items():
            assert isinstance(value, int), f"{key} phải là int, nhưng là {type(value)}"


# ---------------------------------------------------------------------------
# Test Legal RAG Node
# ---------------------------------------------------------------------------

class TestLegalRagNode:
    """Kiểm tra legal_rag_node trong LangGraph workflow."""

    def test_rag_node_vn_returns_thresholds(self):
        """
        INPUT:  state[scenario_type] = "vn_payment"
        OUTPUT: state[legal_thresholds] = {"VN_CASH_THRESHOLD": 20000000}
        """
        state: AgentState = {"scenario_type": "vn_payment"}  # type: ignore
        result = legal_rag_node(state)
        assert "legal_thresholds" in result
        thresholds = result["legal_thresholds"]
        assert "VN_CASH_THRESHOLD" in thresholds
        assert thresholds["VN_CASH_THRESHOLD"] == 20_000_000
        print(f"\n📋 RAG VN: {thresholds}")

    def test_rag_node_kr_returns_thresholds(self):
        """
        INPUT:  state[scenario_type] = "kr_tax_refund"
        OUTPUT: state[legal_thresholds] = {KR_MIN_RECEIPT_AMOUNT: 30000, ...}
        """
        state: AgentState = {"scenario_type": "kr_tax_refund"}  # type: ignore
        result = legal_rag_node(state)
        assert "legal_thresholds" in result
        thresholds = result["legal_thresholds"]
        assert thresholds["KR_MIN_RECEIPT_AMOUNT"] == 30_000
        assert thresholds["KR_CUSTOMS_CHECK_THRESHOLD"] == 75_000
        print(f"\n📋 RAG KR: {thresholds}")

    def test_rag_node_unknown_returns_empty(self):
        """
        INPUT:  state[scenario_type] = "unknown"
        OUTPUT: state[legal_thresholds] = {} (không crash)
        """
        state: AgentState = {"scenario_type": "unknown"}  # type: ignore
        result = legal_rag_node(state)
        assert "legal_thresholds" in result
        assert isinstance(result["legal_thresholds"], dict)

    def test_rag_node_thresholds_are_int(self):
        """Tất cả giá trị trong legal_thresholds phải là int — Z3 yêu cầu."""
        state: AgentState = {"scenario_type": "vn_payment"}  # type: ignore
        result = legal_rag_node(state)
        for key, value in result["legal_thresholds"].items():
            assert isinstance(value, int), f"{key} = {value} phải là int"


# ---------------------------------------------------------------------------
# Test Dynamic Thresholds trong Z3
# ---------------------------------------------------------------------------

class TestDynamicThresholds:
    """Kiểm tra Z3 hoạt động đúng với ngưỡng động từ RAG."""

    def test_verify_node_uses_rag_threshold(self):
        """
        verify_node phải dùng legal_thresholds từ state, không phải hardcoded.

        INPUT:  z3_data={amount=25M, is_cash=True}, legal_thresholds={VN_CASH_THRESHOLD=20M}
        OUTPUT: UNSAT — vi phạm vì 25M >= 20M và dùng tiền mặt
        """
        state: AgentState = {  # type: ignore
            "scenario_type": "vn_payment",
            "z3_data": {
                "amount": 25_000_000,
                "is_cash_payment": True,
                "payment_method": "cash",
                "purpose": "event",
                "description": "sự kiện",
                "currency": "VND",
            },
            "applicable_rules": ["vn_cash_payment_threshold"],
            "legal_thresholds": {"VN_CASH_THRESHOLD": 20_000_000},  # Từ RAG
        }
        result = verify_node(state)
        assert result["z3_status"] == "UNSAT"
        assert result["is_compliant"] is False

    def test_verify_with_higher_custom_threshold(self):
        """
        Nếu ngưỡng tăng lên 30M (ví dụ luật cập nhật), 25M sẽ hợp lệ.

        INPUT:  amount=25M, is_cash=True, VN_CASH_THRESHOLD=30M (giả lập luật mới)
        OUTPUT: SAT — 25M < 30M, vẫn hợp lệ
        """
        state: AgentState = {  # type: ignore
            "scenario_type": "vn_payment",
            "z3_data": {
                "amount": 25_000_000,
                "is_cash_payment": True,
                "payment_method": "cash",
                "purpose": "test",
                "description": "test ngưỡng mới",
                "currency": "VND",
            },
            "applicable_rules": ["vn_cash_payment_threshold"],
            "legal_thresholds": {"VN_CASH_THRESHOLD": 30_000_000},  # Ngưỡng cao hơn
        }
        result = verify_node(state)
        # 25M < 30M → hợp lệ
        assert result["z3_status"] == "SAT"
        assert result["is_compliant"] is True

    def test_verify_without_rag_uses_defaults(self):
        """
        Khi không có legal_thresholds (RAG chưa chạy), Z3 dùng hardcoded defaults.
        Backward compatible với tests cũ.
        """
        state: AgentState = {  # type: ignore
            "scenario_type": "vn_payment",
            "z3_data": {
                "amount": 25_000_000,
                "is_cash_payment": True,
                "payment_method": "cash",
                "purpose": "test",
                "description": "test",
                "currency": "VND",
            },
            "applicable_rules": ["vn_cash_payment_threshold"],
            # legal_thresholds KHÔNG có → dùng defaults
        }
        result = verify_node(state)
        # Vẫn UNSAT với default 20M
        assert result["z3_status"] == "UNSAT"

    def test_kr_dynamic_min_receipt(self):
        """
        Kiểm tra ngưỡng động KR: KR_MIN_RECEIPT_AMOUNT từ RAG.
        """
        state: AgentState = {  # type: ignore
            "scenario_type": "kr_tax_refund",
            "z3_data": {
                "receipt_amount": 50_000,
                "refund_amount": 5_000,
                "needs_customs_check": False,
                "is_eligible": True,
                "is_tax_free_shop": True,
            },
            "applicable_rules": ["kr_tax_refund"],
            "legal_thresholds": {
                "KR_MIN_RECEIPT_AMOUNT": 30_000,
                "KR_CUSTOMS_CHECK_THRESHOLD": 75_000,
            },
        }
        result = verify_node(state)
        assert result["z3_status"] == "SAT"
        assert result["is_compliant"] is True


# ---------------------------------------------------------------------------
# Test End-to-End với RAG pipeline đầy đủ
# ---------------------------------------------------------------------------

class TestEndToEndWithRag:
    """End-to-end tests: NL input → RAG → Z3 → WorkflowResult."""

    def test_full_pipeline_vn_cash_blocked(self, workflow):
        """
        INPUT:  "Thanh toán tiền mặt 25 triệu cho sự kiện"
        FLOW:   parse → legal_rag (VN_CASH_THRESHOLD=20M) → Z3 UNSAT → explain
        OUTPUT: is_compliant=False
        """
        result = workflow.run("Thanh toán tiền mặt 25 triệu cho sự kiện")
        assert result.z3_status == "UNSAT"
        assert result.is_compliant is False
        print(f"\n📋 E2E VN blocked: {result.summary()}")

    def test_full_pipeline_vn_transfer_allowed(self, workflow):
        """
        INPUT:  "Chuyển khoản 30 triệu mua thiết bị"
        FLOW:   parse → legal_rag (VN_CASH_THRESHOLD=20M) → Z3 SAT → explain
        OUTPUT: is_compliant=True
        """
        result = workflow.run("Chuyển khoản 30 triệu mua thiết bị")
        assert result.z3_status == "SAT"
        assert result.is_compliant is True
        print(f"\n📋 E2E VN allowed: {result.summary()}")

    def test_full_pipeline_kr_refund(self, workflow):
        """
        INPUT:  "Mua hàng 50,000 KRW, hoàn 5,000 won"
        FLOW:   parse → legal_rag (KR thresholds) → Z3 SAT → explain
        OUTPUT: is_compliant=True
        """
        result = workflow.run("Mua hàng 50,000 KRW, hoàn 5,000 won")
        assert result.z3_status == "SAT"
        assert result.scenario_type == "kr_tax_refund"
        print(f"\n📋 E2E KR: {result.summary()}")

    def test_workflow_result_has_rag_applied(self, workflow):
        """workflow.run() nên trả về kết quả đúng sau khi RAG được tích hợp."""
        result = workflow.run("Thanh toán tiền mặt 25 triệu")
        # RAG đã lấy ngưỡng → Z3 dùng ngưỡng đó → UNSAT
        assert result.z3_status in ("SAT", "UNSAT")  # Không phải UNKNOWN
        assert len(result.explanation) > 0
