"""Sanitization and redaction of sensitive credentials in logs and audit trails."""

import os
import re
from typing import Any, Dict, List, Union

# Common key prefixes (Groq, OpenRouter, Google AI Studio, OpenAI, Anthropic)
SECRET_PATTERNS = [
    re.compile(r"gsk_[a-zA-Z0-9]{20,}"),
    re.compile(r"sk-or-v1-[a-zA-Z0-9]{30,}"),
    re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    # ZhipuAI GLM keys are an id and secret joined by a dot.
    re.compile(r"\b[0-9a-f]{32}\.[A-Za-z0-9]{16,}\b"),
    # LangSmith / LangChain tracing keys.
    re.compile(r"lsv2_(?:pt|sk)_[a-zA-Z0-9]{20,}"),
]

# Every provider variable whose literal value must never reach a log, a
# WebSocket frame, or a run manifest.
SECRET_ENV_VARS = [
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "GROQ_RESEARCHER_API_KEY",
    "ZHIPUAI_API_KEY",
    "ZHIPUAI_DEV_API_KEY",
    "ZHIPUAI_QA_API_KEY",
    "LANGSMITH_API_KEY",
]


def redact_secrets(text: str) -> str:
    """Redact known API key patterns and configured environment secret values from text."""
    if not text:
        return text

    redacted = text

    # Redact explicit regex patterns
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_API_KEY]", redacted)

    # Redact any non-empty active env secrets
    for env_var in SECRET_ENV_VARS:
        val = os.getenv(env_var, "").strip()
        if len(val) > 6:
            redacted = redacted.replace(val, "[REDACTED_SECRET]")

    return redacted


def sanitize_dict(data: Union[Dict[str, Any], List[Any], str]) -> Any:
    """Recursively sanitize dictionary or list values."""
    if isinstance(data, str):
        return redact_secrets(data)
    elif isinstance(data, dict):
        return {k: sanitize_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_dict(item) for item in data]
    return data
