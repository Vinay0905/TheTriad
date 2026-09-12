"""Docker-backed sandbox runner.

The container is locked down along every axis the approved payload does not
need: no network, no new privileges, no capabilities, a read-only root
filesystem, a bounded CPU/memory/pid budget, and a non-root user. Crucially,
**no host environment is forwarded**, so API keys cannot leak into code the
operator just approved.

If Docker is missing, the daemon is down, or the image is not built, this
runner reports that and runs nothing. There is no host fallback.
"""

import shutil
import subprocess
import uuid
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from ai_team.config import get_config
from ai_team.execution.sandbox.allowlist import CommandNotAllowedError, resolve_argv
from ai_team.execution.sandbox.base import (
    EXIT_POLICY_BLOCKED,
    EXIT_SANDBOX_UNAVAILABLE,
    EXIT_TIMEOUT,
    OutputCallback,
    SandboxResult,
    parse_failing_tests,
)

_BUILD_HINT = (
    "Build it once with: "
    "docker build -t {image} -f docker/sandbox.Dockerfile docker/"
)


class DockerSandboxRunner:
    """Runs approved commands inside a locked-down container."""

    name = "docker"

    def __init__(self, config=None) -> None:
        self._config = config or get_config()

    # -- availability ----------------------------------------------------

    def _docker_path(self) -> Optional[str]:
        return shutil.which("docker")

    def is_available(self) -> Tuple[bool, str]:
        docker = self._docker_path()
        if not docker:
            return False, "The `docker` executable is not on PATH."

        try:
            probe = subprocess.run(
                [docker, "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                timeout=20,
            )
        except subprocess.TimeoutExpired:
            return False, "The Docker daemon did not respond within 20s."
        except OSError as err:
            return False, f"Could not invoke Docker: {err}"

        if probe.returncode != 0:
            detail = (probe.stderr or probe.stdout or "").strip()
            return False, f"The Docker daemon is not reachable: {detail}"

        return True, f"Docker server {probe.stdout.strip()}"

    def _image_present(self, docker: str) -> bool:
        try:
            probe = subprocess.run(
                [docker, "image", "inspect", self._config.sandbox_image],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (subprocess.TimeoutExpired, OSError):
            return False
        return probe.returncode == 0

    # -- execution -------------------------------------------------------

    def _docker_argv(self, container_name: str, workspace: Path, argv: Sequence[str]) -> List[str]:
        config = self._config
        return [
            self._docker_path() or "docker",
            "run",
            "--rm",
            "--name",
            container_name,
            # No egress. Approved test code has no business calling out.
            "--network=none",
            f"--cpus={config.sandbox_cpus}",
            f"--memory={config.sandbox_memory}",
            f"--pids-limit={config.sandbox_pids_limit}",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--security-opt",
            "no-new-privileges",
            "--cap-drop",
            "ALL",
            "--user",
            config.sandbox_uid,
            "-v",
            f"{workspace}:/workspace:rw",
            "-w",
            "/workspace",
            # Only these three variables are set. The host environment, and
            # therefore every API key, is deliberately not forwarded.
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
            "-e",
            "PYTHONUNBUFFERED=1",
            "-e",
            "PYTHONPATH=/workspace",
            config.sandbox_image,
            *argv,
        ]

    def _kill(self, container_name: str) -> None:
        docker = self._docker_path()
        if not docker:
            return
        try:
            subprocess.run(
                [docker, "kill", container_name],
                capture_output=True,
                text=True,
                timeout=20,
            )
        except (subprocess.TimeoutExpired, OSError):
            pass

    def run(
        self,
        workspace: Path,
        declared_commands: Sequence[str],
        timeout_seconds: int,
        on_output: Optional[OutputCallback] = None,
    ) -> SandboxResult:
        def emit(stream: str, chunk: str) -> None:
            if chunk and on_output:
                try:
                    on_output(stream, chunk)
                except Exception as err:
                    print(f"  [Sandbox] output callback failed: {err}")

        available, detail = self.is_available()
        if not available:
            message = (
                f"Execution refused: Docker isolation is required but unavailable. {detail} "
                "No code was run on the host."
            )
            emit("stderr", message)
            return SandboxResult(
                exit_code=EXIT_SANDBOX_UNAVAILABLE,
                stderr=message,
                backend=self.name,
            )

        docker = self._docker_path() or "docker"
        if not self._image_present(docker):
            message = (
                f"Execution refused: sandbox image {self._config.sandbox_image!r} is not "
                "present. " + _BUILD_HINT.format(image=self._config.sandbox_image)
            )
            emit("stderr", message)
            return SandboxResult(
                exit_code=EXIT_SANDBOX_UNAVAILABLE,
                stderr=message,
                backend=self.name,
            )

        stdout_parts: List[str] = []
        stderr_parts: List[str] = []
        executed: List[str] = []
        exit_code = 0

        for declared in declared_commands:
            try:
                argv = resolve_argv(declared)
            except CommandNotAllowedError as err:
                message = f"Security policy block: {err}"
                print(f"  [Sandbox Policy] {message}")
                stderr_parts.append(message)
                emit("stderr", message)
                exit_code = EXIT_POLICY_BLOCKED
                break

            container_name = f"triad-{uuid.uuid4().hex[:12]}"
            command_argv = self._docker_argv(container_name, workspace, argv)
            print(f"  [Sandbox/docker] $ {' '.join(argv)}")

            try:
                completed = subprocess.run(
                    command_argv,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                )
            except subprocess.TimeoutExpired:
                self._kill(container_name)
                message = (
                    f"Command timed out after {timeout_seconds}s and the container "
                    "was killed: " + declared
                )
                stderr_parts.append(message)
                emit("stderr", message)
                executed.append(declared)
                return SandboxResult(
                    exit_code=EXIT_TIMEOUT,
                    stdout="\n".join(stdout_parts),
                    stderr="\n".join(stderr_parts),
                    commands_executed=executed,
                    timed_out=True,
                    backend=self.name,
                )
            except OSError as err:
                message = f"Could not start the sandbox container: {err}"
                stderr_parts.append(message)
                emit("stderr", message)
                exit_code = EXIT_SANDBOX_UNAVAILABLE
                break

            executed.append(declared)
            if completed.stdout:
                stdout_parts.append(completed.stdout)
                emit("stdout", completed.stdout)
            if completed.stderr:
                stderr_parts.append(completed.stderr)
                emit("stderr", completed.stderr)

            exit_code = completed.returncode
            if exit_code != 0:
                break

        combined = "\n".join(stdout_parts) + "\n" + "\n".join(stderr_parts)
        failing = parse_failing_tests(combined)
        if failing == 0 and exit_code != 0:
            failing = 1

        return SandboxResult(
            exit_code=exit_code,
            stdout="\n".join(stdout_parts),
            stderr="\n".join(stderr_parts),
            commands_executed=executed,
            failing_tests_count=failing,
            backend=self.name,
        )
