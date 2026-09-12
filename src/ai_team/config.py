"""Centralized configuration for TriadCouncil multi-agent system."""

from dataclasses import dataclass, field
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present in workspace root
load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    """Application configuration with environment variable overrides."""

    # Provider API Keys
    openrouter_api_key: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY", "")
    )
    gemini_api_key: str = field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY", "")
    )
    groq_api_key: str = field(
        default_factory=lambda: os.getenv("GROQ_API_KEY", "")
    )
    # ZhipuAI GLM-4-Flash Keys (Free tier)
    zhipuai_dev_api_key: str = field(
        default_factory=lambda: os.getenv(
            "ZHIPUAI_DEV_API_KEY", os.getenv("ZHIPUAI_API_KEY", "")
        )
    )
    zhipuai_qa_api_key: str = field(
        default_factory=lambda: os.getenv(
            "ZHIPUAI_QA_API_KEY", os.getenv("ZHIPUAI_API_KEY", "")
        )
    )

    # Provider Models
    openrouter_model: str = field(
        default_factory=lambda: os.getenv(
            "OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"
        )
    )
    gemini_researcher_model: str = field(
        default_factory=lambda: os.getenv(
            "GEMINI_RESEARCHER_MODEL", "gemini-2.5-flash"
        )
    )
    groq_model: str = field(
        default_factory=lambda: os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    )
    glm_model: str = field(
        default_factory=lambda: os.getenv("GLM_MODEL", "glm-4-flash")
    )

    # Operational & Execution Paths
    runs_dir: Path = field(
        default_factory=lambda: Path(os.getenv("AI_TEAM_RUNS_DIR", ".runs"))
    )
    execution_timeout_seconds: int = field(
        default_factory=lambda: int(
            os.getenv("AI_TEAM_EXECUTION_TIMEOUT_SECONDS", "120")
        )
    )
    max_retry_attempts: int = field(
        default_factory=lambda: int(
            os.getenv("AI_TEAM_MAX_RETRY_ATTEMPTS", "2")
        )
    )
    server_host: str = field(
        default_factory=lambda: os.getenv("AI_TEAM_SERVER_HOST", "0.0.0.0")
    )
    server_port: int = field(
        default_factory=lambda: int(os.getenv("AI_TEAM_SERVER_PORT", "8000"))
    )


def get_config() -> AppConfig:
    """Retrieve an immutable AppConfig instance."""
    return AppConfig()
