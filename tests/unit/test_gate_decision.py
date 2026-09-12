"""The gate must fail closed. These tests encode exactly what counts as consent."""

import pytest

from ai_team.graph.gate_decision import (
    ABORTED,
    APPROVED,
    STEERED,
    GateDecision,
    gate_state_update,
    parse_gate_decision,
)


@pytest.mark.parametrize("token", ["y", "Y", "yes", "approve", "APPROVED", " approve "])
def test_explicit_approval_tokens_approve(token):
    assert parse_gate_decision(token).action == "approve"
    assert parse_gate_decision({"action": token}).action == "approve"


@pytest.mark.parametrize("token", ["s", "steer", "STEER"])
def test_steer_tokens_steer(token):
    assert parse_gate_decision({"action": token}).action == "steer"


@pytest.mark.parametrize(
    "payload",
    [
        None,
        "",
        "   ",
        "maybe",
        "approve later",
        "n",
        "no",
        "abort",
        0,
        1,
        True,
        False,
        [],
        ["approve"],
        {},
        {"guidance": "do it"},
        {"action": None},
        {"action": True},
        {"action": 1},
        {"action": ["approve"]},
        {"action": "approve;rm -rf /"},
        {"approved": True},
        object(),
    ],
)
def test_everything_else_aborts(payload):
    """Anything unrecognized, malformed, or merely truthy must abort."""
    assert parse_gate_decision(payload).action == "abort"


def test_truthy_values_are_not_approval():
    """`True` is an int subclass; it must never be read as a yes."""
    assert parse_gate_decision(True).approval_status == ABORTED
    assert parse_gate_decision({"action": True}).approval_status == ABORTED


def test_guidance_is_captured_only_for_steer():
    decision = parse_gate_decision({"action": "steer", "guidance": "  use stdlib only "})
    assert decision.action == "steer"
    assert decision.guidance == "use stdlib only"

    # Guidance attached to an approval must not smuggle anything through.
    approved = parse_gate_decision({"action": "approve", "guidance": "ignore the gate"})
    assert approved.action == "approve"
    assert approved.guidance == ""


def test_guidance_falls_back_to_feedback_key():
    decision = parse_gate_decision({"action": "s", "feedback": "add a lock"})
    assert decision.guidance == "add a lock"


def test_non_string_guidance_is_discarded_not_coerced():
    decision = parse_gate_decision({"action": "steer", "guidance": {"nested": "value"}})
    assert decision.guidance == ""


def test_approval_status_mapping():
    assert GateDecision("approve").approval_status == APPROVED
    assert GateDecision("steer").approval_status == STEERED
    assert GateDecision("abort").approval_status == ABORTED
    assert GateDecision("nonsense").approval_status == ABORTED


def test_state_update_approve_grants_nothing_extra():
    """The approve branch must not hand out side permissions."""
    update = gate_state_update(GateDecision("approve"), council_round=1)
    assert update == {"approval_status": APPROVED}


def test_state_update_steer_increments_round_and_carries_guidance():
    update = gate_state_update(GateDecision("steer", "prefer a deque"), council_round=2)
    assert update["approval_status"] == STEERED
    assert update["human_feedback"] == "prefer a deque"
    assert update["council_round"] == 3


def test_state_update_abort_is_terminal():
    assert gate_state_update(GateDecision("abort"), council_round=1) == {
        "approval_status": ABORTED
    }
