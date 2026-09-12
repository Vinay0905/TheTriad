"""Mock execution runner used for deterministic Milestone A testing."""

import subprocess
from pathlib import Path
from typing import List
from ai_team.domain.contracts import ExecutionSummary


class MockSandboxRunner:
    """Executes declared commands locally in the run workspace for Milestone A tests."""

    def __init__(self, workspace: Path, timeout_seconds: int = 30):
        self.workspace = workspace.resolve()
        self.timeout_seconds = timeout_seconds

    def run_commands(self, declared_commands: List[str]) -> ExecutionSummary:
        """Run declared commands sequentially inside the workspace, capturing evidence."""
        executed = []
        combined_stdout = []
        combined_stderr = []
        last_exit_code = 0

        for cmd in declared_commands:
            executed.append(cmd)
            try:
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                )
                combined_stdout.append(proc.stdout)
                combined_stderr.append(proc.stderr)
                last_exit_code = proc.returncode

                if proc.returncode != 0:
                    break

            except subprocess.TimeoutExpired:
                combined_stderr.append(
                    f"Command timed out after {self.timeout_seconds} seconds: {cmd}"
                )
                last_exit_code = 124
                break
            except Exception as e:
                combined_stderr.append(f"Command execution error: {str(e)}")
                last_exit_code = 1
                break

        # List all relative files in workspace
        files_created = [
            str(p.relative_to(self.workspace))
            for p in self.workspace.rglob("*")
            if p.is_file()
        ]

        return ExecutionSummary(
            success=(last_exit_code == 0),
            exit_code=last_exit_code,
            stdout="\n".join(combined_stdout).strip(),
            stderr="\n".join(combined_stderr).strip(),
            files_created=files_created,
            commands_executed=executed,
            error_summary=None if last_exit_code == 0 else "One or more commands failed",
        )
