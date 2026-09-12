"""Human Confirmation Gate enforcing immutable safety boundary prior to execution."""

import sys
from typing import Callable, Optional
from ai_team.domain.contracts import ExecutionBundle


def format_approval_summary(bundle: ExecutionBundle) -> str:
    """Format an informative, clear summary of the execution proposal for the human operator."""
    lines = [
        "",
        "=" * 78,
        "                     PROPOSED EXECUTION BUNDLE REVIEW",
        "=" * 78,
        f"Task: {bundle.task}",
        f"Target Workspace: {bundle.workspace_path}",
        f"Bundle Integrity Digest (SHA-256): {bundle.bundle_digest}",
        "-" * 78,
        "Acceptance Criteria:",
    ]
    for ac in bundle.acceptance_criteria:
        lines.append(f"  • {ac}")

    lines.append("-" * 78)
    lines.append("Files to be written:")
    for path, content in {**bundle.source_files, **bundle.test_files}.items():
        lines.append(f"  [+] {path} ({len(content.splitlines())} lines)")

    lines.append("-" * 78)
    lines.append("Commands to be executed in sandbox:")
    for cmd in bundle.declared_commands:
        lines.append(f"  $ {cmd}")

    lines.append("=" * 78)
    return "\n".join(lines)


def prompt_human_approval(
    bundle: ExecutionBundle,
    input_func: Optional[Callable[[str], str]] = None,
    output_func: Optional[Callable[[str], None]] = None,
) -> bool:
    """
    Present the execution bundle to the human and request confirmation.
    Returns True ONLY if user explicitly responds with 'y' or 'yes'.
    Treats any other input, EOF, or blank as rejection (fail closed).
    """
    _input = input_func or input
    _print = output_func or print

    summary_text = format_approval_summary(bundle)
    _print(summary_text)

    try:
        response = _input("\nProceed with execution in sandbox? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        _print("\nConfirmation interrupted. Aborting pipeline.")
        return False

    is_approved = response in {"y", "yes"}
    if not is_approved:
        _print("\nExecution declined by user. Pipeline halted with zero side effects.")
    else:
        _print("\nExecution approved by user. Proceeding to sandboxed execution.")

    return is_approved
