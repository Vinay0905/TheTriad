"""LangGraph StateGraph builder with bounded iterative QA cycles and Human Steering Gate."""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from ai_team.graph.state import TriadCouncilState
from ai_team.graph.nodes.manager import manager_rfc_node, manager_final_report_node
from ai_team.graph.nodes.researcher import researcher_audit_node
from ai_team.graph.nodes.tdd_contract import tdd_contract_node
from ai_team.graph.nodes.developer import developer_node
from ai_team.graph.nodes.qa_audit import qa_audit_node
from ai_team.graph.nodes.preflight import preflight_gate_node
from ai_team.graph.nodes.human_gate import human_steering_gate_node
from ai_team.graph.nodes.sandbox_exec import sandbox_execution_node

MAX_QA_REPAIR_CYCLES = 2


def route_qa(state: TriadCouncilState) -> Literal["developer_node", "preflight_gate_node"]:
    """
    Bounded Iterative QA Cycle:
    If Maya (QA) fails the code and cycle budget (<2 attempts) is not exhausted,
    route back to Alex (Developer) with Maya's feedback.
    Otherwise, advance to the Preflight Packaging & Human Gate.
    """
    qa_passed = state.get("qa_passed", True)
    attempts = state.get("repair_attempts", 0)

    if not qa_passed and attempts < MAX_QA_REPAIR_CYCLES:
        print(f"  ↻ [QA Loop] Routing back to Developer for repair (Attempt {attempts}/{MAX_QA_REPAIR_CYCLES})...")
        return "developer_node"

    return "preflight_gate_node"


def route_gate(state: TriadCouncilState) -> Literal["sandbox_execution_node", "manager_rfc_node", "manager_final_report_node"]:
    """Human Steering Gate routing based on operator decision."""
    status = state.get("approval_status", "ABORTED")
    if status == "APPROVED":
        return "sandbox_execution_node"
    elif status == "STEERED":
        return "manager_rfc_node"
    else:
        return "manager_final_report_node"


def build_triad_graph(checkpointer=None):
    """
    Construct, wire, and compile the bounded TriadCouncil LangGraph StateGraph:
    Manager -> Researcher -> TDD -> [Developer <-> QA (max 2)] -> Preflight -> Human Gate -> Sandbox -> Final Report
    """
    workflow = StateGraph(TriadCouncilState)

    # 1. Register Core Nodes
    workflow.add_node("manager_rfc_node", manager_rfc_node)
    workflow.add_node("researcher_audit_node", researcher_audit_node)
    workflow.add_node("tdd_contract_node", tdd_contract_node)
    workflow.add_node("developer_node", developer_node)
    workflow.add_node("qa_audit_node", qa_audit_node)
    workflow.add_node("preflight_gate_node", preflight_gate_node)
    workflow.add_node("human_steering_gate_node", human_steering_gate_node)
    workflow.add_node("sandbox_execution_node", sandbox_execution_node)
    workflow.add_node("manager_final_report_node", manager_final_report_node)

    # 2. Linear Formulation Edges
    workflow.add_edge(START, "manager_rfc_node")
    workflow.add_edge("manager_rfc_node", "researcher_audit_node")
    workflow.add_edge("researcher_audit_node", "tdd_contract_node")
    workflow.add_edge("tdd_contract_node", "developer_node")
    workflow.add_edge("developer_node", "qa_audit_node")

    # 3. Bounded Iterative QA Cycle
    workflow.add_conditional_edges(
        "qa_audit_node",
        route_qa,
        {
            "developer_node": "developer_node",
            "preflight_gate_node": "preflight_gate_node",
        },
    )

    workflow.add_edge("preflight_gate_node", "human_steering_gate_node")

    # 4. Human Approval Gate
    workflow.add_conditional_edges(
        "human_steering_gate_node",
        route_gate,
        {
            "sandbox_execution_node": "sandbox_execution_node",
            "manager_rfc_node": "manager_rfc_node",
            "manager_final_report_node": "manager_final_report_node",
        },
    )

    # 5. Terminal Execution Edges
    workflow.add_edge("sandbox_execution_node", "manager_final_report_node")
    workflow.add_edge("manager_final_report_node", END)

    return workflow.compile(checkpointer=checkpointer)
