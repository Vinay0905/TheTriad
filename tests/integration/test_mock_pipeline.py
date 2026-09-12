"""Integration test for full end-to-end pipeline execution with mock providers."""

from pathlib import Path
from ai_team.domain.states import State, TerminalStatus
from ai_team.orchestration.state_machine import OrchestrationRun
from ai_team.providers.mocks import (
    MockJuniorDev,
    MockManager,
    MockResearcher,
    MockSeniorExecutor,
    MockSeniorReviewer,
)


def test_mock_pipeline_end_to_end_success(tmp_path: Path):
    """
    Test complete lifecycle with human approval:
    RECEIVED -> PLANNING -> RESEARCH_SKIPPED -> DRAFTING -> REVIEWING ->
    BUNDLE_LOCKED -> AWAITING_APPROVAL -> EXECUTING -> REPORTING -> SUCCEEDED.
    """
    orchestrator = OrchestrationRun(
        task="Write a CSV to JSON converter",
        manager=MockManager(research_required=False),
        researcher=MockResearcher(),
        junior_dev=MockJuniorDev(),
        senior_reviewer=MockSeniorReviewer(),
        senior_executor=MockSeniorExecutor(),
        runs_dir=tmp_path,
        approval_func=lambda bundle: True,  # Human approves 'y'
    )

    final_state = orchestrator.run()

    # 1. Verify terminal status
    assert final_state == State.SUCCEEDED
    assert orchestrator.terminal_status == TerminalStatus.SUCCESS

    # 2. Verify summary
    assert orchestrator.summary is not None
    assert orchestrator.summary.success is True
    assert orchestrator.summary.exit_code == 0
    assert len(orchestrator.summary.commands_executed) == 1

    # 3. Verify workspace artifacts
    workspace = orchestrator.workspace
    assert (workspace / "converter.py").exists()
    assert (workspace / "test_converter.py").exists()

    # 4. Verify run directory artifacts
    run_dir = orchestrator.persistence.run_dir
    assert (run_dir / "01_plan.json").exists()
    assert (run_dir / "03_draft.json").exists()
    assert (run_dir / "04_review.json").exists()
    assert (run_dir / "05_bundle.json").exists()
    assert (run_dir / "06_decision.json").exists()
    assert (run_dir / "07_execution.json").exists()
    assert (run_dir / "08_final_report.md").exists()
    assert (run_dir / "events.jsonl").exists()


def test_mock_pipeline_with_research_grounding(tmp_path: Path):
    """Verify research phase is invoked when research_required is True."""
    orchestrator = OrchestrationRun(
        task="Write a modern CSV to JSON converter",
        manager=MockManager(research_required=True),
        researcher=MockResearcher(),
        junior_dev=MockJuniorDev(),
        senior_reviewer=MockSeniorReviewer(),
        senior_executor=MockSeniorExecutor(),
        runs_dir=tmp_path,
        approval_func=lambda bundle: True,
    )

    final_state = orchestrator.run()
    assert final_state == State.SUCCEEDED
    assert orchestrator.findings is not None
    assert len(orchestrator.findings.citations) > 0
    assert (orchestrator.persistence.run_dir / "02_research.json").exists()
