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


class BaseOfficeEvent(BaseModel):
    timestamp: float = Field(default_factory=time.time)


class AgentMoveEvent(BaseOfficeEvent):
    event_type: Literal["AGENT_MOVE"] = "AGENT_MOVE"
    agent_id: str
    from_node: str
    to_node: str
    action: str = "Walk"


class AgentStatusEvent(BaseOfficeEvent):
    event_type: Literal["AGENT_STATUS"] = "AGENT_STATUS"
    agent_id: str
    status_text: str  # e.g., "Thinking...", "Auditing edge cases..."
    animation: Literal["Idle", "Walk", "Sit", "Type", "Coffee"]


class WhiteboardGateEvent(BaseOfficeEvent):
    event_type: Literal["WHITEBOARD_GATE"] = "WHITEBOARD_GATE"
    thread_id: str
    task: str
    code_preview: str
    qa_report: str
    bundle_digest: str


class TerminalLogEvent(BaseOfficeEvent):
    event_type: Literal["TERMINAL_LOG"] = "TERMINAL_LOG"
    stream: Literal["stdout", "stderr"]
    chunk: str


class ProjectCompletedEvent(BaseOfficeEvent):
    event_type: Literal["PROJECT_COMPLETED"] = "PROJECT_COMPLETED"
    thread_id: str
    success: bool
    summary: str


class OfficeClockEvent(BaseOfficeEvent):
    """Current server-owned simulated office time and attendance phase."""

    event_type: Literal["OFFICE_CLOCK"] = "OFFICE_CLOCK"
    phase: Literal["WORKDAY", "OFF_HOURS"]
    display_time: str
    day_number: int
    seconds_remaining: int


OfficeEvent = Union[
    AgentMoveEvent,
    AgentStatusEvent,
    WhiteboardGateEvent,
    TerminalLogEvent,
    ProjectCompletedEvent,
    OfficeClockEvent,
]
