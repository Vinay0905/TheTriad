"""CLI entry point running the TriadCouncil LangGraph workflow."""

import argparse
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

from ai_team.config import get_config
from ai_team.execution.bundle import bundle_file_list
from ai_team.graph.builder import GATE_NODE, build_triad_graph
from ai_team.persistence.checkpointer import open_checkpointer

load_dotenv()

# Human-readable labels for the nodes that actually exist in the compiled
# graph. Anything not listed here is printed by its raw name, so the CLI can
# never claim a node ran that is not wired.
_NODE_LABELS: Dict[str, str] = {
    "manager_rfc_node": "[Manager] Architectural RFC and acceptance criteria drafted",
    "researcher_audit_node": "[Researcher] Dependency and concurrency audit complete",
    "tdd_contract_node": "[TDD Engineer] Test contract authored and frozen",
    "developer_node": "[Developer] Implementation drafted against the contract",
    "qa_audit_node": "[QA Auditor] Adversarial audit complete",
    "preflight_gate_node": "[Preflight] ExecutionBundle locked with SHA-256 digest",
    GATE_NODE: "[Human Gate] Awaiting operator decision",
    "sandbox_execution_node": "[Sandbox] Approved code executed in isolation",
    "manager_final_report_node": "[Manager] Final report compiled",
}


def format_cli_gate(bundle: Dict[str, Any]) -> str:
    """Render the execution bundle for human review."""
    qa_status = bundle.get("qa_status", "UNAVAILABLE")
    lines = [
        "",
        "=" * 78,
        "                 TRIADCOUNCIL HUMAN STEERING GATE (interrupt)",
        "=" * 78,
        f"Task:       {bundle.get('task')}",
        f"Thread:     {bundle.get('thread_id')}",
        f"Workspace:  {bundle.get('workspace_path')}",
        f"Digest:     {bundle.get('bundle_digest')}",
        f"QA Status:  {qa_status}",
    ]

    if qa_status != "PASS":
        lines.append("")
        lines.append(f"  !! QA did not pass. Auditor notes: {bundle.get('qa_report') or 'none'}")

    lines.append("-" * 78)
    lines.append("Files to be written:")
    for filename in bundle_file_list(bundle):
        lines.append(f"  [+] {filename}")

    attribution = bundle.get("provider_attribution") or {}
    if attribution:
        lines.append("-" * 78)
        lines.append("Produced by:")
        for artifact, model in sorted(attribution.items()):
            lines.append(f"  {artifact}: {model}")

    lines.append("-" * 78)
    lines.append("Implementation preview (main.py):")
    main_code = (bundle.get("source_files") or {}).get("main.py", "")
    for code_line in (main_code.strip() or "(empty)").splitlines():
        lines.append(f"    {code_line}")

    lines.append("-" * 78)
    lines.append("Commands to be executed in the sandbox:")
    for cmd in bundle.get("declared_commands", []):
        lines.append(f"  $ {cmd}")

    lines.append("=" * 78)
    return "\n".join(lines)


def _print_completed_nodes(event: Dict[str, Any]) -> None:
    for node_name in event:
        if node_name.startswith("__"):
            continue
        print(f"  - {_NODE_LABELS.get(node_name, node_name)}")


def _prompt_decision() -> Dict[str, Any]:
    """Ask the operator. Anything other than an explicit token aborts."""
    try:
        choice = input("\nEnter decision ([y] Approve / [n] Abort / [s] Steer): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n[TriadCouncil] No decision received. Aborting.")
        return {"action": "abort"}

    if choice in ("s", "steer"):
        try:
            guidance = input("Enter architectural steering guidance: ").strip()
        except (EOFError, KeyboardInterrupt):
            guidance = ""
        return {"action": "steer", "guidance": guidance}

    return {"action": choice}


def run_cli(task: str, runs_dir: str = ".runs", mock_mode: bool = False) -> int:
    """Run the graph, stopping at the human gate until the operator decides."""
    if mock_mode:
        print(
            "\n[TriadCouncil] MOCK mode: provider credentials are cleared, so the "
            "council will fail closed at each role. This exercises the gate and "
            "the routing, not the model output."
        )
        for key in (
            "OPENROUTER_API_KEY",
            "GEMINI_API_KEY",
            "GROQ_API_KEY",
            "GROQ_RESEARCHER_API_KEY",
            "ZHIPUAI_API_KEY",
            "ZHIPUAI_QA_API_KEY",
            "ZHIPUAI_DEV_API_KEY",
        ):
            os.environ.pop(key, None)

    get_config()
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    graph_config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 50,
    }

    print(f"\n[TriadCouncil] Task: {task!r}")
    print(f"[TriadCouncil] Thread: {thread_id}\n")

    # The checkpointer must stay open for the whole run, including across the
    # gate suspension, so the graph lives inside this context.
    with open_checkpointer(Path(runs_dir) / "checkpoints.db", durable=not mock_mode) as saver:
        app = build_triad_graph(checkpointer=saver)

        print("--- Deliberation, research, frozen contract, implementation, audit ---")
        for event in app.stream({"task_prompt": task}, graph_config):
            _print_completed_nodes(event)

        # Steering re-enters the council and returns here, so this is a loop
        # rather than a single prompt. Delivery is only reported once the graph
        # has no next node at all.
        while True:
            snapshot = app.get_state(graph_config)
            if not snapshot.next:
                break

            if GATE_NODE not in snapshot.next:
                print(f"\n[TriadCouncil] Graph paused unexpectedly at {snapshot.next}. Stopping.")
                return 1

            print(format_cli_gate(snapshot.values.get("execution_bundle") or {}))

            from langgraph.types import Command

            decision = _prompt_decision()
            if decision["action"] in ("y", "yes", "approve"):
                print("\n[TriadCouncil] Approved. Executing in the sandbox...")
            elif decision["action"] == "steer":
                print("\n[TriadCouncil] Steering guidance returned to the council...")
            else:
                print("\n[TriadCouncil] Declined. Nothing will be written or executed.")

            print("--- Post-gate ---")
            for event in app.stream(Command(resume=decision), graph_config):
                _print_completed_nodes(event)

        final_state = app.get_state(graph_config)
        report = final_state.values.get("final_status_report")
        if report:
            print("\n" + report)

        approved = final_state.values.get("approval_status") == "APPROVED"
        exit_code = (final_state.values.get("sandbox_result") or {}).get("exit_code", 1)
        return 0 if (approved and exit_code == 0) else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TriadCouncil: LangGraph multi-agent software engineering CLI"
    )
    parser.add_argument("task", nargs="?", help="Software engineering task prompt")
    parser.add_argument("--runs-dir", default=".runs", help="Runs and persistence directory")
    parser.add_argument(
        "--mock",
        action="store_true",
        help=(
            "Offline mode: clears provider credentials and uses in-memory "
            "checkpoints. The human approval gate still applies."
        ),
    )
    args = parser.parse_args()

    if not args.task:
        task_input = input("Enter software engineering task: ").strip()
        if not task_input:
            print("Error: task description cannot be empty.")
            sys.exit(1)
        args.task = task_input

    sys.exit(run_cli(task=args.task, runs_dir=args.runs_dir, mock_mode=args.mock))


if __name__ == "__main__":
    main()
