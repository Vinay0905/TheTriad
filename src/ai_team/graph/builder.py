"""LangGraph StateGraph builder: bounded QA cycles behind a human approval gate."""

from typing import Literal

from langgraph.graph import END, START, StateGraph

from ai_team.graph.nodes.developer import developer_node
from ai_team.graph.nodes.human_gate import human_steering_gate_node
from ai_team.graph.nodes.manager import manager_final_report_node, manager_rfc_node
from ai_team.graph.nodes.preflight import preflight_gate_node
from ai_team.graph.nodes.qa_audit import qa_audit_node
from ai_team.graph.nodes.researcher import researcher_audit_node
from ai_team.graph.nodes.sandbox_exec import sandbox_execution_node
from ai_team.graph.nodes.tdd_contract import tdd_contract_node
from ai_team.graph.state import TriadCouncilState

MAX_QA_REPAIR_CYCLES = 2

GATE_NODE = "human_steering_gate_node"


def route_tdd(
    state: TriadCouncilState,
) -> Literal["developer_node", "manager_final_report_node"]:
    """Stop the run if no valid test contract exists.

    Without a contract there is nothing to implement against and nothing
    meaningful to approve, so the run ends rather than proceeding to produce an
    artifact no test constrains.
    """
    if state.get("tdd_status") == "INVALID":
        print("  [Router] No valid TDD contract. Ending run before implementation.")
        return "manager_final_report_node"
    return "developer_node"


def route_qa(state: TriadCouncilState) -> Literal["developer_node", "preflight_gate_node"]:
    """Bounded repair cycle between the developer and the auditor.

    An unavailable auditor is not a failing audit: there is no feedback to
    repair against, so the run advances to the gate carrying an explicit
    "QA unavailable" status rather than burning repair attempts.
    """
    if state.get("qa_skipped"):
        print("  [Router] Auditor unavailable. Advancing to the gate as UNAVAILABLE.")
        return "preflight_gate_node"

    attempts = state.get("repair_attempts", 0)
    if not state.get("qa_passed", False) and attempts < MAX_QA_REPAIR_CYCLES:
        print(f"  [Router] QA failed. Repair attempt {attempts}/{MAX_QA_REPAIR_CYCLES}.")
        return "developer_node"

    return "preflight_gate_node"


def route_gate(
    state: TriadCouncilState,
) -> Literal["sandbox_execution_node", "manager_rfc_node", "manager_final_report_node"]:
    """Route on the operator's decision, defaulting to the no-execution path."""
    status = state.get("approval_status")
    if status == "APPROVED":
        return "sandbox_execution_node"
    if status == "STEERED":
        return "manager_rfc_node"
    # Anything else, including a missing status, must not reach the sandbox.
    return "manager_final_report_node"


def build_triad_graph(checkpointer=None):
    """Compile the council graph.

    A checkpointer is required for the human gate to be resumable, but is
    optional here so tests can compile the topology on its own.
    """
    workflow = StateGraph(TriadCouncilState)

    workflow.add_node("manager_rfc_node", manager_rfc_node)
    workflow.add_node("researcher_audit_node", researcher_audit_node)
    workflow.add_node("tdd_contract_node", tdd_contract_node)
    workflow.add_node("developer_node", developer_node)
    workflow.add_node("qa_audit_node", qa_audit_node)
    workflow.add_node("preflight_gate_node", preflight_gate_node)
    workflow.add_node(GATE_NODE, human_steering_gate_node)
    workflow.add_node("sandbox_execution_node", sandbox_execution_node)
    workflow.add_node("manager_final_report_node", manager_final_report_node)

    workflow.add_edge(START, "manager_rfc_node")
    workflow.add_edge("manager_rfc_node", "researcher_audit_node")
    workflow.add_edge("researcher_audit_node", "tdd_contract_node")

    workflow.add_conditional_edges(
        "tdd_contract_node",
        route_tdd,
        {
            "developer_node": "developer_node",
            "manager_final_report_node": "manager_final_report_node",
        },
    )

    workflow.add_edge("developer_node", "qa_audit_node")

    workflow.add_conditional_edges(
        "qa_audit_node",
        route_qa,
        {
            "developer_node": "developer_node",
            "preflight_gate_node": "preflight_gate_node",
        },
    )

    workflow.add_edge("preflight_gate_node", GATE_NODE)

    workflow.add_conditional_edges(
        GATE_NODE,
        route_gate,
        {
            "sandbox_execution_node": "sandbox_execution_node",
            "manager_rfc_node": "manager_rfc_node",
            "manager_final_report_node": "manager_final_report_node",
        },
    )

    workflow.add_edge("sandbox_execution_node", "manager_final_report_node")
    workflow.add_edge("manager_final_report_node", END)

    return workflow.compile(checkpointer=checkpointer)
