"""
TrustAgent.Forensics — LangGraph Graph Builder (Phase 3)

Xây dựng và compile StateGraph cho workflow kiểm chứng AI.

Sơ đồ graph:
    START
      │
      ▼
    parse_node          ← Semantic parsing (Gemini/Mock)
      │
      ├─ [UNKNOWN] ───────────────────────┐
      │                                   │
      ▼                                   │
    verify_node         ← Z3 verification │
      │                                   │
      ▼                                   ▼
    explain_node        ← Friendly response generation
      │
      ▼
     END
"""

from __future__ import annotations

try:
    from langgraph.graph import StateGraph, END, START
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from src.agents.state import AgentState
from src.agents.nodes import parse_node, verify_node, explain_node, route_after_parse


def build_graph():
    """
    Tạo và compile LangGraph StateGraph cho TrustAgent workflow.

    Returns:
        CompiledGraph nếu langgraph đã cài, MockGraph nếu chưa cài.
    """
    if not LANGGRAPH_AVAILABLE:
        return _MockGraph()

    # Tạo graph với AgentState là schema
    graph = StateGraph(AgentState)

    # Thêm các nodes
    graph.add_node("parse", parse_node)
    graph.add_node("verify", verify_node)
    graph.add_node("explain", explain_node)

    # Thêm edges (luồng)
    graph.add_edge(START, "parse")

    # Conditional routing sau parse
    graph.add_conditional_edges(
        "parse",
        route_after_parse,
        {
            "verify": "verify",   # scenario xác định → verify
            "explain": "explain", # UNKNOWN → skip verify
        },
    )

    graph.add_edge("verify", "explain")
    graph.add_edge("explain", END)

    return graph.compile()


class _MockGraph:
    """
    Graph giả lập khi langgraph chưa được cài.
    Chạy các nodes tuần tự (không có state machine thực sự).
    Dùng cho dev/test khi chưa cài langgraph.
    """

    def invoke(self, initial_state: dict) -> AgentState:
        """Chạy workflow tuần tự: parse → route → (verify) → explain."""
        state: AgentState = dict(initial_state)  # type: ignore

        # Bước 1: Parse
        state.update(parse_node(state))

        # Bước 2: Route
        next_step = route_after_parse(state)

        # Bước 3: Verify (nếu có)
        if next_step == "verify":
            state.update(verify_node(state))

        # Bước 4: Explain
        state.update(explain_node(state))

        return state  # type: ignore
