"""Sandboxed execution node: the only place in the system that runs code.

Preconditions, checked in this order and all fatal:

1. The operator explicitly approved.
2. The frozen test contract is intact.
3. The bundle still hashes to the digest that was approved.

Only then are files written, and only inside an isolated workspace. Execution
itself happens through a `SandboxRunner`, which refuses to run at all if
isolation is unavailable. There is no host execution path and no second
interactive prompt: the human gate is the permission.
"""

from pathlib import Path
from typing import Any, Dict

from ai_team.config import get_config
from ai_team.domain.contracts import TerminalLogEvent
from ai_team.execution.bundle import BundleTamperError, verify_bundle_integrity
from ai_team.execution.sandbox import get_sandbox_runner
from ai_team.execution.sandbox.base import EXIT_SANDBOX_UNAVAILABLE, SandboxResult
from ai_team.execution.workspace import write_bundle_files
from ai_team.graph.contract_lock import assert_contract_unbroken
from ai_team.graph.state import TriadCouncilState
from ai_team.persistence.redaction import redact_secrets
from ai_team.spatial.event_bus import get_event_bus


def _stream_to_office(stream: str, chunk: str) -> None:
    """Mirror container output to the HUD, with secrets masked."""
    try:
        get_event_bus().dispatch(
            TerminalLogEvent(stream=stream, chunk=redact_secrets(chunk))
        )
    except Exception as err:
        print(f"  [Sandbox] log dispatch skipped: {err}")


def sandbox_execution_node(state: TriadCouncilState) -> Dict[str, Any]:
    """Write and run the approved bundle inside the isolation backend."""
    if state.get("approval_status") != "APPROVED":
        raise PermissionError(
            "Refusing to execute: the operator has not approved this bundle."
        )

    assert_contract_unbroken(state, "sandbox execution")

    config = get_config()
    bundle = state.get("execution_bundle") or {}

    # The approval was granted for a specific payload. If anything changed
    # since, the approval no longer applies, so nothing is written.
    try:
        digest = verify_bundle_integrity(bundle)
    except BundleTamperError as err:
        message = f"Execution refused: {err}"
        print(f"  [Sandbox] {message}")
        _stream_to_office("stderr", message)
        return {
            "sandbox_result": SandboxResult(
                exit_code=EXIT_SANDBOX_UNAVAILABLE,
                stderr=message,
                backend="none",
            ).as_state_dict(),
            "last_failing_tests_count": 1,
        }

    runner = get_sandbox_runner()

    workspace = Path(bundle["workspace_path"]).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    files_created = write_bundle_files(
        workspace=workspace,
        source_files=bundle.get("source_files") or {},
        test_files=bundle.get("test_files") or {},
    )
    print(
        f"  [Sandbox] Wrote {len(files_created)} file(s) to {workspace} "
        f"for digest {digest[:12]}..."
    )

    result = runner.run(
        workspace=workspace,
        declared_commands=bundle.get("declared_commands") or [],
        timeout_seconds=config.execution_timeout_seconds,
        on_output=_stream_to_office,
    )
    result.files_created = files_created

    print(
        f"  [Sandbox/{result.backend}] exit={result.exit_code} "
        f"failing_tests={result.failing_tests_count}"
    )

    return {
        "sandbox_result": result.as_state_dict(),
        "last_failing_tests_count": result.failing_tests_count,
    }
