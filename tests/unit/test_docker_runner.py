"""The Docker runner must isolate, or refuse. It must never fall back to the host."""

import subprocess
from pathlib import Path

import pytest

from ai_team.execution.sandbox import docker_runner as runner_module
from ai_team.execution.sandbox.base import (
    EXIT_POLICY_BLOCKED,
    EXIT_SANDBOX_UNAVAILABLE,
    EXIT_TIMEOUT,
)
from ai_team.execution.sandbox.docker_runner import DockerSandboxRunner

UNITTEST_COMMAND = "python3 -m unittest test_main.py"


class _FakeCompleted:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.fixture
def recorded(monkeypatch):
    """Make docker appear present and healthy, recording every invocation."""
    calls = []

    monkeypatch.setattr(runner_module.shutil, "which", lambda _name: "/usr/bin/docker")

    def fake_run(argv, **kwargs):
        calls.append({"argv": list(argv), "kwargs": dict(kwargs)})
        if "version" in argv:
            return _FakeCompleted(stdout="27.0.3")
        if "inspect" in argv:
            return _FakeCompleted(stdout="[]")
        return _FakeCompleted(stdout="OK\nRan 2 tests\n")

    monkeypatch.setattr(runner_module.subprocess, "run", fake_run)
    return calls


def _container_call(calls):
    """The invocation that actually launched the container."""
    return next(
        call for call in calls if "run" in call["argv"] and "--rm" in call["argv"]
    )


def _run_argv(calls):
    return _container_call(calls)["argv"]


# -- refusal paths ------------------------------------------------------


def test_missing_docker_refuses_and_never_touches_the_host(monkeypatch, tmp_path):
    monkeypatch.setattr(runner_module.shutil, "which", lambda _name: None)

    def explode(*args, **kwargs):  # pragma: no cover - must not be reached
        raise AssertionError("No subprocess may run when Docker is unavailable")

    monkeypatch.setattr(runner_module.subprocess, "run", explode)

    result = DockerSandboxRunner().run(tmp_path, [UNITTEST_COMMAND], 60)

    assert result.exit_code == EXIT_SANDBOX_UNAVAILABLE
    assert "docker" in result.stderr.lower()
    assert result.commands_executed == []


def test_dead_daemon_refuses(monkeypatch, tmp_path):
    monkeypatch.setattr(runner_module.shutil, "which", lambda _name: "/usr/bin/docker")
    monkeypatch.setattr(
        runner_module.subprocess,
        "run",
        lambda *a, **k: _FakeCompleted(returncode=1, stderr="Cannot connect to daemon"),
    )

    result = DockerSandboxRunner().run(tmp_path, [UNITTEST_COMMAND], 60)

    assert result.exit_code == EXIT_SANDBOX_UNAVAILABLE
    assert result.commands_executed == []


def test_missing_image_refuses_with_a_build_hint(monkeypatch, tmp_path):
    monkeypatch.setattr(runner_module.shutil, "which", lambda _name: "/usr/bin/docker")

    def fake_run(argv, **kwargs):
        if "version" in argv:
            return _FakeCompleted(stdout="27.0.3")
        if "inspect" in argv:
            return _FakeCompleted(returncode=1, stderr="No such image")
        raise AssertionError("Must not start a container without the image")

    monkeypatch.setattr(runner_module.subprocess, "run", fake_run)

    result = DockerSandboxRunner().run(tmp_path, [UNITTEST_COMMAND], 60)

    assert result.exit_code == EXIT_SANDBOX_UNAVAILABLE
    assert "docker build" in result.stderr


def test_disallowed_command_is_blocked_before_any_container_starts(recorded, tmp_path):
    result = DockerSandboxRunner().run(
        tmp_path, ["python3 -m unittest test_main.py; rm -rf /"], 60
    )

    assert result.exit_code == EXIT_POLICY_BLOCKED
    assert result.commands_executed == []
    assert not any(
        "run" in call["argv"] and "--rm" in call["argv"] for call in recorded
    )


# -- hardening flags ----------------------------------------------------


