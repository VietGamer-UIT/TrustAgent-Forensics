"""
TrustAgent.Forensics — Public API cho LangGraph Workflow (Phase 3)

TrustAgentWorkflow là điểm vào chính của toàn bộ hệ thống.
Người dùng chỉ cần gọi .run(câu_yêu_cầu) và nhận kết quả đầy đủ.

Ví dụ sử dụng:
    workflow = TrustAgentWorkflow()
    result = workflow.run("Thanh toán tiền mặt 25 triệu cho sự kiện")
    print(result.is_compliant)    # False
    print(result.explanation)     # "❌ Giao dịch bị từ chối..."
    print(result.z3_status)       # "UNSAT"
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from src.agents.graph import build_graph
from src.agents.state import AgentState

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """
    Kết quả cuối cùng sau khi chạy toàn bộ workflow.

    Đây là object người dùng nhận được từ TrustAgentWorkflow.run().
    Chứa đầy đủ thông tin để hiển thị, lưu audit trail, hoặc debug.
    """

    # Input gốc
    user_input: str = ""

    # Kết quả parse (Phase 2)
    scenario_type: str = "UNKNOWN"         # "VN_PAYMENT" | "KR_TAX_REFUND" | "UNKNOWN"
    parse_confidence: float = 0.0          # 0.0 - 1.0

    # Kết quả Z3 (Phase 1)
    z3_status: str = "UNKNOWN"             # "SAT" | "UNSAT" | "UNKNOWN"
    is_compliant: bool = False
    violations: list[dict] = field(default_factory=list)
    verify_time_ms: float = 0.0

    # Giải thích thân thiện
    explanation: str = ""

    # Thông tin debug
    error: str | None = None
    total_duration_ms: float = 0.0

    # Data trung gian (để debug)
    z3_data: dict = field(default_factory=dict)
    applicable_rules: list[str] = field(default_factory=list)

    @property
    def is_blocked(self) -> bool:
        """True nếu giao dịch bị chặn."""
        return not self.is_compliant

    @property
    def status_emoji(self) -> str:
        """Emoji tương ứng với kết quả."""
        if self.z3_status == "SAT":
            return "✅"
        elif self.z3_status == "UNSAT":
            return "❌"
        return "⚠️"

    def summary(self) -> str:
        """Tóm tắt ngắn gọn kết quả."""
        return (
            f"{self.status_emoji} [{self.z3_status}] "
            f"Scenario: {self.scenario_type} | "
            f"Tuân thủ: {'Có' if self.is_compliant else 'Không'} | "
            f"Thời gian: {self.total_duration_ms:.1f}ms"
        )

    def to_dict(self) -> dict:
        """Chuyển thành dict để lưu vào DB hoặc trả về API."""
        return {
            "user_input": self.user_input,
            "scenario_type": self.scenario_type,
            "parse_confidence": self.parse_confidence,
            "z3_status": self.z3_status,
            "is_compliant": self.is_compliant,
            "violations": self.violations,
            "verify_time_ms": self.verify_time_ms,
            "explanation": self.explanation,
            "error": self.error,
            "total_duration_ms": self.total_duration_ms,
        }


class TrustAgentWorkflow:
    """
    Public API cho toàn bộ TrustAgent pipeline.

    Nội bộ dùng LangGraph StateGraph (hoặc MockGraph nếu langgraph chưa cài)
    để điều phối: parse → verify → explain.

    Sử dụng:
        workflow = TrustAgentWorkflow()

        # Kiểm tra giao dịch VN
        result = workflow.run("Thanh toán tiền mặt 25 triệu cho sự kiện")
        print(result.summary())
        # ❌ [UNSAT] Scenario: VN_PAYMENT | Tuân thủ: Không | Thời gian: 5.2ms

        # Kiểm tra hoàn thuế KR
        result = workflow.run("Mua hàng 50,000 won, hoàn 5,000 KRW tại Incheon")
        print(result.summary())
        # ✅ [SAT] Scenario: KR_TAX_REFUND | Tuân thủ: Có | Thời gian: 3.1ms
    """

    def __init__(self) -> None:
        self._graph = build_graph()
        logger.info("TrustAgentWorkflow khởi tạo thành công")

    def run(self, user_input: str) -> WorkflowResult:
        """
        Chạy toàn bộ pipeline: NL Input → Parse → Verify → Explain.

        Args:
            user_input: Câu yêu cầu bằng tiếng Việt hoặc tiếng Anh

        Returns:
            WorkflowResult chứa đầy đủ thông tin kết quả

        Ví dụ Input/Output:
            Input:  "Thanh toán tiền mặt 25 triệu cho sự kiện"
            Output: WorkflowResult(
                user_input    = "Thanh toán tiền mặt 25 triệu cho sự kiện",
                scenario_type = "VN_PAYMENT",
                z3_status     = "UNSAT",
                is_compliant  = False,
                violations    = [{"rule_name": "vn_cash_payment_threshold", ...}],
                explanation   = "❌ Giao dịch bị từ chối...",
                verify_time_ms = 2.3,
                total_duration_ms = 5.7,
            )
        """
        t_start = time.perf_counter()
        logger.info(f"TrustAgentWorkflow.run() bắt đầu: '{user_input[:80]}'")

        # Khởi tạo state với input
        initial_state: AgentState = {  # type: ignore
            "user_input": user_input,
        }

        try:
            # Chạy graph
            final_state: AgentState = self._graph.invoke(initial_state)

            total_ms = (time.perf_counter() - t_start) * 1000

            result = WorkflowResult(
                user_input=user_input,
                scenario_type=final_state.get("scenario_type", "UNKNOWN"),
                parse_confidence=final_state.get("parse_confidence", 0.0),
                z3_status=final_state.get("z3_status", "UNKNOWN"),
                is_compliant=final_state.get("is_compliant", False),
                violations=final_state.get("violations", []),
                verify_time_ms=final_state.get("verify_time_ms", 0.0),
                explanation=final_state.get("explanation", ""),
                error=final_state.get("final_error"),
                total_duration_ms=total_ms,
                z3_data=final_state.get("z3_data", {}),
                applicable_rules=final_state.get("applicable_rules", []),
            )

            logger.info(f"TrustAgentWorkflow.run() xong: {result.summary()}")
            return result

        except Exception as e:
            total_ms = (time.perf_counter() - t_start) * 1000
            logger.error(f"TrustAgentWorkflow.run() lỗi nghiêm trọng: {e}")
            return WorkflowResult(
                user_input=user_input,
                z3_status="UNKNOWN",
                is_compliant=False,
                explanation=f"⚠️ Lỗi hệ thống: {e}",
                error=str(e),
                total_duration_ms=total_ms,
            )
