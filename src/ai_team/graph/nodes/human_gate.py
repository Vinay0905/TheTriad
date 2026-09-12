"""Human Steering Gate node using LangGraph native interrupt().

This is the security boundary of the whole system: everything upstream is text,
everything downstream can write files and run commands. The node therefore
fails closed. There is no code path here that approves without an explicit
operator token, and there is deliberately no flag to skip it.
"""

from importlib import import_module
from typing import Any, Dict, Tuple

from ai_team.graph.gate_decision import ABORTED, gate_state_update, parse_gate_decision
from ai_team.graph.state import TriadCouncilState


def _control_flow_exception_types() -> Tuple[type, ...]:
    """Collect the LangGraph exceptions that implement control flow, not failure.

    `interrupt()` suspends the graph by raising, so these must propagate. The
    set of exported names has moved between 0.x releases, hence the lookup.
    """
    names = (
        ("langgraph.errors", "GraphBubbleUp"),
        ("langgraph.errors", "GraphInterrupt"),
        ("langgraph.errors", "NodeInterrupt"),
        ("langgraph.errors", "ParentCommand"),
    )
    found = []
    for module_name, attr in names:
        try:
            candidate = getattr(import_module(module_name), attr)
        except (ImportError, AttributeError):
            continue
        if isinstance(candidate, type) and issubclass(candidate, BaseException):
            found.append(candidate)
    return tuple(found)


def _abort(reason: str) -> Dict[str, Any]:
    print(f"  [Gate] Failing closed: {reason}")
    return {
        "approval_status": ABORTED,
        "human_feedback": f"Aborted without operator approval: {reason}",
    }


def human_steering_gate_node(state: TriadCouncilState) -> Dict[str, Any]:
    """Suspend the graph before any filesystem write or command execution.

    Note on ordering: `interrupt()` re-runs this node from the top on resume,
    so this node performs no side effects at all. The gate UI event is emitted
    by whoever drives the graph (CLI or server) once `stream()` has halted.
    """
    bundle = state.get("execution_bundle") or {}

    try:
        interrupt = getattr(import_module("langgraph.types"), "interrupt")
    except (ImportError, AttributeError) as err:
        # Without a working interrupt there is no way to obtain consent, so the
        # only safe answer is no.
        return _abort(f"LangGraph interrupt() unavailable ({err})")

    control_flow_exceptions = _control_flow_exception_types()

    request = {
        "type": "CONFIRMATION_REQUIRED",
        "thread_id": bundle.get("thread_id"),
        "task": bundle.get("task"),
        "digest": bundle.get("bundle_digest"),
        "workspace": bundle.get("workspace_path"),
        "files": sorted(
            list(bundle.get("source_files", {}).keys())
            + list(bundle.get("test_files", {}).keys())
        ),
        "commands": bundle.get("declared_commands", []),
        "qa_status": bundle.get("qa_status", "UNAVAILABLE"),
        "options": ["[y] Approve", "[n] Abort", "[s] Steer with Guidance"],
    }

    try:
        raw_decision = interrupt(request)
    except Exception as err:
        # Suspension must propagate. If we cannot positively identify the
        # control-flow exceptions, re-raise everything rather than risk
        # swallowing a suspend and continuing.
        if not control_flow_exceptions or isinstance(err, control_flow_exceptions):
            raise
        return _abort(f"unexpected error while awaiting approval ({type(err).__name__})")

    decision = parse_gate_decision(raw_decision)
    if decision.action == "abort":
        print("  [Gate] Operator declined. Nothing will be written or executed.")
    elif decision.action == "steer":
        print("  [Gate] Operator steered. Returning to the council.")
    else:
        print("  [Gate] Operator approved. Proceeding to sandboxed execution.")

    return gate_state_update(decision, state.get("council_round", 1))
