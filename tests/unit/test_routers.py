"""Unit tests for LangGraph conditional edge routing and circuit breakers."""

from ai_team.graph.routers import route_human_gate, route_post_execution
from ai_team.graph.state import TriadCouncilState


def test_route_human_gate_decisions():
    assert route_human_gate({"approval_status": "APPROVED"}) == "sandbox_execution_node"
    assert route_human_gate({"approval_status": "STEERED"}) == "manager_rfc_node"
    assert route_human_gate({"approval_status": "ABORTED"}) == "clean_abort_node"
    assert route_human_gate({}) == "clean_abort_node"


def test_route_post_execution_success():
    state: TriadCouncilState = {
        "sandbox_result": {"exit_code": 0, "stdout": "All tests passed"}
    }
    assert route_post_execution(state) == "manager_final_report_node"


def test_route_post_execution_micro_repair_local_bug():
    state: TriadCouncilState = {
        "sandbox_result": {"exit_code": 1, "stderr": "AssertionError: expected 2 got 1"},
        "micro_repair_count": 0,
        "macro_replan_count": 0,
        "last_failing_tests_count": 1,
    }
    assert route_post_execution(state) == "senior_micro_repair_node"


def test_route_post_execution_architectural_blocker():
    state: TriadCouncilState = {
        "sandbox_result": {
            "exit_code": 1,
            "stderr": "ModuleNotFoundError: No module named 'missing_package'",
        },
        "micro_repair_count": 0,
        "macro_replan_count": 0,
    }
    assert route_post_execution(state) == "macro_escalation_node"


def test_route_post_execution_circuit_breaker_monotonic_failure():
    # If failures INCREASE during a repair attempt, regression detected -> escalate to macro
    state: TriadCouncilState = {
        "sandbox_result": {
            "exit_code": 1,
            "stderr": "AssertionError",
            "failing_tests_count": 3,
        },
        "micro_repair_count": 1,
        "macro_replan_count": 0,
        "last_failing_tests_count": 1,  # Previously only 1 failure, now 3
    }
    assert route_post_execution(state) == "macro_escalation_node"
