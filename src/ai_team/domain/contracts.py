"""Pydantic data contracts for inter-role message validation and audit trails."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TaskPlan(BaseModel):
    """Manager's structured task plan and requirement decomposition."""

    summary: str = Field(description="Executive summary of the task plan")
    assumptions: List[str] = Field(default_factory=list, description="Explicit assumptions")
    acceptance_criteria: List[str] = Field(
        min_length=1, description="Measurable criteria defining task completion"
    )
    research_required: bool = Field(
        default=False,
        description="Whether live web search grounding is needed before drafting",
    )
    research_questions: List[str] = Field(
        default_factory=list, description="Specific questions for the Researcher"
    )


class Citation(BaseModel):
    """Web source cited by Researcher during grounding."""

    title: str = Field(description="Title of the web source")
    url: str = Field(description="URL of the cited source")


class ResearchFindings(BaseModel):
    """Researcher's grounded facts retrieved via Gemini Search tool."""

    topic: str = Field(description="Research subject")
    findings: List[str] = Field(default_factory=list, description="Key verified facts")
    citations: List[Citation] = Field(default_factory=list, description="Cited references")
    gotchas: List[str] = Field(
        default_factory=list, description="Known deprecations, bugs, or version constraints"
    )


class CodeDraft(BaseModel):
    """Junior Dev's initial code and proposed test suite."""

    source_files: Dict[str, str] = Field(
        min_length=1, description="Mapping of relative filename to source code"
    )
    test_files: Dict[str, str] = Field(
        default_factory=dict, description="Mapping of test filename to unit test code"
    )
    implementation_notes: str = Field(
        default="", description="Technical rationale, limitations, and assumptions"
    )


class ReviewResult(BaseModel):
    """Senior Dev's read-only review and finalized execution bundle."""

    approved: bool = Field(description="Whether the draft meets standards")
    critique: str = Field(description="Detailed code review critique")
    finalized_source_files: Dict[str, str] = Field(
        min_length=1, description="Hardened and finalized source code files"
    )
    finalized_test_files: Dict[str, str] = Field(
        min_length=1, description="Hardened and finalized test files"
    )
    declared_commands: List[str] = Field(
        min_length=1, description="Explicit commands declared to execute and test the code"
    )


class ExecutionBundle(BaseModel):
    """The central planning contract approved by human before execution."""

    task: str = Field(description="Original user task description")
    assumptions: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(min_length=1)
    source_files: Dict[str, str] = Field(min_length=1)
    test_files: Dict[str, str] = Field(min_length=1)
    declared_commands: List[str] = Field(min_length=1)
    workspace_path: str = Field(description="Target isolated workspace directory path")
    bundle_digest: str = Field(
        description="Canonical SHA-256 integrity hash of files and declared commands"
    )


class ExecutionSummary(BaseModel):
    """Authentic runtime evidence captured directly from the execution sandbox."""

    success: bool = Field(description="True only if process exited with code 0")
    exit_code: int = Field(description="Actual process exit code")
    stdout: str = Field(default="", description="Captured standard output")
    stderr: str = Field(default="", description="Captured standard error")
    files_created: List[str] = Field(default_factory=list, description="Files present in workspace")
    commands_executed: List[str] = Field(default_factory=list, description="Commands actually run")
    error_summary: Optional[str] = Field(
        default=None, description="Diagnostic error summary if execution failed"
    )


# =====================================================================
# Real-Time WebSocket Event Contracts (Frontend 3D Synchronization)
# =====================================================================

import time
from typing import Literal, Union


# Animation vocabulary shared with frontend/src/types/office.ts.
AgentAnimationName = Literal["Idle", "Walk", "Sit", "Type", "Coffee", "Think", "Wait"]

# Behaviour arbitration priority. The OfficeDirector resolves competing intents
# by this order; a scheduled break can never preempt a gate presentation.
BehaviorPriority = Literal[
    "PIPELINE_CRITICAL",
    "PROVIDER_STATE",
    "SCHEDULED_BREAK",
    "AMBIENT_IDLE",
]

# Provider availability, as surfaced to the office and the operator HUD.
ProviderState = Literal[
    "OK",
    "RATE_LIMITED",
    "QUOTA_EXHAUSTED",
    "AUTH_FAILED",
    "OFFLINE",
]


class BaseOfficeEvent(BaseModel):
    timestamp: float = Field(default_factory=time.time)


class AgentMoveEvent(BaseOfficeEvent):
    """Movement *intent*. The server owns destination and slot; the client owns motion."""

    event_type: Literal["AGENT_MOVE"] = "AGENT_MOVE"
    agent_id: str
    from_node: str
    to_node: str
    action: str = "Walk"
    slot_id: Optional[str] = Field(
        default=None,
        description="Reserved sub-slot within to_node, so two agents never share a seat",
    )
    reason: str = Field(default="", description="Human-readable cause, for the HUD")
    priority: BehaviorPriority = "AMBIENT_IDLE"


class AgentStatusEvent(BaseOfficeEvent):
    event_type: Literal["AGENT_STATUS"] = "AGENT_STATUS"
    agent_id: str
    status_text: str  # e.g., "Thinking...", "Auditing edge cases..."
    animation: AgentAnimationName


