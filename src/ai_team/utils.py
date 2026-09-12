"""Helper utilities for LLM code extraction and formatting."""

import re


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
