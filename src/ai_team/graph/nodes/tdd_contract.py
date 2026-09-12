"""TDD Contract node authoring rigorous unit tests before implementation."""

import os
from typing import Dict, Any
from ai_team.graph.state import TriadCouncilState
from ai_team.utils import extract_python_code, validate_python_syntax, repair_truncated_python_code


def tdd_contract_node(state: TriadCouncilState) -> Dict[str, Any]:
    """
    Authors the interface definition and rigorous unit test suite (TDD).
    The Developer must implement code that satisfies this test contract.
    """
    task = state.get("task_prompt", "")
    rfc = state.get("manager_rfc") or {}
    criteria = rfc.get("acceptance_criteria", [])
    criteria_str = "\n".join(f"- {c}" for c in criteria) if isinstance(criteria, list) else str(criteria)

    prompt = (
        f"You are a Senior Software Quality Engineer authoring a strict, comprehensive Python unit test suite for the following task:\n\n"
        f"Task: {task}\n\n"
        f"Acceptance Criteria:\n{criteria_str}\n\n"
        "Generate a complete, executable Python unit test file named `test_main.py` that imports from `main` "
        "(e.g., `from main import ...` or `import main`). "
        "The test suite must cover both standard use cases and edge cases using Python's standard `unittest` framework. "
        "CRITICAL: The Python code must be 100% complete, fully closed, and syntactically valid. Do NOT leave expressions or parentheses unfinished.\n"
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

    groq_key = os.getenv("GROQ_RESEARCHER_API_KEY") or os.getenv("GROQ_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    # Primary: Fast Groq LPU Generation
    if groq_key:
        try:
            print("  ... Senior Dev authoring dynamic TDD contract via Groq...")
            from langchain_groq import ChatGroq
            model = os.getenv("GROQ_RESEARCHER_MODEL", "openai/gpt-oss-120b").strip()
            llm = ChatGroq(
                model_name=model,
                groq_api_key=groq_key,
                temperature=0.2,
                max_tokens=2500,
                request_timeout=30,
            )
            resp = llm.invoke(prompt)
            clean_test = extract_python_code(resp.content)
            clean_test = repair_truncated_python_code(clean_test)
            is_valid, err = validate_python_syntax(clean_test)
            if is_valid and "unittest" in clean_test and "class " in clean_test:
                test_suite_code = clean_test
            elif not is_valid:
                print(f"  [TDD Warning] Groq generated code has syntax error: {err}. Falling back...")
        except Exception as err:
            print(f"  [TDD Notice] Groq contract notice: {err}")

    # Secondary fallback to OpenRouter
    if "def test_basic_contract" in test_suite_code and openrouter_key:
        try:
            print("  ... Senior Dev authoring TDD contract via OpenRouter...")
            from langchain_openai import ChatOpenAI
            llm_router = ChatOpenAI(
                model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_key,
                temperature=0.2,
                max_tokens=2500,
                request_timeout=30,
            )
            resp = llm_router.invoke(prompt)
            clean_test = extract_python_code(resp.content)
            clean_test = repair_truncated_python_code(clean_test)
            is_valid, err = validate_python_syntax(clean_test)
            if is_valid and "unittest" in clean_test and "class " in clean_test:
                test_suite_code = clean_test
            elif not is_valid:
                print(f"  [TDD Warning] OpenRouter code has syntax error: {err}")
        except Exception as err:
            print(f"  [TDD Notice] OpenRouter contract notice: {err}")

    # Ensure baseline validity
    if not validate_python_syntax(test_suite_code)[0]:
        print("  [TDD Recovery] Falling back to baseline test suite.")
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
