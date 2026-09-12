"""Integration tests verifying the Human Confirmation Gate safety boundary."""

from pathlib import Path
from unittest.mock import MagicMock
from ai_team.domain.states import State, TerminalStatus
from ai_team.orchestration.state_machine import OrchestrationRun
from ai_team.providers.mocks import (
    MockJuniorDev,
    MockManager,
    MockResearcher,
    MockSeniorExecutor,
    MockSeniorReviewer,
)


def test_safety_gate_rejection_guarantees_zero_execution(tmp_path: Path):
    """
    NON-NEGOTIABLE SAFETY INVARIANT:
    Rejecting at the human confirmation gate ('n') MUST:
    1. Immediately halt the pipeline in State.ABORTED.
    2. Never invoke the SeniorExecutor.
    3. Write zero files to the workspace.
    4. Execute zero shell commands.
    """
    mock_executor = MagicMock(spec=MockSeniorExecutor)

    orchestrator = OrchestrationRun(
        task="Write a CSV to JSON tool",
        manager=MockManager(research_required=False),
        researcher=MockResearcher(),
        junior_dev=MockJuniorDev(),
        senior_reviewer=MockSeniorReviewer(),
        senior_executor=mock_executor,
        runs_dir=tmp_path,
        approval_func=lambda bundle: False,  # Human says 'n'
    )

    final_state = orchestrator.run()

    # 1. State must be ABORTED
    assert final_state == State.ABORTED
    assert orchestrator.terminal_status == TerminalStatus.ABORTED_BY_USER

    # 2. SeniorExecutor MUST NOT be invoked
    assert mock_executor.execute.call_count == 0

    # 3. Workspace must be completely empty
    workspace_files = list(orchestrator.workspace.rglob("*"))
    # Only empty directory exists, zero files written
    assert len([p for p in workspace_files if p.is_file()]) == 0

    # 4. Decision artifact must record rejection
    decision_file = orchestrator.persistence.run_dir / "06_decision.json"
    assert decision_file.exists()
    assert '"approved": false' in decision_file.read_text()
