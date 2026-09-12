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
    groq_researcher_api_key: str = field(
        default_factory=lambda: os.getenv(
            "GROQ_RESEARCHER_API_KEY", os.getenv("GROQ_API_KEY", "")
        )
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
    groq_researcher_model: str = field(
        default_factory=lambda: os.getenv(
            "GROQ_RESEARCHER_MODEL", "openai/gpt-oss-120b"
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
    # Bind to loopback by default. This is a single-operator cockpit, not a
    # service; exposing the approval gate on 0.0.0.0 is not a safe default.
    server_host: str = field(
        default_factory=lambda: os.getenv("AI_TEAM_SERVER_HOST", "127.0.0.1")
    )
    server_port: int = field(
        default_factory=lambda: int(os.getenv("AI_TEAM_SERVER_PORT", "8000"))
    )
    server_reload: bool = field(
        default_factory=lambda: os.getenv("AI_TEAM_SERVER_RELOAD", "0").lower()
        in ("1", "true", "yes")
    )

    # --- Sandbox isolation -------------------------------------------------
    # Selector for the SandboxRunner implementation. "docker" is the only
    # backend wired today; "e2b" is reserved so the graph never needs changing.
    sandbox_backend: str = field(
        default_factory=lambda: os.getenv("AI_TEAM_SANDBOX", "docker")
    )
    sandbox_image: str = field(
        default_factory=lambda: os.getenv(
            "AI_TEAM_SANDBOX_IMAGE", "triadcouncil-sandbox:py312"
        )
    )
    # Bind-mount ownership differs between Linux and macOS virtiofs, so the
    # container uid must be overridable without a code change.
    sandbox_uid: str = field(
        default_factory=lambda: os.getenv("AI_TEAM_SANDBOX_UID", "65534:65534")
    )
    sandbox_memory: str = field(
        default_factory=lambda: os.getenv("AI_TEAM_SANDBOX_MEMORY", "512m")
    )
    sandbox_cpus: str = field(
        default_factory=lambda: os.getenv("AI_TEAM_SANDBOX_CPUS", "1")
    )
    sandbox_pids_limit: int = field(
        default_factory=lambda: int(os.getenv("AI_TEAM_SANDBOX_PIDS_LIMIT", "128"))
    )

    # --- Provider resilience ----------------------------------------------
    provider_max_retries: int = field(
        default_factory=lambda: int(os.getenv("AI_TEAM_PROVIDER_MAX_RETRIES", "3"))
    )
    provider_backoff_base_seconds: float = field(
        default_factory=lambda: float(
            os.getenv("AI_TEAM_PROVIDER_BACKOFF_BASE_SECONDS", "2.0")
        )
    )
    provider_backoff_max_seconds: float = field(
        default_factory=lambda: float(
            os.getenv("AI_TEAM_PROVIDER_BACKOFF_MAX_SECONDS", "30.0")
        )
    )
    # How long a role stays clocked out after a hard quota error, when the
    # provider gives us no explicit reset hint.
    provider_quota_cooldown_seconds: int = field(
        default_factory=lambda: int(
            os.getenv("AI_TEAM_PROVIDER_QUOTA_COOLDOWN_SECONDS", "3600")
        )
    )

    # --- Observability ----------------------------------------------------
    langsmith_tracing: bool = field(
        default_factory=lambda: os.getenv("LANGSMITH_TRACING", "").lower()
        in ("1", "true", "yes")
    )
    langsmith_api_key: str = field(
        default_factory=lambda: os.getenv("LANGSMITH_API_KEY", "")
    )
    langsmith_project: str = field(
        default_factory=lambda: os.getenv("LANGSMITH_PROJECT", "triadcouncil")
    )

    # --- Office simulation -------------------------------------------------
    workday_real_seconds: int = field(
        default_factory=lambda: int(os.getenv("AI_TEAM_WORKDAY_REAL_SECONDS", "1200"))
    )
    off_hours_real_seconds: int = field(
        default_factory=lambda: int(os.getenv("AI_TEAM_OFF_HOURS_REAL_SECONDS", "1200"))
    )
    # Terminal log retention, so a long run cannot grow memory without bound.
    terminal_log_limit: int = field(
        default_factory=lambda: int(os.getenv("AI_TEAM_TERMINAL_LOG_LIMIT", "500"))
    )


def get_config() -> AppConfig:
    """Retrieve an immutable AppConfig instance."""
    return AppConfig()
