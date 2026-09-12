import ast
import re
from typing import Tuple


def extract_python_code(text: str) -> str:
    """
    Extract pure executable Python code from an LLM response.
    Handles ```python code blocks, generic markdown fences, and raw code.
    """
    if not text or not isinstance(text, str):
        return ""

    text = text.strip()

    # Match ```python ... ```
    match = re.search(r"```(?:python|py)\s*\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Match generic ``` ... ```
    match = re.search(r"```\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Clean any loose fences
    cleaned_lines = []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def validate_python_syntax(code: str) -> Tuple[bool, str]:
    """
    Validate whether code is syntactically valid Python using ast.parse.
    Returns (True, "") if valid, or (False, error_description) if invalid.
    """
    if not code or not code.strip():
        return False, "Code is empty"
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as err:
        return False, f"SyntaxError at line {err.lineno}, col {err.offset}: {err.msg}"
    except Exception as err:
        return False, f"Parse error: {err}"


def repair_truncated_python_code(code: str) -> str:
    """
    Attempts to heal truncated Python code caused by LLM token limit cutoffs.
    Trims trailing incomplete statements and re-validates syntax.
    """
    code = code.strip()
    is_valid, _ = validate_python_syntax(code)
    if is_valid:
        return code

    lines = code.splitlines()
    for i in range(len(lines) - 1, max(0, len(lines) - 30), -1):
        candidate = "\n".join(lines[:i]).strip()
        is_cand_valid, _ = validate_python_syntax(candidate)
        if is_cand_valid:
            if "unittest.TestCase" in candidate and "__main__" not in candidate:
                with_runner = candidate + "\n\nif __name__ == '__main__':\n    unittest.main()\n"
                if validate_python_syntax(with_runner)[0]:
                    return with_runner
            return candidate

        if "unittest.TestCase" in candidate:
            candidate_with_footer = candidate + "\n\nif __name__ == '__main__':\n    unittest.main()\n"
            if validate_python_syntax(candidate_with_footer)[0]:
                return candidate_with_footer

    return code

