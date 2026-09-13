"""TDD Contract node: author the test suite before any implementation exists.

Once this node returns, `test_main.py` is immutable for the rest of the run.
If no provider can produce a valid, non-vacuous suite, the run fails here. It
must never fall back to a stub that passes against anything, because the whole
value of the pipeline rests on these assertions being real.
"""

from typing import Any, Dict

from ai_team.config import get_config
from ai_team.graph.contract_lock import freeze_contract, validate_test_contract
from ai_team.graph.nodes._llm import authoring_candidates
from ai_team.graph.state import TriadCouncilState
from ai_team.providers.resilience import (
    AllProvidersUnavailableError,
    InvalidModelOutput,
    RoleProvider,
    call_with_office_presence,
)
from ai_team.utils import extract_python_code, repair_truncated_python_code

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


def _interfaces_from_tests(task: str, test_source: str) -> str:
    """Record the import surface the tests demand, as the implementation contract."""
    imports = [
        line
        for line in test_source.splitlines()
        if "from main import" in line or line.strip() == "import main"
    ]
    return f"'''Public interface contract for: {task}'''\n" + "\n".join(imports)


def _validating(candidate: RoleProvider) -> RoleProvider:
    """Wrap a candidate so an unusable suite moves on to the next provider."""

    def call() -> str:
        raw = candidate.call()
        suite = repair_truncated_python_code(extract_python_code(raw or ""))
        is_valid, reason = validate_test_contract(suite)
        if not is_valid:
            # Rejected, not repaired. A suite that cannot fail is worse than
            # no suite, because it manufactures a passing run out of nothing.
            raise InvalidModelOutput(f"unusable test contract ({reason})")
        return suite

    return RoleProvider(
        label=candidate.label,
        provider=candidate.provider,
        model=candidate.model,
        call=call,
    )


def tdd_contract_node(state: TriadCouncilState) -> Dict[str, Any]:
    """Author and freeze the test contract, or fail the run."""
    config = get_config()
    task = state.get("task_prompt", "")
    prompt = _PROMPT.format(
        task=task, criteria=_criteria_text(state.get("manager_rfc") or {})
    )

    candidates = [_validating(item) for item in authoring_candidates(config, prompt)]

    try:
        suite, attribution = call_with_office_presence(
            role="tdd_contract",
            agent_id="developer",
            candidates=candidates,
            on_wait_status="Alex: provider is rate limiting the contract draft; waiting.",
        )
    except AllProvidersUnavailableError as err:
        reason = "; ".join(err.notes)
        print(f"  [TDD Engineer] FAILED to author a valid test contract: {reason}")
        return {
            "tdd_contract": {},
            "tdd_status": "INVALID",
            "tdd_locked": False,
            "tdd_failure_reason": reason,
            "qa_passed": False,
            "qa_feedback": f"No valid TDD contract was produced: {reason}",
        }

    print(f"  [TDD Engineer] Contract locked from {attribution}.")
    delta = freeze_contract(
        test_source=suite,
        interfaces_source=_interfaces_from_tests(task, suite),
    )
    delta["tdd_status"] = "LOCKED"
    delta["provider_attribution"] = {
        **(state.get("provider_attribution") or {}),
        "test_main.py": attribution,
    }
    return delta
