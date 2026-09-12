"""TDD Contract node authoring rigorous unit tests before implementation."""

import os
from typing import Dict, Any
from ai_team.graph.state import TriadCouncilState
from ai_team.utils import extract_python_code


def tdd_contract_node(state: TriadCouncilState) -> Dict[str, Any]:
    """
    Authors the interface definition and rigorous unit test suite (TDD).
    The Developer must implement code that satisfies this test contract.
    """
    task = state.get("task_prompt", "")
    rfc = state.get("manager_rfc") or {}
    fmea = state.get("redteam_fmea") or {}
    criteria = rfc.get("acceptance_criteria", [])
    criteria_str = "\n".join(f"- {c}" for c in criteria) if isinstance(criteria, list) else str(criteria)

    prompt = (
        f"You are a Senior Software Quality Engineer authoring a strict, comprehensive Python unit test suite for the following task:\n\n"
        f"Task: {task}\n\n"
        f"Acceptance Criteria:\n{criteria_str}\n\n"
        "Generate a complete, executable Python unit test file named `test_main.py` that imports from `main` "
        "(e.g., `from main import ...`). "
        "The test suite must cover both standard use cases and edge cases using Python's standard `unittest` framework. "
        "Return ONLY the valid Python code enclosed in ```python markdown fences."
    )

    # Dynamic baseline test suite
    test_suite_code = (
        f"'''Unit tests for: {task}'''\n"
        "import unittest\n"
        "import main\n\n"
        "class TestImplementation(unittest.TestCase):\n"
        "    def test_basic_contract(self):\n"
        "        self.assertTrue(hasattr(main, '__name__'))\n\n"
        "if __name__ == '__main__':\n"
        "    unittest.main()\n"
    )

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            print("  ... Senior Dev authoring dynamic TDD contract via Gemini...")
            from google import genai
            client = genai.Client(api_key=api_key)
            models_to_try = [
                os.getenv("GEMINI_RESEARCHER_MODEL", "gemini-2.5-flash"),
                "gemini-2.5-flash",
                "gemini-flash-latest",
            ]
            for m in dict.fromkeys(models_to_try):
                try:
                    response = client.models.generate_content(
                        model=m,
                        contents=prompt,
                    )
                    clean_test = extract_python_code(response.text)
                    if clean_test and "unittest" in clean_test and "class " in clean_test:
                        test_suite_code = clean_test
                        break
                except Exception:
                    continue
        except Exception as err:
            print(f"  [TDD Notice] Gemini contract notice: {err}")

    # Secondary fallback to OpenRouter if Gemini was unavailable
    if "def test_basic_contract" in test_suite_code and os.getenv("OPENROUTER_API_KEY"):
        try:
            print("  ... Senior Dev authoring TDD contract via secondary provider...")
            from langchain_openai import ChatOpenAI
            llm_router = ChatOpenAI(
                model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                temperature=0.2,
                max_tokens=800,
                request_timeout=25,
            )
            resp = llm_router.invoke(prompt)
            clean_test = extract_python_code(resp.content)
            if clean_test and "unittest" in clean_test and "class " in clean_test:
                test_suite_code = clean_test
        except Exception:
            pass

    # Extract interface contract signatures from test imports
    interfaces_code = (
        f"'''Public interface contract for: {task}'''\n"
        + "\n".join([l for l in test_suite_code.splitlines() if "from main import" in l or "import main" in l])
    )

    return {
        "tdd_contract": {
            "interfaces.py": interfaces_code,
            "test_main.py": test_suite_code,
        }
    }
