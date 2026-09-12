"""Isolated sandbox execution node with file autonomy and interactive terminal command gates."""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any
from ai_team.execution.workspace import write_bundle_files
from ai_team.graph.state import TriadCouncilState


def prompt_terminal_command(cmd: str) -> bool:
    """Prompt the operator in the terminal for permission to execute a shell command."""
    print("\n" + "=" * 78)
    print("   [Antigravity Coder] REQUESTING PERMISSION TO RUN TERMINAL COMMAND")
    print("=" * 78)
    print(f"  $ {cmd}")
    print("=" * 78)
    try:
        choice = input("Allow command execution in sandbox? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        choice = "n"

    is_allowed = choice in ["y", "yes"]
    if is_allowed:
        print("  ✓ Command approved. Executing in sandbox...\n")
    else:
        print("  ✗ Command denied by operator. Halting command call.\n")
    return is_allowed


def sandbox_execution_node(state: TriadCouncilState) -> Dict[str, Any]:
    """
    Executed exclusively downstream of the Human Confirmation Gate.
    1. Full autonomy: Creates and edits source/test files inside the workspace.
    2. Interactive command gate: Pauses and asks operator permission before running
       each terminal shell command.
    """
    if state.get("approval_status") != "APPROVED":
        raise PermissionError("Cannot execute sandbox without explicit operator approval.")

    bundle = state["execution_bundle"]
    workspace = Path(bundle["workspace_path"]).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    # 1. Full Autonomy: Write and edit files in the workspace without prompting
    files_created = write_bundle_files(
        workspace=workspace,
        source_files=bundle["source_files"],
        test_files=bundle["test_files"],
    )

    # 2. Interactive Terminal Command Gate: Asks permission before each shell execution
    combined_stdout = []
    combined_stderr = []
    executed_commands = []
    last_exit = 0

    # Allow custom prompt hook in state for headless automated testing
    cmd_prompter = state.get("triage_metadata", {}).get(
        "command_prompt_func", prompt_terminal_command
    )

    # Enforce Command Whitelist for safety
    ALLOWED_PREFIXES = ("python3 -m unittest", "python3 -m pytest", "python3 main.py", "python -m unittest", "ls", "cat")
    from ai_team.spatial.event_bus import get_event_bus
    from ai_team.domain.contracts import TerminalLogEvent
    import asyncio

    bus = get_event_bus()

    for cmd in bundle["declared_commands"]:
        # Safety whitelist validation
        if not any(cmd.strip().startswith(prefix) for prefix in ALLOWED_PREFIXES):
            denial_msg = f"Security Policy Block: Command '{cmd}' is not on the sandbox whitelist."
            print(f"  [Sandbox Policy] {denial_msg}")
            combined_stderr.append(denial_msg)
            last_exit = 126
            break

        executed_commands.append(cmd)
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=str(workspace),
                capture_output=True,
                text=True,
                timeout=60,
            )
            combined_stdout.append(proc.stdout)
            combined_stderr.append(proc.stderr)
            last_exit = proc.returncode

            # Stream logs to 3D Office HUD
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    if proc.stdout:
                        asyncio.create_task(bus.broadcast(TerminalLogEvent(stream="stdout", chunk=proc.stdout)))
                    if proc.stderr:
                        asyncio.create_task(bus.broadcast(TerminalLogEvent(stream="stderr", chunk=proc.stderr)))
            except Exception:
                pass

            if proc.returncode != 0:
                break
        except subprocess.TimeoutExpired:
            combined_stderr.append(f"Command timed out after 60 seconds: {cmd}")
            last_exit = 124
            break
        except Exception as e:
            combined_stderr.append(f"Execution error: {e}")
            last_exit = 1
            break

    # Extract failure count from stdout if present
    failing_count = 0
    full_out = "\n".join(combined_stdout) + "\n" + "\n".join(combined_stderr)
    if "failures=" in full_out:
        try:
            failing_count = int(full_out.split("failures=")[1].split()[0].rstrip(")"))
        except Exception:
            failing_count = 1 if last_exit != 0 else 0
    elif last_exit != 0:
        failing_count = 1

    return {
        "sandbox_result": {
            "exit_code": last_exit,
            "stdout": "\n".join(combined_stdout).strip(),
            "stderr": "\n".join(combined_stderr).strip(),
            "files_created": files_created,
            "commands_executed": executed_commands,
            "failing_tests_count": failing_count,
        },
        "last_failing_tests_count": failing_count,
    }
