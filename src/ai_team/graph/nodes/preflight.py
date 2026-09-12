"""Manager pre-flight gate: package the approved payload and lock its digest.

This node decides exactly what the operator is asked to approve. It therefore
does not repair, substitute, or improve anything. If the implementation is not
valid Python, that is QA's verdict to report, not preflight's to paper over.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from ai_team.config import get_config
from ai_team.execution.bundle import build_bundle
from ai_team.execution.sandbox.allowlist import allowed_commands
from ai_team.graph.contract_lock import assert_contract_unbroken, frozen_test_source
from ai_team.graph.state import TriadCouncilState

DEFAULT_COMMAND = "python3 -m unittest test_main.py"


def _thread_id(config_arg: Optional[Dict[str, Any]]) -> str:
    """Read the real thread id from the graph config.

    The bundle previously carried the literal string "active_session", which
    meant the gate event and the download endpoint could not identify the run.
    """
    if isinstance(config_arg, dict):
        configurable = config_arg.get("configurable") or {}
        thread_id = configurable.get("thread_id")
        if thread_id:
            return str(thread_id)
    return "unknown_thread"


def preflight_gate_node(
    state: TriadCouncilState, config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Assemble the ExecutionBundle and compute its integrity digest."""
    assert_contract_unbroken(state, "the preflight gate")

    app_config = get_config()
    task = state.get("task_prompt", "")
    synthesized = state.get("synthesized_code") or {}

    # Source is whatever the developer produced; tests come from the frozen
    # contract, never from the developer's output.
    source_files = {
        name: content
        for name, content in synthesized.items()
        if not name.startswith("test_")
    }
    source_files.setdefault("main.py", "")
    test_files = {"test_main.py": frozen_test_source(state)}

    declared_commands = [DEFAULT_COMMAND]
    if DEFAULT_COMMAND not in allowed_commands():  # pragma: no cover - guards a typo
        raise RuntimeError(
            f"Default declared command {DEFAULT_COMMAND!r} is not on the sandbox allowlist."
        )

    thread_id = _thread_id(config)
    workspace_path = str(Path(app_config.runs_dir) / thread_id / "workspace")

    # QA status travels with the bundle so the gate can state it plainly.
    if state.get("qa_skipped"):
        qa_status = "UNAVAILABLE"
    elif state.get("qa_passed"):
        qa_status = "PASS"
    else:
        qa_status = "FAIL"

    rfc = state.get("manager_rfc") or {}
    bundle = build_bundle(
        task=task,
        source_files=source_files,
        test_files=test_files,
        declared_commands=declared_commands,
        workspace_path=workspace_path,
        thread_id=thread_id,
        assumptions=rfc.get("assumptions", []),
        acceptance_criteria=rfc.get("acceptance_criteria", []),
        qa_status=qa_status,
        qa_report=state.get("qa_feedback", ""),
        tdd_digest=state.get("tdd_digest", ""),
        provider_attribution=state.get("provider_attribution") or {},
    )

    print(
        f"  [Preflight] Bundle locked for {thread_id}: "
        f"digest {bundle['bundle_digest'][:12]}..., QA {qa_status}"
    )

    return {
        "execution_bundle": bundle,
        "approval_status": "PENDING",
    }
