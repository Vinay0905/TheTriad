"""Sandbox backends and the factory that selects one."""

from typing import Optional

from ai_team.config import get_config
from ai_team.execution.sandbox.base import (
    EXIT_POLICY_BLOCKED,
    EXIT_SANDBOX_UNAVAILABLE,
    EXIT_TIMEOUT,
    SandboxResult,
    SandboxRunner,
    SandboxUnavailableError,
)

__all__ = [
    "EXIT_POLICY_BLOCKED",
    "EXIT_SANDBOX_UNAVAILABLE",
    "EXIT_TIMEOUT",
    "SandboxResult",
    "SandboxRunner",
    "SandboxUnavailableError",
    "get_sandbox_runner",
]


def get_sandbox_runner(backend: Optional[str] = None) -> SandboxRunner:
    """Return the configured isolation backend.

    An unknown backend name is an error rather than a silent downgrade: the
    operator should never be told a run was isolated when it was not.
    """
    selected = (backend or get_config().sandbox_backend or "docker").strip().lower()

    if selected == "docker":
        from ai_team.execution.sandbox.docker_runner import DockerSandboxRunner

        return DockerSandboxRunner()

    raise SandboxUnavailableError(
        f"Unknown sandbox backend {selected!r}. Supported backends: 'docker'. "
        "Set AI_TEAM_SANDBOX accordingly."
    )