class AgentWaitingEvent(BaseOfficeEvent):
    """A transient provider rate limit, rendered as a person waiting rather than a crash."""

    event_type: Literal["AGENT_WAITING"] = "AGENT_WAITING"
    agent_id: str
    provider: str
    model: str
    reason: str
    retry_after_seconds: float
    attempt: int = 1
    max_attempts: int = 1


class AgentClockOutEvent(BaseOfficeEvent):
    """A hard quota exhaustion. The agent leaves through the door and the role goes unavailable."""

    event_type: Literal["AGENT_CLOCK_OUT"] = "AGENT_CLOCK_OUT"
    agent_id: str
    provider: str
    reason: str
    reset_at_display: Optional[str] = None
    covered_by: Optional[str] = Field(
        default=None,
        description="Named substitute model if the work was covered. Failover is never silent.",
    )


class AgentClockInEvent(BaseOfficeEvent):
    event_type: Literal["AGENT_CLOCK_IN"] = "AGENT_CLOCK_IN"
    agent_id: str
    provider: str
    reason: str = ""


class AgentBreakEvent(BaseOfficeEvent):
    event_type: Literal["AGENT_BREAK"] = "AGENT_BREAK"
    agent_id: str
    break_type: Literal["COFFEE", "AIR", "LUNCH", "STRETCH", "READING"]
    destination: str
    duration_sim_minutes: int
    returning: bool = False


class ProviderRoleHealth(BaseModel):
    role: str
    provider: str
    model: str
    state: ProviderState = "OK"
    reset_at_display: Optional[str] = None
    detail: str = ""


class ProviderHealthEvent(BaseOfficeEvent):
    """Real backend health. Replaces the hardcoded 'NODES: 4/4 LIVE' telemetry."""

    event_type: Literal["PROVIDER_HEALTH"] = "PROVIDER_HEALTH"
    roles: List[ProviderRoleHealth] = Field(default_factory=list)
    sandbox_available: bool = False
    sandbox_backend: str = "docker"


class RedGreenStatusEvent(BaseOfficeEvent):
    """Frozen-contract test state, shown on the whiteboard."""

    event_type: Literal["RED_GREEN_STATUS"] = "RED_GREEN_STATUS"
    thread_id: str
    phase: Literal["RED", "GREEN", "UNVERIFIED"]
    detail: str = ""
    failing_tests_count: int = 0
    tdd_digest: str = ""


class WhiteboardGateEvent(BaseOfficeEvent):
    """Gate presentation payload. Must never carry the run token."""

    event_type: Literal["WHITEBOARD_GATE"] = "WHITEBOARD_GATE"
    thread_id: str
    task: str
    code_preview: str
    qa_report: str
    bundle_digest: str
    qa_status: Literal["PASS", "FAIL", "UNAVAILABLE"] = "PASS"
    red_status: Literal["RED", "GREEN", "UNVERIFIED"] = "UNVERIFIED"
    files: List[str] = Field(default_factory=list)
    commands: List[str] = Field(default_factory=list)
    gate_kind: Literal["EXECUTE", "RED_VERIFICATION"] = "EXECUTE"


class TerminalLogEvent(BaseOfficeEvent):
    event_type: Literal["TERMINAL_LOG"] = "TERMINAL_LOG"
    stream: Literal["stdout", "stderr"]
    chunk: str


class ProjectCompletedEvent(BaseOfficeEvent):
    event_type: Literal["PROJECT_COMPLETED"] = "PROJECT_COMPLETED"
    thread_id: str
    success: bool
    summary: str
    # success must require approval AND a zero sandbox exit code; these fields
    # exist so the HUD can show why, rather than asserting a percentage.
    approval_status: Optional[str] = None
    exit_code: Optional[int] = None
    failing_tests_count: int = 0
    trace_url: Optional[str] = None
    bundle_digest: Optional[str] = None


class OfficeClockEvent(BaseOfficeEvent):
    """Current server-owned simulated office time and attendance phase."""

    event_type: Literal["OFFICE_CLOCK"] = "OFFICE_CLOCK"
    phase: Literal["WORKDAY", "OFF_HOURS"]
    display_time: str
    day_number: int
    seconds_remaining: int


class OfficeScheduleTickEvent(BaseOfficeEvent):
    """Sim-time heartbeat for routine scheduling. 1 sim hour == 150 real seconds."""

    event_type: Literal["OFFICE_SCHEDULE_TICK"] = "OFFICE_SCHEDULE_TICK"
    sim_minutes_since_open: int
    display_time: str
    day_number: int


OfficeEvent = Union[
    AgentMoveEvent,
    AgentStatusEvent,
    AgentWaitingEvent,
    AgentClockOutEvent,
    AgentClockInEvent,
    AgentBreakEvent,
    ProviderHealthEvent,
    RedGreenStatusEvent,
    WhiteboardGateEvent,
    TerminalLogEvent,
    ProjectCompletedEvent,
    OfficeClockEvent,
    OfficeScheduleTickEvent,
]
