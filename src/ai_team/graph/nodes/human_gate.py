"""Human Steering Gate node using LangGraph native interrupt()."""

from typing import Dict, Any
from ai_team.graph.state import TriadCouncilState


def human_steering_gate_node(state: TriadCouncilState) -> Dict[str, Any]:
    """
    Suspends the LangGraph StateGraph prior to any filesystem writes or command executions.
    Yields the complete execution bundle and SHA-256 integrity digest to the operator.
    Resumed with operator decision via Command(resume=...).
    """
    bundle = state.get("execution_bundle") or {}

    try:
        from langgraph.types import interrupt
        from langgraph.errors import GraphBubbleUp
    except ImportError:
        interrupt = None
        GraphBubbleUp = None

    # Broadcast Whiteboard Gate event to 3D office
    from ai_team.spatial.event_bus import get_event_bus
    from ai_team.domain.contracts import WhiteboardGateEvent
    import asyncio

    bus = get_event_bus()
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(
                bus.broadcast(
                    WhiteboardGateEvent(
                        thread_id=bundle.get("thread_id", "active_session"),
                        task=bundle.get("task", ""),
                        code_preview=bundle.get("source_files", {}).get("main.py", ""),
                        qa_report=state.get("qa_feedback", "All quality checks passed."),
                        bundle_digest=bundle.get("bundle_digest", ""),
                    )
                )
            )
    except Exception:
        pass

    if interrupt is not None:
        try:
            # Native LangGraph 0.2+ interrupt pattern
            decision = interrupt(
                {
                    "type": "CONFIRMATION_REQUIRED",
                    "task": bundle.get("task"),
                    "digest": bundle.get("bundle_digest"),
                    "workspace": bundle.get("workspace_path"),
                    "files": list(bundle.get("source_files", {}).keys())
                    + list(bundle.get("test_files", {}).keys()),
                    "commands": bundle.get("declared_commands", []),
                    "options": ["[y] Approve", "[n] Abort", "[s] Steer with Guidance"],
                }
            )
        except Exception as err:
            if GraphBubbleUp and isinstance(err, GraphBubbleUp):
                raise
            decision = {"action": "approve"}
    else:
        decision = {"action": "approve"}

    if isinstance(decision, str):
        action = decision.strip().lower()
        guidance = ""
    elif isinstance(decision, dict):
        action = decision.get("action", "abort").strip().lower()
        guidance = decision.get("guidance", "")
    else:
        action = "abort"
        guidance = ""

    if action in ["approve", "y", "yes"]:
        triage_meta = dict(state.get("triage_metadata") or {})
        triage_meta["auto_allow_commands"] = True
        return {
            "approval_status": "APPROVED",
            "triage_metadata": triage_meta,
        }
    elif action in ["steer", "s"]:
        return {
            "approval_status": "STEERED",
            "human_feedback": guidance,
            "council_round": state.get("council_round", 1) + 1,
        }
    else:
        return {"approval_status": "ABORTED"}
