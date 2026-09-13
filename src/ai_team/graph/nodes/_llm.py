"""Shared, thin provider adapters for the council nodes.

Each function does one thing: send a prompt, return text. Retry, backoff,
rate-limit visibility, quota clock-outs, and attribution all live in
`ai_team.providers.resilience`, so nodes never hand-roll a fallback chain. The
old per-node chains were the reason a run could not tell you which model had
written its code.
"""

from typing import List

from ai_team.config import AppConfig
from ai_team.providers.resilience import RoleProvider


def _groq_text(prompt: str, model: str, api_key: str, max_tokens: int) -> str:
    from langchain_groq import ChatGroq

    llm = ChatGroq(
        model_name=model,
        groq_api_key=api_key,
        temperature=0.2,
        max_tokens=max_tokens,
        request_timeout=30,
    )
    return llm.invoke(prompt).content or ""


def _openrouter_text(prompt: str, model: str, api_key: str, max_tokens: int) -> str:
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=model,
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        temperature=0.2,
        max_tokens=max_tokens,
        request_timeout=35,
    )
    return llm.invoke(prompt).content or ""


def _gemini_text(prompt: str, model: str, api_key: str, _max_tokens: int) -> str:
    from google import genai

    client = genai.Client(api_key=api_key)
    return client.models.generate_content(model=model, contents=prompt).text or ""


def _glm_text(prompt: str, model: str, api_key: str, max_tokens: int) -> str:
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=model,
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=api_key,
        temperature=0.2,
        max_tokens=max_tokens,
        request_timeout=30,
    )
    return llm.invoke(prompt).content or ""


def groq_candidate(
    config: AppConfig, prompt: str, *, model: str = "", key: str = "", max_tokens: int = 2500
) -> RoleProvider:
    resolved_model = model or config.groq_model
    resolved_key = key or config.groq_api_key
    return RoleProvider(
        label="Groq",
        provider="groq",
        model=resolved_model,
        call=lambda: _groq_text(prompt, resolved_model, resolved_key, max_tokens),
    )


def openrouter_candidate(
    config: AppConfig, prompt: str, *, max_tokens: int = 2500
) -> RoleProvider:
    return RoleProvider(
        label="OpenRouter",
        provider="openrouter",
        model=config.openrouter_model,
        call=lambda: _openrouter_text(
            prompt, config.openrouter_model, config.openrouter_api_key, max_tokens
        ),
    )


def gemini_candidate(
    config: AppConfig, prompt: str, *, max_tokens: int = 2500
) -> RoleProvider:
    return RoleProvider(
        label="Gemini",
        provider="gemini",
        model=config.gemini_researcher_model,
        call=lambda: _gemini_text(
            prompt, config.gemini_researcher_model, config.gemini_api_key, max_tokens
        ),
    )


def glm_candidate(config: AppConfig, prompt: str, *, max_tokens: int = 800) -> RoleProvider:
    key = config.zhipuai_qa_api_key or config.zhipuai_dev_api_key
    return RoleProvider(
        label="GLM",
        provider="zhipuai",
        model=config.glm_model,
        call=lambda: _glm_text(prompt, config.glm_model, key, max_tokens),
    )


def coding_candidates(config: AppConfig, prompt: str) -> List[RoleProvider]:
    """Providers able to write implementation code, in preference order."""
    candidates: List[RoleProvider] = []
    if config.groq_api_key:
        candidates.append(groq_candidate(config, prompt))
    if config.gemini_api_key:
        candidates.append(gemini_candidate(config, prompt))
    if config.openrouter_api_key:
        candidates.append(openrouter_candidate(config, prompt))
    return candidates


def authoring_candidates(config: AppConfig, prompt: str) -> List[RoleProvider]:
    """Providers for the TDD contract, which benefits from a stronger model."""
    candidates: List[RoleProvider] = []
    if config.groq_researcher_api_key:
        candidates.append(
            groq_candidate(
                config,
                prompt,
                model=config.groq_researcher_model,
                key=config.groq_researcher_api_key,
            )
        )
    if config.openrouter_api_key:
        candidates.append(openrouter_candidate(config, prompt))
    if config.gemini_api_key:
        candidates.append(gemini_candidate(config, prompt))
    return candidates
