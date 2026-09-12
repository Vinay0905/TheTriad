"""CLI entry point running the TriadCouncil LangGraph workflow."""

import argparse
import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv
from ai_team.config import get_config
from ai_team.graph.builder import build_triad_graph
from ai_team.persistence.checkpointer import get_checkpointer

# Ensure .env is loaded
load_dotenv()


def format_cli_gate(bundle: dict) -> str:
    """Format the execution bundle presentation for human review."""
    lines = [
        "",
        "=" * 78,
        "                 TRIADCOUNCIL HUMAN STEERING GATE (interrupt)",
        "=" * 78,
        f"Task: {bundle.get('task')}",
        f"Workspace: {bundle.get('workspace_path')}",
        f"Bundle Integrity Digest (SHA-256): {bundle.get('bundle_digest')}",
        "-" * 78,
        "Files to write:",
    ]
    for filename in sorted(
        list(bundle.get("source_files", {}).keys()) + list(bundle.get("test_files", {}).keys())
    ):
        lines.append(f"  [+] {filename}")

    lines.append("-" * 78)
    verdict = bundle.get("debate_verdict")
    if verdict:
        lines.append("Council Architectural Debate & Verdict:")
        for vline in verdict.strip().splitlines():
            lines.append(f"  {vline}")
        lines.append("-" * 78)

    lines.append("Synthesized Source Code Preview (main.py):")
    main_code = bundle.get("source_files", {}).get("main.py", "")
    if main_code:
        for code_line in main_code.strip().splitlines():
            lines.append(f"    {code_line}")
    lines.append("-" * 78)
    lines.append("Declared Sandbox Commands:")
    for cmd in bundle.get("declared_commands", []):
        lines.append(f"  $ {cmd}")

    lines.append("=" * 78)
    return "\n".join(lines)


def run_cli(task: str, runs_dir: str = ".runs", mock_mode: bool = False):
    """Execute the TriadCouncil LangGraph state graph with interactive Human Gate."""
    if mock_mode:
        print("\n[TriadCouncil] Running in offline MOCK mode (simulated multi-agent council, zero API calls)")
        for key in [
            "OPENROUTER_API_KEY",
            "GEMINI_API_KEY",
            "GROQ_API_KEY",
            "ZHIPUAI_API_KEY",
            "ZHIPUAI_QA_API_KEY",
            "ZHIPUAI_DEV_API_KEY",
        ]:
            os.environ.pop(key, None)

    config = get_config()
    db_path = Path(runs_dir) / "checkpoints.db"
    checkpointer = get_checkpointer(db_path)

    app = build_triad_graph(checkpointer=checkpointer)

    thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    graph_config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 50,
    }

    print(f"\n[TriadCouncil] Initializing LangGraph run for task: '{task}'")
    print(f"[TriadCouncil] Session Thread ID: {thread_id}\n")

    initial_input = {"task_prompt": task}

    # 1. Execute up to the Human Steering Gate interrupt()
    print("--- Phase 1: Deliberation, TDD Contract & Tournament Drafting ---")
    for event in app.stream(initial_input, graph_config):
        for node_name, updates in event.items():
            if node_name == "manager_rfc_node":
                print("  ✓ [Manager] Architectural RFC & Acceptance Criteria formulated")
            elif node_name == "researcher_audit_node":
                print("  ✓ [Researcher] Search Grounding & deprecation audit complete")
            elif node_name == "redteam_fmea_node":
                print("  ✓ [QA Auditor / GLM-4-Flash] Adversarial FMEA & negative tests authored")
            elif node_name == "tdd_contract_node":
                print("  ✓ [TDD Engineer] Strict interfaces & unit test harness locked")
            elif node_name == "junior_draft_node":
                print("  ✓ [Tournament Duel] Groq (Candidate A) vs. GLM-4-Flash (Candidate B) drafted")
            elif node_name == "senior_review_node":
                print("  ✓ [Senior Dev] Reviewed candidates & synthesized hardened hybrid code")
            elif node_name == "preflight_gate_node":
                print("  ✓ [Preflight Gate] ExecutionBundle locked with SHA-256 digest")
            else:
                print(f"  ✓ Completed step: {node_name}")

    # 2. Check state at interrupt
    state_snapshot = app.get_state(graph_config)

    if state_snapshot.next:
        bundle = state_snapshot.values.get("execution_bundle", {})
        print(format_cli_gate(bundle))

        try:
            choice = input("\nEnter decision ([y] Approve / [n] Abort / [s] Steer): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = "n"

        from langgraph.types import Command

        if choice in ["y", "yes"]:
            resume_cmd = Command(resume={"action": "approve"})
            print("\n[TriadCouncil] Approved. Proceeding to sandboxed execution...")
        elif choice in ["s", "steer"]:
            guidance = input("Enter architectural steering guidance: ")
            resume_cmd = Command(resume={"action": "steer", "guidance": guidance})
            print("\n[TriadCouncil] Re-routing guidance back to Council Deliberation...")
        else:
            resume_cmd = Command(resume={"action": "abort"})
            print("\n[TriadCouncil] Execution declined. Clean abort initiated.")

        # 3. Resume from exact checkpoint
        for event in app.stream(resume_cmd, graph_config):
            for node_name in event.keys():
                print(f"  ✓ Post-gate step: {node_name}")

    # 4. Final summary
    final_snapshot = app.get_state(graph_config)
    report = final_snapshot.values.get("final_status_report")
    if report:
        print("\n" + report)


def main():
    parser = argparse.ArgumentParser(
        description="TriadCouncil: LangGraph Multi-Agent Software Engineering CLI"
    )
    parser.add_argument("task", nargs="?", help="Software engineering task prompt")
    parser.add_argument("--runs-dir", default=".runs", help="Runs and persistence directory")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in offline simulated mock mode without calling external LLM APIs",
    )
    args = parser.parse_args()

    if not args.task:
        task_input = input("Enter software engineering task: ").strip()
        if not task_input:
            print("Error: Task description cannot be empty.")
            sys.exit(1)
        args.task = task_input

    run_cli(task=args.task, runs_dir=args.runs_dir, mock_mode=args.mock)


if __name__ == "__main__":
    main()
