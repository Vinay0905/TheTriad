"""The human gate, exercised through a real LangGraph `interrupt()`.

The previous version of this file called node functions directly and asserted
on a hand-built state dict, so it proved nothing about suspension or routing.
These tests compile a graph with a checkpointer, let the gate actually suspend,
and resume it with `Command(resume=...)` the way the CLI and server do.
"""

from pathlib import Path
from typing import Any, Dict

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from ai_team.execution.sandbox.base import SandboxResult
from ai_team.graph.builder import GATE_NODE, build_triad_graph, route_gate
from ai_team.graph.contract_lock import compute_test_digest
from ai_team.graph.nodes import sandbox_exec as sandbox_exec_module
from ai_team.graph.nodes.human_gate import human_steering_gate_node
from ai_team.graph.nodes.manager import manager_final_report_node
from ai_team.graph.nodes.preflight import preflight_gate_node
from ai_team.graph.nodes.sandbox_exec import sandbox_execution_node
from ai_team.graph.state import TriadCouncilState

FROZEN_SUITE = (
    "import unittest\n"
    "from main import convert\n\n"
    "class TestConvert(unittest.TestCase):\n"
    "    def test_converts(self):\n"
    "        self.assertEqual(convert('a'), 'A')\n"
)
IMPLEMENTATION = "def convert(value):\n    return value.upper()\n"


def _seed_node(state: TriadCouncilState) -> Dict[str, Any]:
    """Stand in for the council, so no provider is called."""
    return {
        "tdd_contract": {"test_main.py": FROZEN_SUITE, "interfaces.py": ""},
        "tdd_digest": compute_test_digest(FROZEN_SUITE),
        "tdd_locked": True,
        "tdd_status": "LOCKED",
        "synthesized_code": {"main.py": IMPLEMENTATION, "test_main.py": FROZEN_SUITE},
        "qa_passed": True,
        "qa_skipped": False,
        "qa_feedback": "No defects found.",
        "manager_rfc": {"assumptions": [], "acceptance_criteria": ["works"]},
        "repair_attempts": 0,
    }


def _build_gate_graph(checkpointer):
    """The real preflight -> gate -> sandbox -> report path."""
    workflow = StateGraph(TriadCouncilState)
    workflow.add_node("seed_node", _seed_node)
    workflow.add_node("preflight_gate_node", preflight_gate_node)
    workflow.add_node(GATE_NODE, human_steering_gate_node)
    workflow.add_node("sandbox_execution_node", sandbox_execution_node)
    workflow.add_node("manager_final_report_node", manager_final_report_node)

    workflow.add_edge(START, "seed_node")
    workflow.add_edge("seed_node", "preflight_gate_node")
    workflow.add_edge("preflight_gate_node", GATE_NODE)
    workflow.add_conditional_edges(
        GATE_NODE,
        route_gate,
        {
            "sandbox_execution_node": "sandbox_execution_node",
            # Steering would re-enter the council; here it simply ends so the
            # test can assert the gate re-opens rather than delivering.
            "manager_rfc_node": "seed_node",
            "manager_final_report_node": "manager_final_report_node",
        },
    )
    workflow.add_edge("sandbox_execution_node", "manager_final_report_node")
    workflow.add_edge("manager_final_report_node", END)
    return workflow.compile(checkpointer=checkpointer)


@pytest.fixture
def gate_app(monkeypatch, tmp_path):
    """A compiled gate graph writing into an isolated runs directory."""
    monkeypatch.setenv("AI_TEAM_RUNS_DIR", str(tmp_path / "runs"))
    return _build_gate_graph(MemorySaver())


@pytest.fixture
def config_for(tmp_path):
    def _config(thread_id: str) -> Dict[str, Any]:
        return {"configurable": {"thread_id": thread_id}, "recursion_limit": 25}

    return _config


def _advance_to_gate(app, graph_config):
    for _ in app.stream({"task_prompt": "Uppercase a string"}, graph_config):
        pass
    return app.get_state(graph_config)


def _workspace_files(snapshot) -> list:
    bundle = snapshot.values.get("execution_bundle") or {}
    workspace = Path(bundle.get("workspace_path", "/nonexistent"))
    if not workspace.exists():
        return []
    return [p for p in workspace.rglob("*") if p.is_file()]


# -- suspension ---------------------------------------------------------


def test_graph_compiles():
    assert build_triad_graph() is not None


def test_gate_actually_suspends_the_graph(gate_app, config_for):
    snapshot = _advance_to_gate(gate_app, config_for("t_suspend"))

    assert GATE_NODE in snapshot.next, "The gate must halt the graph"
    assert snapshot.values["approval_status"] == "PENDING"
    assert _workspace_files(snapshot) == [], "Nothing may be written before approval"


def test_bundle_carries_the_real_thread_id(gate_app, config_for):
    snapshot = _advance_to_gate(gate_app, config_for("t_thread_id"))
    bundle = snapshot.values["execution_bundle"]

    assert bundle["thread_id"] == "t_thread_id"
    assert "active_session" not in bundle["workspace_path"]


def test_packaged_tests_come_from_the_frozen_contract(gate_app, config_for):
    snapshot = _advance_to_gate(gate_app, config_for("t_frozen"))
    bundle = snapshot.values["execution_bundle"]

    assert bundle["test_files"]["test_main.py"] == FROZEN_SUITE
    assert "hasattr" not in bundle["test_files"]["test_main.py"]


