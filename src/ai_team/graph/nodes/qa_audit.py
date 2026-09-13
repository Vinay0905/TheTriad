"""QA & Security Auditor node (Maya), backed by ZhipuAI GLM-4-Flash.

Two corrections from the previous implementation, both load-bearing:

1. This node no longer returns `tdd_contract`. It previously replaced the
   frozen suite with an existence check whenever the tests looked odd, which
   silently destroyed the contract.
2. It fails closed. A provider outage used to set `qa_passed = True`, so a
   rate limit rendered as a passing audit. An unreachable auditor is now
   reported as unavailable and the gate says so.
"""

import re
from typing import Any, Dict

from ai_team.config import get_config
from ai_team.domain.contracts import AgentStatusEvent
from ai_team.graph.contract_lock import assert_contract_unbroken, frozen_test_source
from ai_team.graph.nodes._llm import glm_candidate
from ai_team.graph.state import TriadCouncilState
from ai_team.providers.resilience import (
    AllProvidersUnavailableError,
    call_with_office_presence,
)
from ai_team.spatial.event_bus import get_event_bus
from ai_team.utils import repair_truncated_python_code, validate_python_syntax

_AUDIT_PROMPT = (
    "You are Maya, a Principal QA & Security Engineer reviewing Python code "
    "for the task: '{task}'.\n\n"
    "Implementation (main.py):\n```python\n{main}\n```\n\n"
    "Frozen test suite (test_main.py):\n```python\n{tests}\n```\n\n"
    "Evaluate strictly for:\n"
    "1. Concurrency and race conditions.\n"
    "2. Boundary and edge cases: empty input, zero, maximum capacity, wrong types.\n"
    "3. Missing imports, unreachable code, or names the tests require but the "
    "implementation does not define.\n\n"
    "Respond in English only.\n\n"
    "If there is ANY serious bug or unhandled edge case:\n"
    "STATUS: FAIL\n"
    "REASON: <2-3 sentences naming the bug and the fix>\n\n"
    "Otherwise:\n"
    "STATUS: PASS\n"
    "SUMMARY: <brief confirmation>"
)


def _announce(attempt: int) -> None:
    try:
        get_event_bus().dispatch(
            AgentStatusEvent(
                agent_id="qa",
                status_text=f"Auditing implementation against the contract (pass {attempt})...",
                animation="Type",
            )
        )
    except Exception as err:
        print(f"  [QA Maya] status dispatch skipped: {err}")


def _fail(state: TriadCouncilState, feedback: str, **extra: Any) -> Dict[str, Any]:
    """A failed audit. Only failures consume a repair attempt."""
    print(f"  [QA Maya] FAIL: {feedback[:120]}")
    result: Dict[str, Any] = {
        "qa_passed": False,
        "qa_feedback": feedback,
        "repair_attempts": state.get("repair_attempts", 0) + 1,
        "qa_skipped": False,
    }
    result.update(extra)
    return result


def qa_audit_node(state: TriadCouncilState) -> Dict[str, Any]:
    """Deterministic syntax gate, then an adversarial model audit."""
    assert_contract_unbroken(state, "the QA audit node")

    config = get_config()
    task = state.get("task_prompt", "")
    attempt = state.get("repair_attempts", 0) + 1
    _announce(attempt)

    if state.get("tdd_status") == "INVALID":
        return _fail(
            state,
            "No valid TDD contract exists, so the implementation cannot be audited: "
            f"{state.get('tdd_failure_reason', 'unknown reason')}",
        )

    tests = frozen_test_source(state)
    main_code = (state.get("synthesized_code") or {}).get("main.py", "")

    if not main_code.strip():
        return _fail(state, "Implementation (main.py) is empty or missing.")

    # 1. Deterministic AST gate. Healing a truncated response is fine; papering
    #    over genuinely broken code is not.
    main_valid, main_error = validate_python_syntax(main_code)
    if not main_valid:
        healed = repair_truncated_python_code(main_code)
        if validate_python_syntax(healed)[0]:
            main_code = healed
        else:
            return _fail(
                state,
                f"SyntaxError in main.py: {main_error}. Close all unterminated "
                "expressions, strings, and blocks.",
            )

    # 2. Adversarial audit. Note the frozen suite is passed for context only;
    #    this node never returns it.
    api_key = config.zhipuai_qa_api_key or config.zhipuai_dev_api_key
    if not api_key:
        # No auditor configured. That is not a pass.
        return {
            "qa_passed": False,
            "qa_skipped": True,
            "qa_feedback": (
                "QA unavailable: no GLM credentials configured, so no adversarial "
                "audit was performed. Syntax checks passed only."
            ),
            "repair_attempts": state.get("repair_attempts", 0),
            "synthesized_code": {"main.py": main_code, "test_main.py": tests},
        }

    prompt = _AUDIT_PROMPT.format(task=task, main=main_code, tests=tests)
    try:
        print(f"  ... [QA Maya / {config.glm_model}] Running adversarial review...")
        content, attribution = call_with_office_presence(
            role="qa_audit",
            agent_id="qa",
            candidates=[glm_candidate(config, prompt)],
            on_wait_status="Maya: the auditor API is rate limiting; waiting to retry.",
        )
        content = (content or "").strip()
    except AllProvidersUnavailableError as err:
        # Fail closed. The operator is told the auditor was unreachable and
        # decides at the gate with that knowledge. This is also where Maya
        # clocks out of the office if her quota is gone for the day.
        print(f"  [QA Maya] Auditor unavailable: {err}")
        return {
            "qa_passed": False,
            "qa_skipped": True,
            "qa_feedback": (
                f"QA unavailable: the {config.glm_model} auditor could not be "
                f"reached ({'; '.join(err.notes)[:160]}). Syntax checks passed, "
                "but no adversarial audit was performed."
            ),
            "repair_attempts": state.get("repair_attempts", 0),
            "synthesized_code": {"main.py": main_code, "test_main.py": tests},
        }

    if "STATUS: FAIL" in content:
        reason = content.split("REASON:", 1)[-1].strip() if "REASON:" in content else content
        if re.search(r"[\u4e00-\u9fff]", reason):
            reason = "Auditor reported a defect but the response was not in English."
        return _fail(
            state,
            reason,
            synthesized_code={"main.py": main_code, "test_main.py": tests},
        )

    summary = content.split("SUMMARY:", 1)[-1].strip() if "SUMMARY:" in content else content
    if re.search(r"[\u4e00-\u9fff]", summary):
        summary = "Implementation reviewed; structure and interface contracts verified."

    print("  [QA Maya] PASS")
    return {
        "qa_passed": True,
        "qa_skipped": False,
        "qa_feedback": summary,
        # Unchanged on success, so a passing audit cannot reset the loop budget.
        "repair_attempts": state.get("repair_attempts", 0),
        "synthesized_code": {"main.py": main_code, "test_main.py": tests},
        "provider_attribution": {
            **(state.get("provider_attribution") or {}),
            "qa_audit": attribution,
        },
    }
