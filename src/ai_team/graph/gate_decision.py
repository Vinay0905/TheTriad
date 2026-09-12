"""Fail-closed parsing of human gate decisions.

This module is deliberately free of LangGraph imports so the safety-critical
mapping can be unit tested on its own. The governing rule is simple: approval
must be explicit and unambiguous. Anything else aborts.
"""

from dataclasses import dataclass
from typing import Any, Dict, Final

APPROVED: Final = "APPROVED"
STEERED: Final = "STEERED"
ABORTED: Final = "ABORTED"

# Only these exact tokens grant permission to touch a filesystem or run a command.
_APPROVE_TOKENS: Final = frozenset({"y", "yes", "approve", "approved"})
_STEER_TOKENS: Final = frozenset({"s", "steer", "steered"})

_ACTION_TO_STATUS: Final = {
    "approve": APPROVED,
    "steer": STEERED,
    "abort": ABORTED,
}


@dataclass(frozen=True)
class GateDecision:
    """A normalized operator decision."""

    action: str  # "approve" | "steer" | "abort"
    guidance: str = ""

    @property
    def approval_status(self) -> str:
        return _ACTION_TO_STATUS.get(self.action, ABORTED)


def _coerce_guidance(value: Any) -> str:
    """Guidance is advisory free text. Anything non-textual is discarded, not coerced."""
    if isinstance(value, str):
        return value.strip()
    return ""


def _normalize_action(value: Any) -> str:
    """Map a raw action token to an action, defaulting to abort.

    `bool` is rejected explicitly because it is a subclass of `int` and a stray
    ``True`` must never read as approval.
    """
    if isinstance(value, bool) or not isinstance(value, str):
        return "abort"

    token = value.strip().lower()
    if token in _APPROVE_TOKENS:
        return "approve"
    if token in _STEER_TOKENS:
        return "steer"
    return "abort"


def parse_gate_decision(raw: Any) -> GateDecision:
    """Normalize an arbitrary resume payload into a decision, failing closed.

    Accepts a bare string (``"y"``) or a mapping (``{"action": "steer",
    "guidance": "..."}``). Every other shape, and every unrecognized token,
    resolves to abort.
    """
    if isinstance(raw, str):
        return GateDecision(action=_normalize_action(raw))

    if isinstance(raw, dict):
        action = _normalize_action(raw.get("action"))
        if action == "steer":
            guidance = _coerce_guidance(raw.get("guidance")) or _coerce_guidance(
                raw.get("feedback")
            )
            return GateDecision(action=action, guidance=guidance)
        return GateDecision(action=action)

    return GateDecision(action="abort")


def gate_state_update(decision: GateDecision, council_round: int) -> Dict[str, Any]:
    """Build the state delta for a decision.

    Kept next to the parser so the approve branch cannot quietly acquire extra
    permissions somewhere else in the graph.
    """
    if decision.action == "approve":
        return {"approval_status": APPROVED}

    if decision.action == "steer":
        return {
            "approval_status": STEERED,
            "human_feedback": decision.guidance,
            "council_round": council_round + 1,
        }

    return {"approval_status": ABORTED}
