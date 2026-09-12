"""TDD Contract node authoring the frozen test suite before implementation exists.

Once this node returns, `test_main.py` is immutable for the rest of the run.
If no provider can produce a valid, non-vacuous suite, the run fails here. It
must never fall back to a stub that passes against anything, because the whole
value of the pipeline rests on these assertions being real.
"""

from typing import Any, Dict, Optional, Tuple

from ai_team.config import get_config
from ai_team.graph.contract_lock import freeze_contract, validate_test_contract
from ai_team.graph.state import TriadCouncilState
from ai_team.utils import (
    extract_python_code,
    repair_truncated_python_code,
)

_PROMPT = (
    "You are a Senior Software Quality Engineer authoring a strict Python unit "
    "test suite for the following task.\n\n"
    "Task: {task}\n\n"
    "Acceptance Criteria:\n{criteria}\n\n"
    "Generate a complete, executable `test_main.py` that imports from `main` "
    "(for example `from main import ...`). Use the standard `unittest` "
    "framework and cover the happy path, boundary values, and invalid input.\n\n"
    "HARD REQUIREMENTS:\n"
    "1. Every test must make an assertion that would FAIL against a wrong "
    "implementation. Existence checks such as "
    "`assertTrue(hasattr(main, '__name__'))` are forbidden and will be "
    "rejected.\n"
    "2. The code must be syntactically complete, with no unclosed strings or "
    "parentheses.\n"
    "3. Return ONLY Python code in a ```python fenced block."
)


def _criteria_text(rfc: Dict[str, Any]) -> str:
    criteria = rfc.get("acceptance_criteria", [])
    if isinstance(criteria, list):
        return "\n".join(f"- {item}" for item in criteria)
    return str(criteria)


def _candidate_from_groq(prompt: str, config) -> Tuple[Optional[str], str]:
    from langchain_groq import ChatGroq

    llm = ChatGroq(
        model_name=config.groq_researcher_model,
        groq_api_key=config.groq_researcher_api_key,
        temperature=0.2,
        max_tokens=2500,
        request_timeout=30,
    )
    response = llm.invoke(prompt)
    return response.content, f"groq:{config.groq_researcher_model}"


def _candidate_from_openrouter(prompt: str, config) -> Tuple[Optional[str], str]:
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=config.openrouter_model,
        base_url="https://openrouter.ai/api/v1",
        api_key=config.openrouter_api_key,
        temperature=0.2,
        max_tokens=2500,
        request_timeout=30,
    )
    response = llm.invoke(prompt)
    return response.content, f"openrouter:{config.openrouter_model}"


def _interfaces_from_tests(task: str, test_source: str) -> str:
    """Record the import surface the tests demand, as the implementation contract."""
    imports = [
        line
        for line in test_source.splitlines()
        if "from main import" in line or line.strip() == "import main"
    ]
    return f"'''Public interface contract for: {task}'''\n" + "\n".join(imports)


def tdd_contract_node(state: TriadCouncilState) -> Dict[str, Any]:
    """Author and freeze the test contract, or fail the run."""
    config = get_config()
    task = state.get("task_prompt", "")
    prompt = _PROMPT.format(task=task, criteria=_criteria_text(state.get("manager_rfc") or {}))

    attempts = []
    if config.groq_researcher_api_key:
        attempts.append(("Groq", _candidate_from_groq))
    if config.openrouter_api_key:
        attempts.append(("OpenRouter", _candidate_from_openrouter))

    rejections = []

    for label, call in attempts:
        try:
            print(f"  ... [TDD Engineer / {label}] Authoring frozen test contract...")
            raw, attribution = call(prompt, config)
        except Exception as err:
            rejections.append(f"{label} unavailable: {err}")
            continue

        candidate = repair_truncated_python_code(extract_python_code(raw or ""))
        is_valid, reason = validate_test_contract(candidate)
        if is_valid:
            print(f"  [TDD Engineer] Contract locked from {attribution}.")
            delta = freeze_contract(
                test_source=candidate,
                interfaces_source=_interfaces_from_tests(task, candidate),
            )
            delta["tdd_status"] = "LOCKED"
            delta["provider_attribution"] = {
                **(state.get("provider_attribution") or {}),
                "tdd_contract": attribution,
            }
            return delta

        print(f"  [TDD Engineer] Rejected {label} contract: {reason}")
        rejections.append(f"{label} rejected: {reason}")

    if not attempts:
        rejections.append("no provider credentials configured for the TDD role")

    # No stub fallback. A suite that cannot fail is worse than no suite,
    # because it manufactures a passing run out of nothing.
    reason = "; ".join(rejections)
    print(f"  [TDD Engineer] FAILED to author a valid test contract: {reason}")
    return {
        "tdd_contract": {},
        "tdd_status": "INVALID",
        "tdd_locked": False,
        "tdd_failure_reason": reason,
        "qa_passed": False,
        "qa_feedback": f"No valid TDD contract was produced: {reason}",
    }
