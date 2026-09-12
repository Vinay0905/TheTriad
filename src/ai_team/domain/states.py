"""State machine state definitions and terminal status classifications."""

from enum import Enum


class State(str, Enum):
    """Core states of the AI Team orchestration state machine."""

    RECEIVED = "RECEIVED"
    PLANNING = "PLANNING"
    RESEARCHING = "RESEARCHING"
    RESEARCH_SKIPPED = "RESEARCH_SKIPPED"
    DRAFTING = "DRAFTING"
    REVIEWING = "REVIEWING"
    BUNDLE_LOCKED = "BUNDLE_LOCKED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    EXECUTING = "EXECUTING"
    REPORTING = "REPORTING"

    # Terminal States
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"

    @property
    def is_terminal(self) -> bool:
        """Return True if this state is a terminal conclusion."""
        return self in {
            State.SUCCEEDED,
            State.FAILED,
            State.ABORTED,
            State.BLOCKED,
            State.INVALID,
        }

    @property
    def can_mutate_environment(self) -> bool:
        """Return True only if this state permits file writes or command execution."""
        return self == State.EXECUTING


class TerminalStatus(str, Enum):
    """Classification of final execution outcome."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ABORTED_BY_USER = "ABORTED_BY_USER"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"
    INVALID_CONTRACT = "INVALID_CONTRACT"
