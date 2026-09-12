"""State machine orchestrator managing lifecycle, transitions, invariants, and evidence capture."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional
from ai_team.domain.budgets import BudgetTracker, BudgetExceededError
from ai_team.domain.contracts import (
    CodeDraft,
    ExecutionBundle,
    ExecutionSummary,
    ResearchFindings,
    ReviewResult,
    TaskPlan,
)
from ai_team.domain.states import State, TerminalStatus
from ai_team.execution.workspace import create_run_workspace
from ai_team.orchestration.approval import prompt_human_approval
from ai_team.orchestration.bundle import (
    create_execution_bundle,
    verify_bundle_integrity,
    BundleTamperError,
)
from ai_team.persistence.runs import RunPersistence
from ai_team.providers.base import (
    JuniorDevProvider,
    ManagerProvider,
    ResearcherProvider,
    SeniorExecutorProvider,
    SeniorReviewerProvider,
)


class OrchestrationRun:
    """Manages an individual execution run through the finite state machine."""

    def __init__(
        self,
        task: str,
        manager: ManagerProvider,
        researcher: ResearcherProvider,
        junior_dev: JuniorDevProvider,
        senior_reviewer: SeniorReviewerProvider,
        senior_executor: SeniorExecutorProvider,
        runs_dir: Path = Path(".runs"),
        approval_func: Optional[Callable[[ExecutionBundle], bool]] = None,
        budget_tracker: Optional[BudgetTracker] = None,
    ):
        self.task = task
        self.manager = manager
        self.researcher = researcher
        self.junior_dev = junior_dev
        self.senior_reviewer = senior_reviewer
        self.senior_executor = senior_executor
        self.runs_dir = runs_dir
        self.approval_func = approval_func or prompt_human_approval
        self.budget_tracker = budget_tracker or BudgetTracker()

        # Generate unique run ID
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        short_id = uuid.uuid4().hex[:6]
        self.run_id = f"run_{timestamp_str}_{short_id}"

        # Initialize persistence and workspace
        self.persistence = RunPersistence(self.runs_dir, self.run_id)
        self.workspace = create_run_workspace(self.runs_dir, self.run_id)

        # State tracking
        self.current_state = State.RECEIVED
        self.plan: Optional[TaskPlan] = None
        self.findings: Optional[ResearchFindings] = None
        self.draft: Optional[CodeDraft] = None
        self.review: Optional[ReviewResult] = None
        self.bundle: Optional[ExecutionBundle] = None
        self.summary: Optional[ExecutionSummary] = None
        self.final_report: Optional[str] = None
        self.terminal_status: Optional[TerminalStatus] = None

    def _transition(self, to_state: State, payload: Optional[dict] = None) -> None:
        """Enforce transition invariants and log the transition."""
        from_state = self.current_state

        # Invariant: No pre-approval state may write files or execute commands
        if from_state != State.AWAITING_APPROVAL and to_state == State.EXECUTING:
            raise RuntimeError("Cannot transition to EXECUTING without passing AWAITING_APPROVAL")

        self.persistence.log_event(from_state.value, to_state.value, payload)
        self.current_state = to_state

    def run(self) -> State:
        """Execute the state machine pipeline until a terminal state is reached."""
        try:
            # 1. RECEIVED -> PLANNING
            self._transition(State.PLANNING)
            self.budget_tracker.record_call()
            self.plan = self.manager.plan(self.task)
            self.persistence.save_artifact("01_plan.json", self.plan)

            # 2. PLANNING -> RESEARCHING / RESEARCH_SKIPPED
            if self.plan.research_required:
                self._transition(State.RESEARCHING)
                self.budget_tracker.record_call()
                self.findings = self.researcher.investigate(self.plan)
                self.persistence.save_artifact("02_research.json", self.findings)
            else:
                self._transition(State.RESEARCH_SKIPPED)

            # 3. RESEARCH -> DRAFTING
            self._transition(State.DRAFTING)
            self.budget_tracker.record_call()
            self.draft = self.junior_dev.draft(self.plan, self.findings)
            self.persistence.save_artifact("03_draft.json", self.draft)

            # 4. DRAFTING -> REVIEWING
            self._transition(State.REVIEWING)
            self.budget_tracker.record_call()
            self.review = self.senior_reviewer.review(
                self.plan, self.draft, self.findings
            )
            self.persistence.save_artifact("04_review.json", self.review)

            # 5. REVIEWING -> BUNDLE_LOCKED
            self._transition(State.BUNDLE_LOCKED)
            self.bundle = create_execution_bundle(
                task=self.task,
                assumptions=self.plan.assumptions,
                acceptance_criteria=self.plan.acceptance_criteria,
                source_files=self.review.finalized_source_files,
                test_files=self.review.finalized_test_files,
                declared_commands=self.review.declared_commands,
                workspace_path=str(self.workspace),
            )
            self.persistence.save_artifact("05_bundle.json", self.bundle)

            # 6. BUNDLE_LOCKED -> AWAITING_APPROVAL
            self._transition(State.AWAITING_APPROVAL)
            is_approved = self.approval_func(self.bundle)

            if not is_approved:
                # Human declined execution -> Clean ABORT with zero side effects
                self._transition(State.ABORTED, {"decision": "REJECTED"})
                self.terminal_status = TerminalStatus.ABORTED_BY_USER
                self.persistence.save_artifact(
                    "06_decision.json", {"approved": False, "status": "ABORTED"}
                )
                return self.current_state

            # Verify bundle integrity before proceeding
            try:
                verify_bundle_integrity(self.bundle)
            except BundleTamperError as e:
                self._transition(State.INVALID, {"error": str(e)})
                self.terminal_status = TerminalStatus.INVALID_CONTRACT
                return self.current_state

            self.persistence.save_artifact(
                "06_decision.json", {"approved": True, "digest": self.bundle.bundle_digest}
            )

            # 7. AWAITING_APPROVAL -> EXECUTING (Antigravity Sandbox)
            self._transition(State.EXECUTING)
            self.budget_tracker.record_call()
            self.summary = self.senior_executor.execute(self.bundle)
            self.persistence.save_artifact("07_execution.json", self.summary)

            # 8. EXECUTING -> REPORTING
            self._transition(State.REPORTING)
            self.final_report = self.manager.report(self.bundle, self.summary)
            self.persistence.save_artifact("08_final_report.md", self.final_report)

            # 9. REPORTING -> SUCCEEDED or FAILED
            if self.summary.success:
                self._transition(State.SUCCEEDED)
                self.terminal_status = TerminalStatus.SUCCESS
            else:
                self._transition(State.FAILED)
                self.terminal_status = TerminalStatus.FAILURE

            return self.current_state

        except BudgetExceededError as e:
            self._transition(State.BLOCKED, {"budget_error": str(e)})
            self.terminal_status = TerminalStatus.BLOCKED_BY_POLICY
            return self.current_state

        except Exception as e:
            self._transition(State.INVALID, {"unhandled_exception": str(e)})
            self.terminal_status = TerminalStatus.INVALID_CONTRACT
            raise e
