"""Sandbox backends and the factory that selects one."""

import time
from typing import Optional, Tuple

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
    "sandbox_status",
]

# Probing availability shells out to `docker version`, which costs on the order
# of a hundred milliseconds. The HUD asks for it on every provider event and
# every socket connect, so the answer is cached briefly.
_STATUS_TTL_SECONDS = 15.0
_status_cache: Tuple[float, bool, str] = (0.0, False, "not probed")


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


def sandbox_status(force: bool = False) -> Tuple[bool, str]:
    """Whether isolation is currently usable, and why not if it is not.

    Cached for a few seconds. Never raises: a reporting path must not be able
    to take down the server.
    """
    global _status_cache

    checked_at, available, detail = _status_cache
    now = time.monotonic()
    if not force and now - checked_at < _STATUS_TTL_SECONDS and checked_at > 0.0:
        return available, detail

    try:
        available, detail = get_sandbox_runner().is_available()
    except Exception as err:
        available, detail = False, str(err)

    _status_cache = (now, available, detail)
    return available, detail
