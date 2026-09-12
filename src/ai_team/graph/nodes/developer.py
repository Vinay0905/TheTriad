"""Developer node (Alex): implement main.py against the frozen test contract.

Two rules shape this node:

1. It may only produce `main.py`. The test suite is frozen upstream, and this
   node's return value is filtered so it cannot touch it even by accident.
2. There is no stub fallback. If every provider fails, the node reports that
   honestly and lets QA fail the run, rather than shipping a Hello World that
   makes the pipeline look successful.
"""

from typing import Any, Dict, Optional, Tuple

from ai_team.config import get_config
from ai_team.domain.contracts import AgentStatusEvent
from ai_team.graph.contract_lock import assert_contract_unbroken, frozen_test_source
from ai_team.graph.state import TriadCouncilState
from ai_team.spatial.event_bus import get_event_bus
from ai_team.utils import (
    extract_python_code,
    repair_truncated_python_code,
    validate_python_syntax,
)

_DRAFT_PROMPT = (
    "You are Alex, a Senior Software Developer. Write a complete Python "
    "implementation in `main.py` for:\n\n"
    "Task: {task}\n\n"
    "It must satisfy this frozen unit test suite exactly. You may not change "
    "the tests.\n```python\n{tests}\n```\n\n"
    "Requirements:\n"
    "1. Define every class, function, and name the test suite imports.\n"
    "2. Handle edge cases, invalid input, and concurrency where relevant.\n"
    "3. The code must be syntactically complete and valid.\n"
    "4. Return ONLY the Python code for `main.py` in a ```python block."
)

_REPAIR_PROMPT = (
    "You are Alex, a Senior Software Developer. Maya (QA) rejected your "
    "implementation for:\n\nTask: {task}\n\n"
    "Your previous `main.py`:\n```python\n{previous}\n```\n\n"
    "QA findings you must fix:\n{feedback}\n\n"
    "The frozen test suite, which you may not change:\n```python\n{tests}\n```\n\n"
    "Return the complete corrected `main.py` in a ```python block."
)


def _from_groq(prompt: str, config) -> Tuple[str, str]:
    from langchain_groq import ChatGroq

    llm = ChatGroq(
        model_name=config.groq_model,
        groq_api_key=config.groq_api_key,
        temperature=0.2,
        max_tokens=2500,
        request_timeout=30,
    )
    return llm.invoke(prompt).content, f"groq:{config.groq_model}"


def _from_gemini(prompt: str, config) -> Tuple[str, str]:
    from google import genai

    client = genai.Client(api_key=config.gemini_api_key)
    response = client.models.generate_content(
        model=config.gemini_researcher_model,
        contents=prompt,
    )
    return response.text, f"gemini:{config.gemini_researcher_model}"


def _from_openrouter(prompt: str, config) -> Tuple[str, str]:
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=config.openrouter_model,
        base_url="https://openrouter.ai/api/v1",
        api_key=config.openrouter_api_key,
        temperature=0.2,
        max_tokens=2500,
        request_timeout=35,
    )
    return llm.invoke(prompt).content, f"openrouter:{config.openrouter_model}"


def _announce(attempts: int) -> None:
    status = (
        "Writing implementation against the frozen contract..."
        if attempts == 0
        else f"Repairing implementation from QA findings (attempt {attempts})..."
    )
    try:
        get_event_bus().dispatch(
            AgentStatusEvent(agent_id="developer", status_text=status, animation="Type")
        )
    except Exception as err:  # never let choreography break the pipeline
        print(f"  [Developer] status dispatch skipped: {err}")


def developer_node(state: TriadCouncilState) -> Dict[str, Any]:
    """Draft or repair `main.py`. Never touches the test suite."""
    assert_contract_unbroken(state, "the developer node")

    config = get_config()
    task = state.get("task_prompt", "")
    tests = frozen_test_source(state)
    attempts = state.get("repair_attempts", 0)
    previous = (state.get("synthesized_code") or {}).get("main.py", "")

    _announce(attempts)

    if attempts == 0 or not previous:
        prompt = _DRAFT_PROMPT.format(task=task, tests=tests)
    else:
        prompt = _REPAIR_PROMPT.format(
            task=task,
            previous=previous,
            feedback=state.get("qa_feedback", "(no feedback recorded)"),
            tests=tests,
        )

    providers = []
    if config.groq_api_key:
        providers.append(("Groq", _from_groq))
    if config.gemini_api_key:
        providers.append(("Gemini", _from_gemini))
    if config.openrouter_api_key:
        providers.append(("OpenRouter", _from_openrouter))

    code: Optional[str] = None
    attribution = "none"
    notes = []

    for label, call in providers:
        try:
            print(f"  ... [Developer Alex / {label}] Drafting implementation...")
            raw, attribution_candidate = call(prompt, config)
        except Exception as err:
            notes.append(f"{label} unavailable: {err}")
            continue

        candidate = repair_truncated_python_code(extract_python_code(raw or ""))
        is_valid, syntax_error = validate_python_syntax(candidate)
        if is_valid and candidate.strip():
            code = candidate
            attribution = attribution_candidate
            break

        notes.append(f"{label} produced invalid Python: {syntax_error}")

    if code is None:
        # Deliberately no Hello World stub: an empty implementation fails QA,
        # which is the truthful outcome.
        reason = "; ".join(notes) or "no provider credentials configured"
        print(f"  [Developer Alex] No usable implementation produced: {reason}")
        return {
            "synthesized_code": {"main.py": "", "test_main.py": tests},
            "provider_attribution": {
                **(state.get("provider_attribution") or {}),
                "main.py": "none",
            },
            "qa_feedback": f"Developer produced no valid implementation: {reason}",
        }

    print(f"  [Developer Alex] Implementation drafted by {attribution}.")
    return {
        # test_main.py is copied verbatim from the frozen contract so the
        # packaged bundle is complete, never regenerated.
        "synthesized_code": {"main.py": code, "test_main.py": tests},
        "provider_attribution": {
            **(state.get("provider_attribution") or {}),
            "main.py": attribution,
        },
    }
