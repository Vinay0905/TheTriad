"""Unit tests for domain contracts and Pydantic schema validation."""

import pytest
from pydantic import ValidationError
from ai_team.domain.contracts import (
    Citation,
    CodeDraft,
    ExecutionBundle,
    ExecutionSummary,
    ResearchFindings,
    ReviewResult,
    TaskPlan,
)


def test_task_plan_valid():
    plan = TaskPlan(
        summary="Convert CSV to JSON",
        assumptions=["Standard library only"],
        acceptance_criteria=["Correct JSON output", "Handles empty input"],
        research_required=False,
    )
    assert plan.summary == "Convert CSV to JSON"
    assert len(plan.acceptance_criteria) == 2
    assert plan.research_required is False


def test_task_plan_empty_criteria_fails():
    with pytest.raises(ValidationError):
        TaskPlan(
            summary="Invalid task",
            acceptance_criteria=[],  # Must have at least 1 item
        )


def test_research_findings():
    findings = ResearchFindings(
        topic="CSV parsing",
        findings=["csv.DictReader is safe"],
        citations=[Citation(title="Python docs", url="https://docs.python.org")],
        gotchas=["newline='' is recommended"],
    )
    assert len(findings.citations) == 1
    assert findings.citations[0].url == "https://docs.python.org"


def test_code_draft_requires_source_files():
    with pytest.raises(ValidationError):
        CodeDraft(source_files={})  # Must not be empty

    draft = CodeDraft(source_files={"main.py": "print('hello')"})
    assert "main.py" in draft.source_files


def test_review_result():
    res = ReviewResult(
        approved=True,
        critique="Good code",
        finalized_source_files={"app.py": "x = 1"},
        finalized_test_files={"test_app.py": "assert True"},
        declared_commands=["python3 -m unittest"],
    )
    assert res.approved is True
    assert len(res.declared_commands) == 1


def test_execution_summary():
    summary = ExecutionSummary(
        success=True,
        exit_code=0,
        stdout="Tests passed",
        stderr="",
        files_created=["app.py"],
        commands_executed=["pytest"],
    )
    assert summary.success is True
    assert summary.exit_code == 0