def test_container_is_locked_down(recorded, tmp_path):
    DockerSandboxRunner().run(tmp_path, [UNITTEST_COMMAND], 60)
    argv = _run_argv(recorded)

    assert "--network=none" in argv
    assert "--read-only" in argv
    assert "--rm" in argv
    assert "no-new-privileges" in argv
    assert "ALL" in argv  # --cap-drop ALL
    assert any(item.startswith("--memory=") for item in argv)
    assert any(item.startswith("--cpus=") for item in argv)
    assert any(item.startswith("--pids-limit=") for item in argv)


def test_no_shell_is_involved(recorded, tmp_path):
    """argv execution only; a shell would give metacharacters an interpreter."""
    DockerSandboxRunner().run(tmp_path, [UNITTEST_COMMAND], 60)

    for call in recorded:
        assert call["kwargs"].get("shell") in (None, False)


def test_host_environment_is_not_forwarded(recorded, monkeypatch, tmp_path):
    """The container must not be able to see provider credentials."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_supersecretvalue000000000")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-secret")

    DockerSandboxRunner().run(tmp_path, [UNITTEST_COMMAND], 60)
    argv = _run_argv(recorded)

    joined = " ".join(argv)
    assert "gsk_supersecretvalue000000000" not in joined
    assert "sk-or-v1-secret" not in joined
    assert "GROQ_API_KEY" not in joined
    assert "OPENROUTER_API_KEY" not in joined

    # Only these three variables are intentionally set.
    passed = [argv[i + 1] for i, item in enumerate(argv) if item == "-e"]
    assert sorted(passed) == [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=/workspace",
        "PYTHONUNBUFFERED=1",
    ]


def test_only_the_workspace_is_mounted(recorded, tmp_path):
    DockerSandboxRunner().run(tmp_path, [UNITTEST_COMMAND], 60)
    argv = _run_argv(recorded)

    mounts = [argv[i + 1] for i, item in enumerate(argv) if item == "-v"]
    assert mounts == [f"{tmp_path}:/workspace:rw"]
    assert "/workspace" in argv  # -w /workspace


# -- results ------------------------------------------------------------


def test_success_is_reported_from_the_real_exit_code(recorded, tmp_path):
    result = DockerSandboxRunner().run(tmp_path, [UNITTEST_COMMAND], 60)
    assert result.exit_code == 0
    assert result.succeeded
    assert result.commands_executed == [UNITTEST_COMMAND]
    assert result.backend == "docker"


def test_failure_counts_are_parsed(monkeypatch, tmp_path):
    monkeypatch.setattr(runner_module.shutil, "which", lambda _name: "/usr/bin/docker")

    def fake_run(argv, **kwargs):
        if "version" in argv:
            return _FakeCompleted(stdout="27.0.3")
        if "inspect" in argv:
            return _FakeCompleted()
        return _FakeCompleted(returncode=1, stderr="FAILED (failures=3)")

    monkeypatch.setattr(runner_module.subprocess, "run", fake_run)

    result = DockerSandboxRunner().run(tmp_path, [UNITTEST_COMMAND], 60)
    assert result.exit_code == 1
    assert result.failing_tests_count == 3


def test_timeout_kills_the_container(monkeypatch, tmp_path):
    monkeypatch.setattr(runner_module.shutil, "which", lambda _name: "/usr/bin/docker")
    killed = []

    def fake_run(argv, **kwargs):
        if "version" in argv:
            return _FakeCompleted(stdout="27.0.3")
        if "inspect" in argv:
            return _FakeCompleted()
        if "kill" in argv:
            killed.append(argv)
            return _FakeCompleted()
        raise subprocess.TimeoutExpired(cmd=argv, timeout=1)

    monkeypatch.setattr(runner_module.subprocess, "run", fake_run)

    result = DockerSandboxRunner().run(tmp_path, [UNITTEST_COMMAND], 1)

    assert result.exit_code == EXIT_TIMEOUT
    assert result.timed_out
    assert killed, "The container must be killed when it exceeds its budget"


def test_output_is_streamed_to_the_callback(recorded, tmp_path):
    seen = []
    DockerSandboxRunner().run(
        tmp_path, [UNITTEST_COMMAND], 60, on_output=lambda s, c: seen.append((s, c))
    )
    assert any(stream == "stdout" for stream, _ in seen)


def test_availability_reports_a_reason_when_docker_is_absent(monkeypatch):
    monkeypatch.setattr(runner_module.shutil, "which", lambda _name: None)
    available, detail = DockerSandboxRunner().is_available()
    assert available is False
    assert "PATH" in detail
