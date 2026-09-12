"""Conditional routing functions for the TriadCouncil LangGraph StateGraph."""

from ai_team.graph.state import TriadCouncilState


def route_human_gate(state: TriadCouncilState) -> str:
    """Route according to the operator's decision at the Human Steering Gate."""
    status = state.get("approval_status", "ABORTED")

    if status == "APPROVED":
        return "sandbox_execution_node"
    elif status == "STEERED":
        return "manager_rfc_node"
    return "clean_abort_node"


def route_post_execution(state: TriadCouncilState) -> str:
    """
    Evaluate runtime evidence and apply circuit breakers:
    1. Tests passed (exit code 0) -> Final Report.
    2. Local syntax/test failure (attempts < 3) -> Senior Micro-Repair.
    3. Structural/Library blocker (macro < 1) -> Macro Escalation back to Council.
    4. Otherwise -> Forensic Incident Report.
    """
    res = state.get("sandbox_result") or {}
    exit_code = res.get("exit_code", 1)

    # 1. Success path
    if exit_code == 0:
        return "manager_final_report_node"

    stderr = res.get("stderr", "")
    micro_count = state.get("micro_repair_count", 0)
    macro_count = state.get("macro_replan_count", 0)

    # Classify failure category
    is_arch_blocker = any(
        marker in stderr
        for marker in [
            "ModuleNotFoundError",
            "ImportError",
            "EnvironmentError",
            "SystemExit",
            "OSError",
            "PermissionError",
        ]
    )

    if not is_arch_blocker and micro_count < 3:
        # Check monotonic test failure invariant: F_t <= F_{t-1}
        current_failures = res.get("failing_tests_count", 999)
        previous_failures = state.get("last_failing_tests_count", 999)

        if current_failures > previous_failures and micro_count > 0:
            # Regression detected -> Abort micro-repair loop to avoid thrashing
            return "macro_escalation_node"

        return "senior_micro_repair_node"

    elif is_arch_blocker and macro_count < 1:
        return "macro_escalation_node"

    return "forensic_escalation_node"
