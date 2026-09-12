"""TriadCouncil LangGraph state schema definition."""

from typing import TypedDict, Optional, List, Dict, Any, Annotated
import operator


class TriadCouncilState(TypedDict, total=False):
    """
    Central state schema for the TriadCouncil LangGraph StateGraph.
    Tracks planning, deliberation, drafting, review, human gate interruption,
    and sandboxed execution evidence.
    """

    # Core Task & Reporting
    task_prompt: str
    triage_metadata: Optional[Dict[str, Any]]
    final_status_report: Optional[str]

    # Deliberative Council Phase
    manager_rfc: Optional[Dict[str, Any]]
    researcher_audit: Optional[Dict[str, Any]]
    redteam_fmea: Optional[Dict[str, Any]]
    council_round: int

    # TDD Contract & Tournament Drafting
    tdd_contract: Optional[Dict[str, str]]
    # SHA-256 of test_main.py at lock time. Downstream nodes verify against it,
    # so no node can rewrite the tests to make failing code pass.
    tdd_digest: Optional[str]
    tdd_locked: bool
    tdd_status: Optional[str]  # "LOCKED" | "INVALID"
    tdd_failure_reason: Optional[str]
    candidate_a: Optional[Dict[str, str]]
    candidate_b: Optional[Dict[str, str]]
    debate_verdict: Optional[str]
    synthesized_code: Optional[Dict[str, str]]
    # Which provider/model actually produced each artifact. Failover is never
    # silent, so attribution travels with the state.
    provider_attribution: Optional[Dict[str, str]]

    # Human Steering Gate & Execution Bundle
    execution_bundle: Optional[Dict[str, Any]]
    approval_status: Optional[str]  # "PENDING", "APPROVED", "STEERED", "ABORTED"
    human_feedback: Optional[str]

    # Sandboxed Execution & Dual-Loop Healing
    sandbox_result: Optional[Dict[str, Any]]
    repair_attempts: int
    qa_passed: bool
    qa_feedback: Optional[str]
    # True when the auditor could not be reached at all. Such a run must be
    # presented as "QA unavailable", never as a pass.
    qa_skipped: bool
    micro_repair_count: int
    macro_replan_count: int
    patch_history_hashes: Annotated[List[str], operator.add]
    last_failing_tests_count: int
    forensic_report: Optional[str]
