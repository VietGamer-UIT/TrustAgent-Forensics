"""
TrustAgent.Forensics — Trạng thái chia sẻ giữa các Agent Node (Phase 3)

AgentState là "ký ức" trung tâm của toàn bộ workflow LangGraph.
Mỗi node đọc từ state và trả về dict để cập nhật state.

Luồng:
    START → parse_node → verify_node → explain_node → END
"""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """
    Trạng thái chia sẻ giữa tất cả nodes trong LangGraph workflow.

    LangGraph tự động merge dict trả về từ mỗi node vào state này.
    Dùng total=False để các field đều optional (không cần khởi tạo đủ).

    Luồng cập nhật:
        parse_node  → ghi: user_input, scenario_type, z3_data, applicable_rules,
                           parse_confidence, parse_error, parsed_vn, parsed_kr
        verify_node → ghi: z3_status, is_compliant, violations, verify_time_ms, verify_error
        explain_node→ ghi: explanation, final_error
    """

    # --- Input ---
    user_input: str                      # Câu yêu cầu gốc của người dùng

    # --- Kết quả parse (Phase 2) ---
    scenario_type: str                   # "VN_PAYMENT" | "KR_TAX_REFUND" | "UNKNOWN"
    z3_data: dict[str, Any]             # Dict data đưa vào Z3 (từ ParseResult.to_z3_data())
    applicable_rules: list[str]          # Danh sách rule_names áp dụng
    parse_confidence: float              # Độ tin cậy của LLM (0.0 - 1.0)
    parse_error: str | None             # Lỗi nếu parse thất bại

    # Dữ liệu chi tiết đã parse (để explain_node dùng)
    parsed_vn: dict[str, Any] | None    # ParsedVNTransaction.model_dump() nếu VN
    parsed_kr: dict[str, Any] | None    # ParsedKRTaxRefund.model_dump() nếu KR

    # --- Kết quả verify Z3 (Phase 1) ---
    z3_status: str                       # "SAT" | "UNSAT" | "UNKNOWN"
    is_compliant: bool                   # True nếu SAT
    violations: list[dict[str, Any]]     # Danh sách vi phạm (từ RuleViolation.model_dump())
    verify_time_ms: float               # Thời gian Z3 kiểm tra (ms)
    verify_error: str | None            # Lỗi nếu verify thất bại

    # --- Kết quả explain ---
    explanation: str                     # Giải thích thân thiện cho user

    # --- Lỗi chung ---
    final_error: str | None             # Lỗi không mong muốn toàn cục
