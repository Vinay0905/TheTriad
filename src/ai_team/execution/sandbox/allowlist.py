"""Exact-match command allowlist.

The previous implementation matched command *prefixes* and then handed the
string to a shell, so `python3 -m unittest test_main.py; rm -rf /` passed the
check. Two changes fix that class of bug outright:

- Matching is on the whole declared command string, not a prefix, so any extra
  token or shell metacharacter simply fails to find a key.
- The value is an argv list, executed without a shell, so metacharacters have
  no interpreter to reach even if one slipped through.

Commands here are the *declared* strings that appear in the ExecutionBundle and
are shown to the operator at the gate. The argv is what actually runs inside
the container, where the interpreter is always `python`.
"""

from typing import Dict, List, Tuple

JUNIT_REPORT_PATH = ".artifacts/junit.xml"

# Declared command string -> argv executed inside the sandbox container.
_ALLOWED: Dict[str, Tuple[str, ...]] = {
    "python3 -m unittest test_main.py": (
        "python",
        "-m",
        "unittest",
        "-v",
        "test_main.py",
    ),
    "python -m unittest test_main.py": (
        "python",
        "-m",
        "unittest",
        "-v",
        "test_main.py",
    ),
    "python3 -m unittest discover -s . -p test_*.py": (
        "python",
        "-m",
        "unittest",
        "discover",
        "-s",
        ".",
        "-p",
        "test_*.py",
    ),
    "python3 -m pytest test_main.py": (
        "python",
        "-m",
        "pytest",
        "-q",
        "test_main.py",
    ),
    # Emits machine-readable evidence alongside the human-readable output.
    "python3 -m pytest --junitxml test_main.py": (
        "python",
        "-m",
        "pytest",
        "-q",
        f"--junitxml={JUNIT_REPORT_PATH}",
        "test_main.py",
    ),
}


class CommandNotAllowedError(ValueError):
    """Raised when a declared command is not on the allowlist."""


def is_allowed(declared_command: str) -> bool:
    return (declared_command or "").strip() in _ALLOWED


def resolve_argv(declared_command: str) -> List[str]:
    """Translate a declared command into argv, or refuse.

    Refusal is total: there is no partial match, no normalization beyond
    stripping surrounding whitespace, and no shell.
    """
    key = (declared_command or "").strip()
    argv = _ALLOWED.get(key)
    if argv is None:
        raise CommandNotAllowedError(
            f"Command {declared_command!r} is not on the sandbox allowlist. "
            "Only exact, pre-approved test invocations may run."
        )
    return list(argv)


def allowed_commands() -> List[str]:
    """The declared commands an ExecutionBundle may contain."""
    return sorted(_ALLOWED)
