"""Developer node (Alex) drafting implementation and performing iterative repair based on QA feedback."""

import os
from typing import Dict, Any
from ai_team.graph.state import TriadCouncilState
from ai_team.utils import extract_python_code
from ai_team.domain.contracts import AgentStatusEvent
from ai_team.spatial.event_bus import get_event_bus
import asyncio


def developer_node(state: TriadCouncilState) -> Dict[str, Any]:
    """
    Alex (Developer) implements main.py to satisfy the TDD contract.
    If returning from a failed QA audit, Alex reviews Maya's feedback and repairs the code.
    """
    task = state.get("task_prompt", "")
    contract = state.get("tdd_contract") or {}
    test_code = contract.get("test_main.py", "")
    attempts = state.get("repair_attempts", 0)
    qa_feedback = state.get("qa_feedback", "")
    existing_code = (state.get("synthesized_code") or {}).get("main.py", "")

    # 1. Broadcast 3D status to office
    bus = get_event_bus()
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            status_desc = "Writing implementation code..." if attempts == 0 else f"Repairing code based on QA feedback (Attempt {attempts})..."
            asyncio.create_task(
                bus.broadcast(
                    AgentStatusEvent(
                        agent_id="developer",
                        status_text=status_desc,
                        animation="Type",
                    )
                )
            )
    except Exception:
        pass

    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    dev_code = existing_code

    # Build prompt
    if attempts == 0 or not existing_code:
        prompt = (
            f"You are Alex, a Senior Software Developer. Write a complete, production-grade Python implementation in `main.py` for:\n\n"
            f"Task: {task}\n\n"
            f"Unit Test Suite Contract that your code MUST satisfy:\n```python\n{test_code}\n```\n\n"
            "Requirements:\n"
            "1. Must define all classes and functions imported by the test suite.\n"
            "2. Must handle concurrency, edge cases, and type safety.\n"
            "3. Return ONLY valid executable Python code for `main.py` enclosed in ```python markdown fences."
        )
    else:
        prompt = (
            f"You are Alex, a Senior Software Developer. Maya (QA Auditor) found issues with your previous code for:\n"
            f"Task: {task}\n\n"
            f"Previous implementation (main.py):\n```python\n{existing_code}\n```\n\n"
            f"QA Audit Feedback / Failing Issues:\n{qa_feedback}\n\n"
            f"Unit Test Suite Contract:\n```python\n{test_code}\n```\n\n"
            "Fix the identified issues and output the complete, corrected Python code for `main.py` in ```python markdown fences."
        )

    # Provider 1: Groq (LPU Speed)
    if groq_key:
        try:
            print(f"  ... [Developer Alex / Groq] Drafting implementation (Attempt {attempts + 1})...")
            from langchain_groq import ChatGroq
            groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
            llm = ChatGroq(
                model_name=groq_model,
                groq_api_key=groq_key,
                temperature=0.2,
                max_tokens=1500,
                request_timeout=25,
            )
            resp = llm.invoke(prompt)
            clean = extract_python_code(resp.content)
            if clean and len(clean) > 50:
                dev_code = clean
        except Exception as err:
            print(f"  [Developer Notice] Groq notice: {err}. Trying Gemini...")

    # Provider 2: Gemini Fallback
    if (not dev_code or len(dev_code) < 50) and gemini_key:
        try:
            print("  ... [Developer Alex / Gemini] Drafting code via secondary provider...")
            from google import genai
            client = genai.Client(api_key=gemini_key)
            resp = client.models.generate_content(
                model=os.getenv("GEMINI_RESEARCHER_MODEL", "gemini-2.5-flash"),
                contents=prompt,
            )
            clean = extract_python_code(resp.text)
            if clean:
                dev_code = clean
        except Exception as err:
            print(f"  [Developer Notice] Gemini notice: {err}. Trying OpenRouter...")

    # Provider 3: OpenRouter Fallback
    if (not dev_code or len(dev_code) < 50) and openrouter_key:
        try:
            print("  ... [Developer Alex / OpenRouter] Drafting code via fallback...")
            from langchain_openai import ChatOpenAI
            llm_router = ChatOpenAI(
                model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_key,
                temperature=0.2,
                max_tokens=1500,
                request_timeout=30,
            )
            resp = llm_router.invoke(prompt)
            clean = extract_python_code(resp.content)
            if clean:
                dev_code = clean
        except Exception as err:
            print(f"  [Developer Notice] OpenRouter notice: {err}")

    if not dev_code:
        dev_code = (
            f"'''Generated fallback for: {task}'''\n"
            "class CacheEntry:\n"
            "    def __init__(self, value, expiry):\n"
            "        self.value = value\n"
            "        self.expiry = expiry\n"
        )

    return {
        "synthesized_code": {
            "main.py": dev_code,
            "test_main.py": test_code,
        }
    }
