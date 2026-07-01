"""
TrustAgent.Forensics — Tests cho Phase 3: LangGraph Multi-Agent Workflow

Kiểm tra toàn bộ workflow từ NL input đến WorkflowResult cuối cùng.
Không cần langgraph cài sẵn — dùng MockGraph tự động.
Không cần Gemini API key — dùng MockSemanticParser.

Cấu trúc test:
    TestAgentState      — kiểm tra cấu trúc state
    TestParseNode       — kiểm tra node parsing
    TestVerifyNode      — kiểm tra node Z3 verify
    TestExplainNode     — kiểm tra node giải thích
    TestRouting         — kiểm tra conditional routing
    TestWorkflow        — end-to-end workflow tests
    TestWorkflowResult  — kiểm tra WorkflowResult helpers
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agents.state import AgentState
from src.agents.nodes import parse_node, verify_node, explain_node, route_after_parse
from src.agents.workflow import TrustAgentWorkflow, WorkflowResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def workflow() -> TrustAgentWorkflow:
    return TrustAgentWorkflow()


@pytest.fixture
def vn_cash_state() -> AgentState:
    """State sau khi đã parse giao dịch tiền mặt VN 25M."""
    return {
        "user_input": "Thanh toán tiền mặt 25 triệu cho sự kiện",
        "scenario_type": "vn_payment",  # ScenarioType.VN_PAYMENT.value
        "z3_data": {"amount": 25_000_000, "is_cash_payment": True,
                    "payment_method": "cash", "purpose": "event",
                    "description": "sự kiện", "currency": "VND"},
        "applicable_rules": ["vn_cash_payment_threshold"],
        "parse_confidence": 0.95,
        "parse_error": None,
        "parsed_vn": {"amount": 25_000_000, "is_cash_payment": True},
        "parsed_kr": None,
    }


@pytest.fixture
def vn_transfer_state() -> AgentState:
    """State sau khi đã parse giao dịch chuyển khoản VN 30M."""
    return {
        "user_input": "Chuyển khoản 30 triệu mua thiết bị",
        "scenario_type": "vn_payment",  # ScenarioType.VN_PAYMENT.value
        "z3_data": {"amount": 30_000_000, "is_cash_payment": False,
                    "payment_method": "bank_transfer", "purpose": "equipment",
                    "description": "thiết bị", "currency": "VND"},
        "applicable_rules": ["vn_cash_payment_threshold"],
        "parse_confidence": 0.95,
        "parse_error": None,
        "parsed_vn": None,
        "parsed_kr": None,
    }


@pytest.fixture
def kr_small_state() -> AgentState:
    """State sau khi đã parse hoàn thuế KR nhỏ."""
    return {
        "user_input": "Mua hàng 50,000 KRW, hoàn 5,000 won",
        "scenario_type": "kr_tax_refund",  # ScenarioType.KR_TAX_REFUND.value
        "z3_data": {"receipt_amount": 50_000, "refund_amount": 5_000,
                    "needs_customs_check": False, "is_eligible": True,
                    "is_tax_free_shop": True},
        "applicable_rules": ["kr_tax_refund"],
        "parse_confidence": 0.90,
        "parse_error": None,
        "parsed_vn": None,
        "parsed_kr": {"receipt_amount": 50_000, "refund_amount": 5_000},
    }


@pytest.fixture
def unknown_state() -> AgentState:
    """State cho input không xác định."""
    return {
        "user_input": "Hôm nay thời tiết đẹp quá",
        "scenario_type": "unknown",  # ScenarioType.UNKNOWN.value
        "z3_data": {},
        "applicable_rules": [],
        "parse_confidence": 0.0,
        "parse_error": "Không nhận diện được loại kịch bản",
        "parsed_vn": None,
        "parsed_kr": None,
    }


# ---------------------------------------------------------------------------
# Test AgentState structure
# ---------------------------------------------------------------------------

class TestAgentState:
    """Kiểm tra cấu trúc AgentState."""

    def test_state_is_typed_dict(self):
        state: AgentState = {"user_input": "test"}  # type: ignore
        assert state["user_input"] == "test"

    def test_state_supports_all_keys(self, vn_cash_state):
        assert "user_input" in vn_cash_state
        assert "scenario_type" in vn_cash_state
        assert "z3_data" in vn_cash_state
        assert "applicable_rules" in vn_cash_state


# ---------------------------------------------------------------------------
# Test parse_node
# ---------------------------------------------------------------------------

class TestParseNode:
    """Kiểm tra parse_node hoạt động đúng."""

    def test_parse_vn_cash(self):
        state: AgentState = {"user_input": "Thanh toán tiền mặt 25 triệu"}  # type: ignore
        result = parse_node(state)
        assert result["scenario_type"] == "vn_payment"  # ScenarioType.VN_PAYMENT.value
        assert result["z3_data"]["amount"] == 25_000_000
        assert result["z3_data"]["is_cash_payment"] is True
        assert "vn_cash_payment_threshold" in result["applicable_rules"]

    def test_parse_vn_transfer(self):
        state: AgentState = {"user_input": "Chuyển khoản 30 triệu mua thiết bị"}  # type: ignore
        result = parse_node(state)
        assert result["scenario_type"] == "vn_payment"
        assert result["z3_data"]["is_cash_payment"] is False

    def test_parse_kr_refund(self):
        state: AgentState = {"user_input": "Mua hàng 50,000 KRW tại Incheon"}  # type: ignore
        result = parse_node(state)
        assert result["scenario_type"] == "kr_tax_refund"  # ScenarioType.KR_TAX_REFUND.value
        assert "kr_tax_refund" in result["applicable_rules"]

    def test_parse_unknown(self):
        state: AgentState = {"user_input": "Hôm nay thời tiết đẹp"}  # type: ignore
        result = parse_node(state)
        assert result["scenario_type"] == "unknown"  # ScenarioType.UNKNOWN.value
        assert result["z3_data"] == {}

    def test_parse_empty_input(self):
        state: AgentState = {"user_input": ""}  # type: ignore
        result = parse_node(state)
        assert result["scenario_type"] == "unknown"
        assert result["parse_error"] is not None

    def test_parse_returns_confidence(self):
        state: AgentState = {"user_input": "Thanh toán tiền mặt 25 triệu"}  # type: ignore
        result = parse_node(state)
        assert "parse_confidence" in result
        assert 0.0 <= result["parse_confidence"] <= 1.0


# ---------------------------------------------------------------------------
# Test verify_node
# ---------------------------------------------------------------------------

class TestVerifyNode:
    """Kiểm tra verify_node gọi Z3 đúng cách."""

    def test_verify_vn_cash_unsat(self, vn_cash_state):
        result = verify_node(vn_cash_state)
        assert result["z3_status"] == "UNSAT"
        assert result["is_compliant"] is False
        assert len(result["violations"]) > 0

    def test_verify_vn_transfer_sat(self, vn_transfer_state):
        result = verify_node(vn_transfer_state)
        assert result["z3_status"] == "SAT"
        assert result["is_compliant"] is True
        assert result["violations"] == []

    def test_verify_kr_small_sat(self, kr_small_state):
        result = verify_node(kr_small_state)
        assert result["z3_status"] == "SAT"
        assert result["is_compliant"] is True

    def test_verify_empty_data(self):
        state: AgentState = {  # type: ignore
            "z3_data": {},
            "applicable_rules": [],
            "scenario_type": "UNKNOWN",
        }
        result = verify_node(state)
        assert result["z3_status"] == "UNKNOWN"

    def test_verify_returns_time(self, vn_cash_state):
        result = verify_node(vn_cash_state)
        assert "verify_time_ms" in result
        assert result["verify_time_ms"] >= 0

    def test_violations_have_correct_keys(self, vn_cash_state):
        result = verify_node(vn_cash_state)
        if result["violations"]:
            v = result["violations"][0]
            assert "rule_name" in v
            assert "violation_detail" in v


# ---------------------------------------------------------------------------
# Test explain_node
# ---------------------------------------------------------------------------

class TestExplainNode:
    """Kiểm tra explain_node tạo giải thích đúng."""

    def test_explain_unsat_has_blocked_indicator(self, vn_cash_state):
        # Thêm verify results vào state
        state = dict(vn_cash_state)
        state.update({
            "z3_status": "UNSAT",
            "is_compliant": False,
            "violations": [{"rule_name": "vn_cash_payment_threshold",
                           "violation_detail": "Số tiền vi phạm quy định",
                           "legal_reference": "Thông tư 96/2015"}],
            "verify_error": None,
        })
        result = explain_node(state)  # type: ignore
        assert "explanation" in result
        assert len(result["explanation"]) > 0
        # Giải thích phải có chỉ báo blocked
        assert "❌" in result["explanation"] or "từ chối" in result["explanation"].lower()

    def test_explain_sat_has_approved_indicator(self, vn_transfer_state):
        state = dict(vn_transfer_state)
        state.update({
            "z3_status": "SAT",
            "is_compliant": True,
            "violations": [],
            "verify_error": None,
        })
        result = explain_node(state)  # type: ignore
        assert "explanation" in result
        assert "✅" in result["explanation"] or "hợp lệ" in result["explanation"].lower() or "phê duyệt" in result["explanation"].lower()

    def test_explain_unknown_scenario(self, unknown_state):
        state = dict(unknown_state)
        state.update({"z3_status": "UNKNOWN", "is_compliant": False,
                      "violations": [], "verify_error": None})
        result = explain_node(state)  # type: ignore
        assert "explanation" in result
        assert len(result["explanation"]) > 10


# ---------------------------------------------------------------------------
# Test Routing
# ---------------------------------------------------------------------------

class TestRouting:
    """Kiểm tra conditional routing trong graph."""

    def test_route_vn_goes_to_verify(self, vn_cash_state):
        # Phase 3.5: route trả về 'rag' (legal_rag_node) thay vì 'verify' trực tiếp
        state = dict(vn_cash_state)
        state["scenario_type"] = "vn_payment"  # dùng enum value thực tế
        next_step = route_after_parse(state)  # type: ignore
        assert next_step == "rag"  # ← Phase 3.5: đi qua RAG trước

    def test_route_kr_goes_to_verify(self, kr_small_state):
        state = dict(kr_small_state)
        state["scenario_type"] = "kr_tax_refund"
        next_step = route_after_parse(state)  # type: ignore
        assert next_step == "rag"  # ← Phase 3.5: đi qua RAG trước

    def test_route_unknown_skips_verify(self, unknown_state):
        state = dict(unknown_state)
        state["scenario_type"] = "unknown"  # ScenarioType.UNKNOWN.value
        next_step = route_after_parse(state)  # type: ignore
        assert next_step == "explain"


# ---------------------------------------------------------------------------
# Test End-to-End Workflow
# ---------------------------------------------------------------------------

class TestWorkflow:
    """End-to-end workflow tests — NL input → WorkflowResult."""

    def test_vn_cash_25m_blocked(self, workflow):
        """
        INPUT:  "Thanh toán tiền mặt 25 triệu cho sự kiện"
        OUTPUT: z3_status=UNSAT, is_compliant=False
        """
        result = workflow.run("Thanh toán tiền mặt 25 triệu cho sự kiện")
        assert result.z3_status == "UNSAT"
        assert result.is_compliant is False
        assert result.is_blocked is True
        assert len(result.violations) > 0
        print(f"\n📋 Input: 'Thanh toán tiền mặt 25 triệu cho sự kiện'")
        print(f"   Scenario: {result.scenario_type}")
        print(f"   Z3 Status: {result.z3_status}")
        print(f"   Giải thích: {result.explanation[:80]}...")

    def test_vn_transfer_30m_allowed(self, workflow):
        """
        INPUT:  "Chuyển khoản 30 triệu mua thiết bị văn phòng"
        OUTPUT: z3_status=SAT, is_compliant=True
        """
        result = workflow.run("Chuyển khoản 30 triệu mua thiết bị văn phòng")
        assert result.z3_status == "SAT"
        assert result.is_compliant is True
        assert result.is_blocked is False
        print(f"\n📋 Input: 'Chuyển khoản 30 triệu mua thiết bị'")
        print(f"   Giải thích: {result.explanation[:80]}...")

    def test_vn_cash_15m_allowed(self, workflow):
        """
        INPUT:  "Chi 15tr tiền mặt văn phòng phẩm"
        OUTPUT: z3_status=SAT (dưới ngưỡng 20M)
        """
        result = workflow.run("Chi 15tr tiền mặt văn phòng phẩm")
        assert result.z3_status == "SAT"
        assert result.is_compliant is True

    def test_kr_small_refund_allowed(self, workflow):
        """
        INPUT:  "Mua hàng 50,000 KRW, hoàn 5,000 won"
        OUTPUT: z3_status=SAT
        """
        result = workflow.run("Mua hàng 50,000 KRW, hoàn 5,000 won")
        assert result.z3_status == "SAT"
        assert result.scenario_type == "kr_tax_refund"  # ScenarioType.KR_TAX_REFUND.value

    def test_unknown_input_handled_gracefully(self, workflow):
        """
        INPUT:  "Hôm nay thời tiết đẹp quá"
        OUTPUT: scenario=UNKNOWN, explanation có gợi ý
        """
        result = workflow.run("Hôm nay thời tiết đẹp quá")
        assert result.scenario_type == "unknown"  # ScenarioType.UNKNOWN.value
        assert len(result.explanation) > 0
        # Không crash — xử lý gracefully
        assert result.error is None or len(result.explanation) > 10

    def test_result_has_duration(self, workflow):
        result = workflow.run("Thanh toán tiền mặt 25 triệu")
        assert result.total_duration_ms > 0

    def test_result_has_explanation(self, workflow):
        result = workflow.run("Thanh toán tiền mặt 25 triệu")
        assert isinstance(result.explanation, str)
        assert len(result.explanation) > 0


# ---------------------------------------------------------------------------
# Test WorkflowResult helpers
# ---------------------------------------------------------------------------

class TestWorkflowResult:
    """Kiểm tra các helper methods của WorkflowResult."""

    def test_is_blocked_property(self):
        r = WorkflowResult(is_compliant=False)
        assert r.is_blocked is True
        r2 = WorkflowResult(is_compliant=True)
        assert r2.is_blocked is False

    def test_status_emoji_sat(self):
        r = WorkflowResult(z3_status="SAT")
        assert r.status_emoji == "✅"

    def test_status_emoji_unsat(self):
        r = WorkflowResult(z3_status="UNSAT")
        assert r.status_emoji == "❌"

    def test_status_emoji_unknown(self):
        r = WorkflowResult(z3_status="UNKNOWN")
        assert r.status_emoji == "⚠️"

    def test_summary_returns_string(self):
        r = WorkflowResult(z3_status="SAT", scenario_type="VN_PAYMENT",
                           is_compliant=True, total_duration_ms=5.2)
        s = r.summary()
        assert isinstance(s, str)
        assert "SAT" in s

    def test_to_dict_has_required_keys(self):
        r = WorkflowResult(user_input="test", z3_status="SAT")
        d = r.to_dict()
        assert "user_input" in d
        assert "z3_status" in d
        assert "is_compliant" in d
        assert "explanation" in d
