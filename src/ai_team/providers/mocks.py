"""Deterministic mock providers for Milestone A orchestration testing without API keys."""

from pathlib import Path
from typing import Optional
from ai_team.domain.contracts import (
    Citation,
    CodeDraft,
    ExecutionBundle,
    ExecutionSummary,
    ResearchFindings,
    ReviewResult,
    TaskPlan,
)
from ai_team.execution.workspace import write_bundle_files
from ai_team.execution.mock_sandbox import MockSandboxRunner


class MockManager:
    """Mock Manager providing deterministic plans and reports."""

    def __init__(self, research_required: bool = False):
        self.research_required = research_required

    def plan(self, task: str) -> TaskPlan:
        return TaskPlan(
            summary=f"Deterministic plan for task: {task}",
            assumptions=["Python 3.9+ standard library environment", "No external dependencies"],
            acceptance_criteria=[
                "Parse input data correctly",
                "Handle empty or invalid inputs gracefully",
                "Pass all automated unit tests",
            ],
            research_required=self.research_required,
            research_questions=["Are there any edge cases with empty strings?"]
            if self.research_required
            else [],
        )

    def report(self, bundle: ExecutionBundle, summary: ExecutionSummary) -> str:
        status_label = "SUCCESS" if summary.success else "FAILURE"
        return (
            f"# Execution Report: {bundle.task}\n\n"
            f"**Status**: {status_label} (Exit Code: {summary.exit_code})\n"
            f"**Workspace**: {bundle.workspace_path}\n"
            f"**Commands Executed**: {len(summary.commands_executed)}\n"
            f"**Files Created**: {', '.join(summary.files_created)}\n\n"
            f"## Output Summary\n```\n{summary.stdout}\n```\n"
        )


class MockResearcher:
    """Mock Researcher providing deterministic grounded findings."""

    def investigate(self, plan: TaskPlan) -> ResearchFindings:
        return ResearchFindings(
            topic=plan.summary,
            findings=[
                "Standard library 'json' and 'csv' modules are fully sufficient.",
                "Using csv.DictReader provides safe row parsing.",
            ],
            citations=[
                Citation(
                    title="Python CSV Documentation",
                    url="https://docs.python.org/3/library/csv.html",
                )
            ],
            gotchas=["Ensure newline='' when opening files for csv readers."],
        )


class MockJuniorDev:
    """Mock Junior Dev providing draft code."""

    def draft(
        self, plan: TaskPlan, findings: Optional[ResearchFindings] = None
    ) -> CodeDraft:
        return CodeDraft(
            source_files={
                "converter.py": (
                    "import csv\nimport json\n\n"
                    "def csv_to_json(csv_text: str) -> str:\n"
                    "    lines = csv_text.strip().splitlines()\n"
                    "    if not lines:\n"
                    "        return json.dumps([])\n"
                    "    reader = csv.DictReader(lines)\n"
                    "    return json.dumps(list(reader))\n"
                )
            },
            test_files={
                "test_converter.py": (
                    "import unittest\nfrom converter import csv_to_json\n\n"
                    "class TestConverter(unittest.TestCase):\n"
                    "    def test_basic(self):\n"
                    "        csv_data = 'name,age\\nAlice,30'\n"
                    "        self.assertIn('Alice', csv_to_json(csv_data))\n"
                )
            },
            implementation_notes="Simple implementation using standard csv and json.",
        )


class MockSeniorReviewer:
    """Mock Senior Dev reviewer providing hardened code and unit tests."""

    def review(
        self,
        plan: TaskPlan,
        draft: CodeDraft,
        findings: Optional[ResearchFindings] = None,
    ) -> ReviewResult:
        finalized_source = (
            "import csv\nimport json\nfrom io import StringIO\nfrom typing import List, Dict\n\n"
            "def csv_to_json(csv_text: str) -> str:\n"
            "    '''Convert CSV string to JSON array of objects.'''\n"
            "    if not csv_text or not csv_text.strip():\n"
            "        return json.dumps([])\n"
            "    f = StringIO(csv_text.strip())\n"
            "    reader = csv.DictReader(f)\n"
            "    rows: List[Dict[str, str]] = list(reader)\n"
            "    return json.dumps(rows, indent=2)\n"
        )

        finalized_test = (
            "import unittest\nimport json\nfrom converter import csv_to_json\n\n"
            "class TestCsvToJson(unittest.TestCase):\n"
            "    def test_valid_csv(self):\n"
            "        data = 'id,name\\n1,Alice\\n2,Bob'\n"
            "        res = json.loads(csv_to_json(data))\n"
            "        self.assertEqual(len(res), 2)\n"
            "        self.assertEqual(res[0]['name'], 'Alice')\n\n"
            "    def test_empty_csv(self):\n"
            "        res = json.loads(csv_to_json(''))\n"
            "        self.assertEqual(res, [])\n\n"
            "if __name__ == '__main__':\n"
            "    unittest.main()\n"
        )

        return ReviewResult(
            approved=True,
            critique="Hardened with StringIO, proper docstrings, and complete test suite.",
            finalized_source_files={"converter.py": finalized_source},
            finalized_test_files={"test_converter.py": finalized_test},
            declared_commands=["python3 -m unittest test_converter.py"],
        )


class MockSeniorExecutor:
    """Mock Senior Dev executor running declared commands locally in workspace."""

    def execute(self, bundle: ExecutionBundle) -> ExecutionSummary:
        workspace = Path(bundle.workspace_path)
        # Write files with path confinement
        write_bundle_files(workspace, bundle.source_files, bundle.test_files)

        # Run declared commands in mock sandbox
        runner = MockSandboxRunner(workspace=workspace)
        return runner.run_commands(bundle.declared_commands)
