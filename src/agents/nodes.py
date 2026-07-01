"""
TrustAgent.Forensics — Node Functions cho LangGraph Workflow (Phase 3)

Mỗi "node" là một bước trong workflow, nhận vào AgentState và trả về
dict để cập nhật state. LangGraph tự động merge dict vào state.

Các node:
    parse_node   — Gọi SemanticParser để hiểu câu yêu cầu
    verify_node  — Gọi TrustAgentSolver để kiểm chứng bằng Z3
    explain_node — Tạo câu trả lời thân thiện cho người dùng
    route_node   — Quyết định đi tiếp hay skip verify (nếu UNKNOWN)
"""

from __future__ import annotations

import logging
from typing import Any

from src.agents.state import AgentState
from src.semantic.parser import SemanticParser
from src.semantic.schemas import ScenarioType
from src.z3_engine.models import VerificationStatus
from src.z3_engine.solver import TrustAgentSolver
from src.z3_engine.rules.vn_tax_rule import VietnamCashPaymentRule
from src.z3_engine.rules.kr_refund_rule import KoreaTaxRefundRule

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton solver — đã đăng ký sẵn tất cả rules
# ---------------------------------------------------------------------------
_solver = TrustAgentSolver()
_solver.register_rule(VietnamCashPaymentRule())
_solver.register_rule(KoreaTaxRefundRule())


def _get_parser(api_key: str = "") -> SemanticParser:
    """Tạo parser từ config hoặc dùng Mock nếu không có API key."""
    try:
        return SemanticParser.from_config()
    except Exception:
        return SemanticParser(api_key=api_key)


# ---------------------------------------------------------------------------
# Node 1: parse_node — Semantic Parsing (Neural Layer)
# ---------------------------------------------------------------------------
def parse_node(state: AgentState) -> dict[str, Any]:
    """
    Bước 1: Phân tích câu yêu cầu bằng ngôn ngữ tự nhiên.

    Input  (từ state): user_input (str)
    Output (vào state): scenario_type, z3_data, applicable_rules,
                        parse_confidence, parse_error, parsed_vn, parsed_kr

    Ví dụ:
        Input:  "Thanh toán tiền mặt 25 triệu cho sự kiện"
        Output: scenario_type="VN_PAYMENT", z3_data={"amount": 25000000, ...}
    """
    user_input = state.get("user_input", "")
    logger.info(f"[parse_node] Bắt đầu parse: '{user_input[:60]}...'")

    if not user_input or not user_input.strip():
        return {
            "scenario_type": ScenarioType.UNKNOWN.value,
            "z3_data": {},
            "applicable_rules": [],
            "parse_confidence": 0.0,
            "parse_error": "Input rỗng hoặc chỉ có khoảng trắng",
            "parsed_vn": None,
            "parsed_kr": None,
        }

    try:
        parser = _get_parser()
        result = parser.parse(user_input)

        # Trích xuất thêm detail để explain_node dùng sau
        parsed_vn = result.vn_transaction.model_dump() if result.vn_transaction else None
        parsed_kr = result.kr_tax_refund.model_dump() if result.kr_tax_refund else None

        # Lấy confidence từ parsed data
        confidence = 0.0
        if result.vn_transaction:
            confidence = result.vn_transaction.confidence
        elif result.kr_tax_refund:
            confidence = result.kr_tax_refund.confidence

        logger.info(
            f"[parse_node] Kết quả: scenario={result.scenario_type.value}, "
            f"confidence={confidence:.2f}"
        )

        return {
            "scenario_type": result.scenario_type.value,
            "z3_data": result.to_z3_data(),
            "applicable_rules": result.get_applicable_rules(),
            "parse_confidence": confidence,
            "parse_error": result.parse_error,
            "parsed_vn": parsed_vn,
            "parsed_kr": parsed_kr,
        }

    except Exception as e:
        logger.error(f"[parse_node] Lỗi không mong muốn: {e}")
        return {
            "scenario_type": ScenarioType.UNKNOWN.value,
            "z3_data": {},
            "applicable_rules": [],
            "parse_confidence": 0.0,
            "parse_error": str(e),
            "parsed_vn": None,
            "parsed_kr": None,
        }


# ---------------------------------------------------------------------------
# Node 2: verify_node — Z3 Formal Verification (Symbolic Layer)
# ---------------------------------------------------------------------------
def verify_node(state: AgentState) -> dict[str, Any]:
    """
    Bước 2: Kiểm chứng dữ liệu bằng Z3 Theorem Prover.

    Input  (từ state): z3_data, applicable_rules
    Output (vào state): z3_status, is_compliant, violations, verify_time_ms, verify_error

    Ví dụ:
        Input:  z3_data={"amount": 25000000, "is_cash_payment": True}
        Output: z3_status="UNSAT", is_compliant=False, violations=[...]
    """
    z3_data = state.get("z3_data", {})
    applicable_rules = state.get("applicable_rules", [])
    scenario_type = state.get("scenario_type", "UNKNOWN")

    logger.info(
        f"[verify_node] Kiểm chứng scenario={scenario_type}, "
        f"rules={applicable_rules}, data_keys={list(z3_data.keys())}"
    )

    # Nếu không có data để verify → skip
    if not z3_data or not applicable_rules:
        return {
            "z3_status": VerificationStatus.UNKNOWN.value,
            "is_compliant": False,
            "violations": [],
            "verify_time_ms": 0.0,
            "verify_error": "Không có dữ liệu hoặc rule để kiểm chứng",
        }

    try:
        verify_result = _solver.verify(
            data=z3_data,
            rule_names=applicable_rules,
        )

        violations_dicts = [v.model_dump() for v in verify_result.violations]

        logger.info(
            f"[verify_node] Kết quả: status={verify_result.status.value}, "
            f"compliant={verify_result.is_compliant}, "
            f"time={verify_result.verification_time_ms:.2f}ms"
        )

        return {
            "z3_status": verify_result.status.value,
            "is_compliant": verify_result.is_compliant,
            "violations": violations_dicts,
            "verify_time_ms": verify_result.verification_time_ms,
            "verify_error": None,
        }

    except Exception as e:
        logger.error(f"[verify_node] Lỗi không mong muốn: {e}")
        return {
            "z3_status": VerificationStatus.UNKNOWN.value,
            "is_compliant": False,
            "violations": [],
            "verify_time_ms": 0.0,
            "verify_error": str(e),
        }


