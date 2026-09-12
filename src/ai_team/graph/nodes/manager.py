"""Manager RFC and final status reporting nodes."""

import os
from typing import Dict, Any
from ai_team.graph.state import TriadCouncilState


def manager_rfc_node(state: TriadCouncilState) -> Dict[str, Any]:
    """
    Manager deconstructs the task into an architectural RFC and acceptance criteria.
    Incorporates human steering feedback if re-routed.
    """
    task = state["task_prompt"]
    feedback = state.get("human_feedback")

    # In live mode, invokes OpenRouter; in mock mode or fallback, uses structured RFC
    api_key = os.getenv("OPENROUTER_API_KEY")
    content = ""
    if api_key:
        try:
            print("  ... Contacting Manager via OpenRouter...")
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=os.getenv("OPENROUTER_MODEL", "nex-agi/nex-n2.5-mini:free"),
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                temperature=0.2,
                request_timeout=30,
            )
            prompt = (
                f"You are the Engineering Manager. Create an architectural RFC for this task:\n{task}\n"
            )
            if feedback:
                prompt += f"\nCRITICAL OPERATOR GUIDANCE TO INCORPORATE:\n{feedback}\n"
            prompt += (
                "\nOutput a structured summary with: approach, assumptions, and acceptance criteria."
            )
            response = llm.invoke(prompt)
            content = response.content
        except Exception as err:
            print(f"  [Manager Notice] Live OpenRouter notice: {err} -> using structured RFC fallback")
            content = f"Standard architectural plan for: {task}"
            if feedback:
                content += f" (Steered with: {feedback})"
    else:
        content = f"Standard RFC for: {task}"
        if feedback:
            content += f" (Steered with: {feedback})"

    return {
        "manager_rfc": {
            "summary": content,
            "assumptions": ["Python 3.10+ environment", "Clean modular interfaces"],
            "acceptance_criteria": [
                "Execute functional code successfully",
                "Handle edge cases and empty inputs safely",
                "Pass all unit tests with exit code 0",
            ],
            "research_required": True,
        }
    }


def manager_final_report_node(state: TriadCouncilState) -> Dict[str, Any]:
    """Compile final human-readable verification report from authentic sandbox evidence."""
    task = state["task_prompt"]
    res = state.get("sandbox_result") or {}
    bundle = state.get("execution_bundle") or {}

    exit_code = res.get("exit_code", 1)
    status_label = "SUCCESS" if exit_code == 0 else "FAILURE"

    report = (
        f"# TriadCouncil Final Report: {task}\n\n"
        f"**Execution Status**: {status_label} (Exit Code: {exit_code})\n"
        f"**Workspace**: {bundle.get('workspace_path')}\n"
        f"**Bundle Digest**: `{bundle.get('bundle_digest')}`\n"
        f"**Commands Executed**: {len(res.get('commands_executed', []))}\n"
        f"**Files Created**: {', '.join(res.get('files_created', []))}\n\n"
        f"## Observed Sandbox Output\n```\n{res.get('stdout', '')}\n```\n"
    )

    if res.get("stderr"):
        report += f"## Stderr / Warnings\n```\n{res.get('stderr')}\n```\n"

    return {"final_status_report": report}
