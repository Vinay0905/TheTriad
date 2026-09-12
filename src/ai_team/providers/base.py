"""Abstract provider interfaces decoupled from specific LLM SDKs."""

from typing import Optional, Protocol
from ai_team.domain.contracts import (
    CodeDraft,
    ExecutionBundle,
    ExecutionSummary,
    ResearchFindings,
    ReviewResult,
    TaskPlan,
)


class ManagerProvider(Protocol):
    """Interface for the Manager role (Task decomposition and final reporting)."""

    def plan(self, task: str) -> TaskPlan:
        """Decompose a natural language task into a structured plan."""
        ...

    def report(self, bundle: ExecutionBundle, summary: ExecutionSummary) -> str:
        """Synthesize final human-readable report from execution evidence."""
        ...


class ResearcherProvider(Protocol):
    """Interface for the Researcher role (Search-grounded fact gathering)."""

    def investigate(self, plan: TaskPlan) -> ResearchFindings:
        """Research real-world facts, gotchas, and documentation for the plan."""
        ...


class JuniorDevProvider(Protocol):
    """Interface for the Junior Dev role (First-pass code drafting)."""

    def draft(
        self, plan: TaskPlan, findings: Optional[ResearchFindings] = None
    ) -> CodeDraft:
        """Produce an initial, exploratory code draft satisfying the plan."""
        ...


class SeniorReviewerProvider(Protocol):
    """Interface for the Senior Dev review role (Read-only analysis and hardening)."""

    def review(
        self,
        plan: TaskPlan,
        draft: CodeDraft,
        findings: Optional[ResearchFindings] = None,
    ) -> ReviewResult:
        """Critique and finalize code, test suite, and execution commands."""
        ...


class SeniorExecutorProvider(Protocol):
    """Interface for the Senior Dev execution role (Sandboxed execution and evidence capture)."""

    def execute(self, bundle: ExecutionBundle) -> ExecutionSummary:
        """Execute the approved bundle inside the sandbox and capture real evidence."""
        ...
