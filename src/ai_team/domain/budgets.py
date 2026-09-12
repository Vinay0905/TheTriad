"""Operational budgets and hard-stop resource limits."""

import time
from dataclasses import dataclass, field
from typing import Optional


class BudgetExceededError(Exception):
    """Raised when an operational budget threshold is breached."""

    def __init__(self, resource: str, limit: float, current: float):
        self.resource = resource
        self.limit = limit
        self.current = current
        super().__init__(
            f"Budget exceeded for '{resource}': limit={limit}, current={current}"
        )


@dataclass(frozen=True)
class BudgetLimits:
    """Hard-stop resource ceilings for a single run."""

    max_wall_clock_seconds: float = 120.0
    max_provider_calls: int = 15
    max_total_tokens: int = 35_000
    max_retry_attempts: int = 3


@dataclass
class BudgetTracker:
    """Tracks resource consumption against configured limits."""

    limits: BudgetLimits = field(default_factory=BudgetLimits)
    start_time: float = field(default_factory=time.time)
    provider_calls: int = 0
    total_tokens: int = 0
    retry_attempts: int = 0

    def record_call(self, tokens: int = 0) -> None:
        """Record a single provider call with token usage."""
        self.provider_calls += 1
        self.total_tokens += tokens
        self.check_limits()

    def record_retry(self) -> None:
        """Record a retry attempt."""
        self.retry_attempts += 1
        self.check_limits()

    def elapsed_seconds(self) -> float:
        """Return elapsed wall-clock seconds since start."""
        return time.time() - self.start_time

    def check_limits(self) -> None:
        """Check all operational limits. Raise BudgetExceededError if any limit is breached."""
        elapsed = self.elapsed_seconds()
        if elapsed > self.limits.max_wall_clock_seconds:
            raise BudgetExceededError(
                "wall_clock_seconds", self.limits.max_wall_clock_seconds, round(elapsed, 2)
            )

        if self.provider_calls > self.limits.max_provider_calls:
            raise BudgetExceededError(
                "provider_calls", self.limits.max_provider_calls, self.provider_calls
            )

        if self.total_tokens > self.limits.max_total_tokens:
            raise BudgetExceededError(
                "total_tokens", self.limits.max_total_tokens, self.total_tokens
            )

        if self.retry_attempts > self.limits.max_retry_attempts:
            raise BudgetExceededError(
                "retry_attempts", self.limits.max_retry_attempts, self.retry_attempts
            )
