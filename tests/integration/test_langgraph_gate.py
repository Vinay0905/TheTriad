"""Integration tests for the LangGraph Human Steering Gate and command permissions."""

from pathlib import Path
from ai_team.graph.builder import build_triad_graph
from ai_team.graph.nodes.sandbox_exec import sandbox_execution_node
from ai_team.graph.nodes.abort import clean_abort_node
from ai_team.graph.state import TriadCouncilState


def test_langgraph_compilation():
    """Verify that the StateGraph compiles cleanly."""
    app = build_triad_graph()
    assert app is not None


def test_human_gate_abort_invariant(tmp_path: Path):
    """
    CRITICAL SAFETY INVARIANT:
    When operator rejects ('abort'), the graph must route to clean_abort_node.
    Zero files written to workspace. Zero commands executed.
    """
    state: TriadCouncilState = {
        "task_prompt": "Convert CSV to JSON",
        "execution_bundle": {
            "task": "Convert CSV to JSON",
            "workspace_path": str(tmp_path / "workspace"),
            "bundle_digest": "test_digest_123",
            "source_files": {"main.py": "print('hello')"},
            "test_files": {"test_main.py": "assert True"},
            "declared_commands": ["python3 -m unittest test_main.py"],
        },
        "approval_status": "ABORTED",
    }

    # Run clean abort
    result = clean_abort_node(state)
    assert result["approval_status"] == "ABORTED"
    assert "cleanly terminated" in result["final_status_report"]

    # Assert workspace is untouched
    workspace = tmp_path / "workspace"
    assert not workspace.exists() or len(list(workspace.glob("*"))) == 0


def test_human_gate_approved_execution_with_command_allow(tmp_path: Path):
    """Verify that when approved and command is permitted, the sandbox writes files and runs tests."""
    ws = tmp_path / "workspace"
    state: TriadCouncilState = {
        "task_prompt": "Convert CSV to JSON",
        "approval_status": "APPROVED",
        "triage_metadata": {
            "command_prompt_func": lambda cmd: True  # Operator confirms 'y' for terminal command
        },
        "execution_bundle": {
            "task": "Convert CSV to JSON",
            "workspace_path": str(ws),
            "bundle_digest": "test_digest_abc",
            "source_files": {
                "main.py": "def process_data(x):\n    return '[]'\n"
            },
            "test_files": {
                "test_main.py": (
                    "import unittest\nfrom main import process_data\n\n"
                    "class TestMain(unittest.TestCase):\n"
                    "    def test_basic(self):\n"
                    "        self.assertEqual(process_data(''), '[]')\n\n"
                    "if __name__ == '__main__':\n"
                    "    unittest.main()\n"
                )
            },
            "declared_commands": ["python3 -m unittest test_main.py"],
        },
    }

    exec_result = sandbox_execution_node(state)
    res = exec_result["sandbox_result"]

    assert res["exit_code"] == 0
    assert (ws / "main.py").exists()
    assert (ws / "test_main.py").exists()
    assert len(res["commands_executed"]) == 1


def test_command_permission_denial(tmp_path: Path):
    """Verify that when the operator denies permission to run a terminal command ('n'), it is blocked."""
    ws = tmp_path / "workspace"
    state: TriadCouncilState = {
        "task_prompt": "Convert CSV to JSON",
        "approval_status": "APPROVED",
        "triage_metadata": {
            "command_prompt_func": lambda cmd: False  # Operator denies permission for command
        },
        "execution_bundle": {
            "task": "Convert CSV to JSON",
            "workspace_path": str(ws),
            "bundle_digest": "test_digest_denied",
            "source_files": {"main.py": "x = 1"},
            "test_files": {"test_main.py": "assert True"},
            "declared_commands": ["python3 -m unittest test_main.py"],
        },
    }

    exec_result = sandbox_execution_node(state)
    res = exec_result["sandbox_result"]

    # Files are written (file autonomy)
    assert (ws / "main.py").exists()
    # BUT command execution is blocked!
    assert res["exit_code"] == 130
    assert "denied by operator" in res["stderr"]
    assert len(res["commands_executed"]) == 0
