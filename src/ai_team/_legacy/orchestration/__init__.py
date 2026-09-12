"""Orchestration engine, bundle management, and human confirmation gate."""

from ai_team._legacy.orchestration.bundle import (
    create_execution_bundle,
    compute_bundle_digest,
    verify_bundle_integrity,
    BundleTamperError,
)
from ai_team._legacy.orchestration.approval import format_approval_summary, prompt_human_approval
from ai_team._legacy.orchestration.state_machine import OrchestrationRun

__all__ = [
    "create_execution_bundle",
    "compute_bundle_digest",
    "verify_bundle_integrity",
    "BundleTamperError",
    "format_approval_summary",
    "prompt_human_approval",
    "OrchestrationRun",
]