# -- abort --------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        {"action": "abort"},
        {"action": "n"},
        {"action": "no"},
        # Malformed and unrecognized payloads must be treated as refusals.
        {"action": "maybe"},
        {"action": True},
        {},
        "nonsense",
        None,
    ],
)
def test_refusal_writes_nothing_and_runs_nothing(gate_app, config_for, monkeypatch, payload):
    def explode(*args, **kwargs):  # pragma: no cover - must not be reached
        raise AssertionError("The sandbox must not be reached without approval")

    monkeypatch.setattr(sandbox_exec_module, "get_sandbox_runner", explode)

    graph_config = config_for(f"t_abort_{abs(hash(str(payload)))}")
    _advance_to_gate(gate_app, graph_config)

    for _ in gate_app.stream(Command(resume=payload), graph_config):
        pass

    final = gate_app.get_state(graph_config)

    assert not final.next, "The graph should finish after a refusal"
    assert final.values["approval_status"] == "ABORTED"
    assert final.values.get("sandbox_result") is None
    assert _workspace_files(final) == []
    assert "ABORTED BY OPERATOR" in final.values["final_status_report"]


# -- approve ------------------------------------------------------------


def test_approval_writes_files_and_runs_the_sandbox(gate_app, config_for, monkeypatch):
    invocations = []

    class StubRunner:
        name = "stub"

        def is_available(self):
            return True, "stub"

        def run(self, workspace, declared_commands, timeout_seconds, on_output=None):
            invocations.append(
                {"workspace": Path(workspace), "commands": list(declared_commands)}
            )
            return SandboxResult(
                exit_code=0, stdout="Ran 1 test\nOK", backend="stub"
            )

    monkeypatch.setattr(sandbox_exec_module, "get_sandbox_runner", lambda: StubRunner())

    graph_config = config_for("t_approve")
    _advance_to_gate(gate_app, graph_config)

    for _ in gate_app.stream(Command(resume={"action": "approve"}), graph_config):
        pass

    final = gate_app.get_state(graph_config)

    assert final.values["approval_status"] == "APPROVED"
    assert len(invocations) == 1
    assert invocations[0]["commands"] == ["python3 -m unittest test_main.py"]

    written = {p.name for p in _workspace_files(final)}
    assert written == {"main.py", "test_main.py"}

    workspace = invocations[0]["workspace"]
    assert (workspace / "test_main.py").read_text(encoding="utf-8") == FROZEN_SUITE
    assert final.values["sandbox_result"]["exit_code"] == 0
    assert "SUCCESS" in final.values["final_status_report"]


def test_approval_of_a_tampered_bundle_writes_nothing(gate_app, config_for, monkeypatch):
    """Approval is granted for one payload; a changed payload voids it."""

    def explode():  # pragma: no cover - must not be reached
        raise AssertionError("A tampered bundle must not reach the runner")

    monkeypatch.setattr(sandbox_exec_module, "get_sandbox_runner", explode)

    graph_config = config_for("t_tamper")
    snapshot = _advance_to_gate(gate_app, graph_config)

    # Swap the implementation after the operator saw the digest.
    tampered = dict(snapshot.values["execution_bundle"])
    tampered["source_files"] = {"main.py": "import os\nos.system('echo pwned')\n"}
    gate_app.update_state(graph_config, {"execution_bundle": tampered})

    for _ in gate_app.stream(Command(resume={"action": "approve"}), graph_config):
        pass

    final = gate_app.get_state(graph_config)

    assert final.values["sandbox_result"]["exit_code"] != 0
    assert "integrity" in final.values["sandbox_result"]["stderr"].lower()
    assert _workspace_files(final) == []


# -- steer --------------------------------------------------------------


def test_steering_reopens_the_gate_rather_than_delivering(gate_app, config_for):
    graph_config = config_for("t_steer")
    _advance_to_gate(gate_app, graph_config)

    for _ in gate_app.stream(
        Command(resume={"action": "steer", "guidance": "use stdlib only"}), graph_config
    ):
        pass

    snapshot = gate_app.get_state(graph_config)

    # Back at the gate, not finished: a steer is not a delivery.
    assert GATE_NODE in snapshot.next
    assert snapshot.values["human_feedback"] == "use stdlib only"
    assert snapshot.values["council_round"] == 2
    assert snapshot.values.get("sandbox_result") is None


def test_second_decision_after_steering_is_honoured(gate_app, config_for, monkeypatch):
    monkeypatch.setattr(
        sandbox_exec_module,
        "get_sandbox_runner",
        lambda: (_ for _ in ()).throw(AssertionError("must not execute")),
    )

    graph_config = config_for("t_steer_then_abort")
    _advance_to_gate(gate_app, graph_config)

    for _ in gate_app.stream(Command(resume={"action": "steer"}), graph_config):
        pass
    for _ in gate_app.stream(Command(resume={"action": "abort"}), graph_config):
        pass

    final = gate_app.get_state(graph_config)
    assert not final.next
    assert final.values["approval_status"] == "ABORTED"
    assert _workspace_files(final) == []


# -- direct node guard --------------------------------------------------


def test_sandbox_node_refuses_without_approval():
    with pytest.raises(PermissionError):
        sandbox_execution_node({"approval_status": "PENDING", "execution_bundle": {}})

    with pytest.raises(PermissionError):
        sandbox_execution_node({"approval_status": "ABORTED", "execution_bundle": {}})

    with pytest.raises(PermissionError):
        sandbox_execution_node({"execution_bundle": {}})
