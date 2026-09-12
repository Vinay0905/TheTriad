"""Researcher audit node (Elena).

Honesty note: this role currently runs on Groq, not on Gemini with Google
Search grounding. It reasons from model knowledge and does not perform live
retrieval, so its citations are labelled as unverified references rather than
presented as fetched sources. Wiring real grounding is tracked separately;
until then the documentation must not claim it.
"""

from typing import Any, Dict, List

from ai_team.config import get_config
from ai_team.domain.contracts import AgentStatusEvent
from ai_team.graph.state import TriadCouncilState
from ai_team.spatial.event_bus import get_event_bus

_PROMPT = (
    "You are Elena, a Principal Research Engineer. Audit the architectural "
    "approach and dependencies for this task.\n\n"
    "Task: {task}\n\n"
    "RFC summary: {summary}\n\n"
    "Produce a concise, technical audit covering:\n"
    "1. Standard library versus third-party choices, and why.\n"
    "2. Concurrency hazards: lock contention, reentrancy, races.\n"
    "3. Complexity guarantees the implementation should meet.\n"
    "4. Specific anti-patterns and gotchas to avoid.\n"
    "Where you are uncertain about a current API, say so explicitly."
)


def _announce() -> None:
    try:
        get_event_bus().dispatch(
            AgentStatusEvent(
                agent_id="researcher",
                status_text="Auditing dependencies and architectural constraints...",
                animation="Type",
            )
        )
    except Exception as err:
        print(f"  [Researcher] status dispatch skipped: {err}")


def researcher_audit_node(state: TriadCouncilState) -> Dict[str, Any]:
    """Audit the RFC for dependency and concurrency risk."""
    config = get_config()
    task = state.get("task_prompt", "")
    rfc = state.get("manager_rfc") or {}

    _announce()

    citations: List[Dict[str, str]] = []
    attribution = "none"
    findings = ""

    if config.groq_researcher_api_key:
        try:
            model = config.groq_researcher_model
            print(f"  ... [Researcher Elena / Groq {model}] Auditing approach...")
            from langchain_groq import ChatGroq

            llm = ChatGroq(
                model_name=model,
                groq_api_key=config.groq_researcher_api_key,
                temperature=0.2,
                max_tokens=1000,
                request_timeout=30,
            )
            findings = (
                llm.invoke(
                    _PROMPT.format(task=task, summary=rfc.get("summary", ""))
                ).content
                or ""
            ).strip()
            attribution = f"groq:{model}"
            citations.append(
                {
                    "title": "Python Standard Library reference (unverified, not fetched)",
                    "url": "https://docs.python.org/3/library/",
                }
            )
        except Exception as err:
            print(f"  [Researcher Elena] Groq unavailable: {err}")

    if not findings:
        findings = (
            f"No research audit was produced for '{task}'. Proceed on the "
            "manager's RFC alone and treat dependency choices as unverified."
        )

    return {
        "researcher_audit": {
            "findings": findings,
            "citations": citations,
            # There is no live retrieval in this path, so nothing here is
            # independently verified.
            "grounded": False,
            "search_performed": False,
        },
        "provider_attribution": {
            **(state.get("provider_attribution") or {}),
            "researcher_audit": attribution,
        },
    }
