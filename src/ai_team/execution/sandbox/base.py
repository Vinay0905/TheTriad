"""The SandboxRunner seam.

Execution is isolated behind this protocol so the graph never learns which
backend is in use. Docker is the implementation today; E2B or Modal can be
added later by writing another runner and changing `AI_TEAM_SANDBOX`, with no
change to the gate or the nodes.

Every runner must honour one rule: if isolation cannot be established, refuse.
Falling back to the host would defeat the point of asking for approval.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Protocol, Sequence, Tuple, runtime_checkable

# Conventional exit codes for refusals, chosen to not collide with test failures.
EXIT_SANDBOX_UNAVAILABLE = 127
EXIT_POLICY_BLOCKED = 126
EXIT_TIMEOUT = 124

OutputCallback = Callable[[str, str], None]
"""Called as (stream, chunk) where stream is "stdout" or "stderr"."""


class SandboxUnavailableError(RuntimeError):
    """Raised when the isolation backend cannot be used at all."""


@dataclass
class SandboxResult:
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    commands_executed: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    failing_tests_count: int = 0
    timed_out: bool = False
    backend: str = ""

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0

    def as_state_dict(self) -> dict:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout.strip(),
            "stderr": self.stderr.strip(),
            "commands_executed": list(self.commands_executed),
            "files_created": list(self.files_created),
            "failing_tests_count": self.failing_tests_count,
            "timed_out": self.timed_out,
            "backend": self.backend,
        }


@runtime_checkable
class SandboxRunner(Protocol):
    """An isolated execution backend."""

    name: str

    def is_available(self) -> Tuple[bool, str]:
        """Whether the backend can run right now, and why not if it cannot."""

    def run(
        self,
        workspace: Path,
        declared_commands: Sequence[str],
        timeout_seconds: int,
        on_output: Optional[OutputCallback] = None,
    ) -> SandboxResult:
        """Execute the declared commands against a prepared workspace."""


def parse_failing_tests(output: str) -> int:
    """Extract a failure count from unittest/pytest output.

    Best-effort only; the exit code remains the authority on success.
    """
    import re

    total = 0
    for pattern in (r"failures=(\d+)", r"errors=(\d+)", r"(\d+) failed"):
        for match in re.finditer(pattern, output or ""):
            try:
                total += int(match.group(1))
            except (TypeError, ValueError):
                continue
    return total