# ---------------------------------------------------------------------------
# Node 3: explain_node — Tạo phản hồi thân thiện cho người dùng
# ---------------------------------------------------------------------------
def explain_node(state: AgentState) -> dict[str, Any]:
    """
    Bước 3: Tạo câu giải thích thân thiện dựa trên kết quả Z3.

    Input  (từ state): user_input, z3_status, violations, scenario_type, parse_error
    Output (vào state): explanation, final_error

    Ví dụ:
        Input:  z3_status="UNSAT", violations=[{rule: "vn_cash_payment_threshold", ...}]
        Output: explanation="❌ Giao dịch bị từ chối. Số tiền 25,000,000 VNĐ..."
    """
    user_input = state.get("user_input", "")
    z3_status = state.get("z3_status", "UNKNOWN")
    violations = state.get("violations", [])
    scenario_type = state.get("scenario_type", "UNKNOWN")
    parse_error = state.get("parse_error")
    verify_error = state.get("verify_error")

    logger.info(f"[explain_node] Tạo giải thích: status={z3_status}")

    # Trường hợp lỗi nghiêm trọng — không parse được
    if scenario_type == ScenarioType.UNKNOWN.value:
        if parse_error:
            explanation = (
                f"⚠️ Xin lỗi, tôi không hiểu yêu cầu này.\n"
                f"Lý do: {parse_error}\n\n"
                f"Gợi ý: Hãy nêu rõ số tiền, phương thức thanh toán và mục đích.\n"
                f"Ví dụ: 'Thanh toán tiền mặt 25 triệu cho chi phí sự kiện'"
            )
        else:
            explanation = (
                "⚠️ Yêu cầu không thuộc lĩnh vực kiểm tra của hệ thống.\n"
                "Hệ thống hỗ trợ: thanh toán VNĐ (Việt Nam) và hoàn thuế KRW (Hàn Quốc)."
            )
        return {"explanation": explanation, "final_error": None}

    # Trường hợp lỗi Z3
    if verify_error:
        explanation = (
            f"⚠️ Có lỗi khi kiểm tra quy định. Chi tiết: {verify_error}"
        )
        return {"explanation": explanation, "final_error": verify_error}

    # Tạo giải thích dựa trên kết quả Z3
    try:
        parser = _get_parser()

        # Chuyển violations dict → objects tương tự để explain
        class _FakeViolation:
            def __init__(self, d: dict):
                self.violation_detail = d.get("violation_detail", "Vi phạm quy định")

        fake_violations = [_FakeViolation(v) for v in violations]
        explanation = parser.explain_result(user_input, z3_status, fake_violations)

        # Thêm thông tin chi tiết về vi phạm (nếu có)
        if violations and z3_status == "UNSAT":
            violation_details = "\n".join(
                f"  • [{v.get('rule_name', 'unknown')}] {v.get('violation_detail', '')}"
                for v in violations
            )
            explanation += f"\n\nChi tiết vi phạm:\n{violation_details}"

            legal_refs = list({v.get("legal_reference", "") for v in violations if v.get("legal_reference")})
            if legal_refs:
                explanation += f"\n\nCăn cứ pháp lý: {', '.join(legal_refs)}"

        return {"explanation": explanation, "final_error": None}

    except Exception as e:
        logger.error(f"[explain_node] Lỗi: {e}")
        # Fallback đơn giản
        if z3_status == "SAT":
            fallback = "✅ Giao dịch hợp lệ và được phê duyệt."
        elif z3_status == "UNSAT":
            fallback = f"❌ Giao dịch bị từ chối do vi phạm quy định. ({len(violations)} vi phạm)"
        else:
            fallback = "⚠️ Không thể xác định trạng thái giao dịch."
        return {"explanation": fallback, "final_error": str(e)}


# ---------------------------------------------------------------------------
# Route Function — quyết định đường đi trong graph
# ---------------------------------------------------------------------------
def route_after_parse(state: AgentState) -> str:
    """
    Sau parse_node, quyết định bước tiếp theo:
    - Nếu scenario UNKNOWN → nhảy thẳng sang explain_node (không cần verify)
    - Nếu scenario xác định → đi qua verify_node
    """
    scenario_type = state.get("scenario_type", "UNKNOWN")
    if scenario_type == ScenarioType.UNKNOWN.value:
        logger.info("[route] Scenario UNKNOWN → skip verify, đi thẳng explain")
        return "explain"
    logger.info(f"[route] Scenario={scenario_type} → đi qua verify")
    return "verify"
