"""Free-tier reality, expressed as office behaviour instead of hidden failure.

Every role here runs on a free or near-free tier, so rate limits and exhausted
quotas are normal operating conditions rather than exceptions. The old code
swallowed them: a 429 from the auditor set `qa_passed = True`, and the
developer silently walked down a chain of three providers so you never learned
which model wrote your code.

This module makes both visible and honest:

- A **transient rate limit** becomes a person waiting at their desk with a
  countdown, and the call is retried with backoff.
- An **exhausted quota** becomes a person clocking out through the door, and
  the role is marked unavailable until it resets.
- **Failover is always named.** If a substitute covers the work, the office
  says so and the artifact records which model actually produced it.

What this module never does is invent a result. If every provider for a role is
unavailable, it raises, and the caller reports that to the operator.
"""

import random
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from ai_team.config import get_config
from ai_team.domain.contracts import (
    AgentClockInEvent,
    AgentClockOutEvent,
    AgentStatusEvent,
    AgentWaitingEvent,
    ProviderHealthEvent,
    ProviderRoleHealth,
)

OK = "OK"
RATE_LIMITED = "RATE_LIMITED"
QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
AUTH_FAILED = "AUTH_FAILED"
HARD_ERROR = "HARD_ERROR"

# Phrases that mean "you are out for the day", as distinct from "slow down".
# Providers are inconsistent about which HTTP status they use for which, so the
# body text is often the only reliable signal.
_QUOTA_MARKERS = (
    "quota exceeded",
    "insufficient_quota",
    "insufficient balance",
    "out of credits",
    "credit balance",
    "billing",
    "per day",
    "daily limit",
    "requests per day",
    "rpd",
    "exhausted your current quota",
    "free tier limit",
    "account balance",
)

_RATE_MARKERS = (
    "rate limit",
    "ratelimit",
    "too many requests",
    "slow down",
    "requests per minute",
    "tokens per minute",
    "concurrency",
)

_AUTH_MARKERS = (
    "invalid api key",
    "incorrect api key",
    "unauthorized",
    "authentication",
    "api key not valid",
    "no auth credentials",
    "permission denied",
)

_RETRY_AFTER_PATTERNS = (
    re.compile(r"retry[- ]after[\"':\s]+([0-9.]+)", re.I),
    re.compile(r"try again in ([0-9.]+)\s*s", re.I),
    re.compile(r"please retry after ([0-9.]+)", re.I),
)


@dataclass(frozen=True)
class ProviderOutcome:
    """Classification of a provider failure."""

    state: str
    detail: str = ""
    retry_after_seconds: float = 0.0
    reset_after_seconds: float = 0.0

    @property
    def is_transient(self) -> bool:
        return self.state == RATE_LIMITED


def _status_code(error: BaseException) -> Optional[int]:
    for attribute in ("status_code", "http_status", "code"):
        value = getattr(error, attribute, None)
        if isinstance(value, int):
            return value

    response = getattr(error, "response", None)
    if response is not None:
        value = getattr(response, "status_code", None)
        if isinstance(value, int):
            return value

    match = re.search(r"\b(4\d\d|5\d\d)\b", str(error))
    if match:
        return int(match.group(1))
    return None


def _retry_after(text: str) -> float:
    for pattern in _RETRY_AFTER_PATTERNS:
        match = pattern.search(text)
        if match:
            try:
                return max(0.0, float(match.group(1)))
            except ValueError:
                continue
    return 0.0


def classify_provider_error(error: BaseException) -> ProviderOutcome:
    """Decide whether to wait, clock out, or give up.

    Ambiguity resolves toward the *less* destructive reading: an unclear 429 is
    treated as a transient rate limit and retried, because clocking a role out
    for an hour on a misread is worse than one extra backoff.
    """
    text = str(error).lower()
    status = _status_code(error)
    config = get_config()

    if any(marker in text for marker in _AUTH_MARKERS) or status in (401, 403):
        return ProviderOutcome(AUTH_FAILED, detail="credentials rejected")

    # Hard quota: no amount of waiting inside this run will help.
    quota_hit = any(marker in text for marker in _QUOTA_MARKERS)
    # OpenRouter uses 402 for an empty credit balance.
    if status == 402 or (quota_hit and not any(m in text for m in _RATE_MARKERS)):
        return ProviderOutcome(
            QUOTA_EXHAUSTED,
            detail="provider quota or credit exhausted",
            reset_after_seconds=float(config.provider_quota_cooldown_seconds),
        )

    # ZhipuAI signals concurrency/rate limiting with code 1305.
    if "1305" in text or status == 429 or any(m in text for m in _RATE_MARKERS):
        wait = _retry_after(text) or config.provider_backoff_base_seconds
        # Google returns RESOURCE_EXHAUSTED for both cases; the body decides.
        if quota_hit:
            return ProviderOutcome(
                QUOTA_EXHAUSTED,
                detail="daily quota exhausted",
                reset_after_seconds=float(config.provider_quota_cooldown_seconds),
            )
        return ProviderOutcome(
            RATE_LIMITED, detail="rate limited", retry_after_seconds=wait
        )

    if "resource_exhausted" in text:
        return ProviderOutcome(
            RATE_LIMITED,
            detail="resource exhausted",
            retry_after_seconds=config.provider_backoff_base_seconds,
        )

    return ProviderOutcome(HARD_ERROR, detail=str(error)[:200])


# ---------------------------------------------------------------------------
# Health registry
# ---------------------------------------------------------------------------


@dataclass
class _RoleHealth:
    role: str
    agent_id: str
    provider: str = ""
    model: str = ""
    state: str = OK
    detail: str = ""
    available_at: float = 0.0

    def is_available(self) -> bool:
        if self.state in (OK, RATE_LIMITED):
            return True
        return time.time() >= self.available_at


class ProviderHealthRegistry:
    """Live availability per role, shared by the graph and the HUD.

    This is what the TopBar reads. It previously displayed a hardcoded
    "NODES: 4/4 LIVE", which was true only by coincidence.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._roles: Dict[str, _RoleHealth] = {}

    def _entry(self, role: str, agent_id: str) -> _RoleHealth:
        entry = self._roles.get(role)
        if entry is None:
            entry = _RoleHealth(role=role, agent_id=agent_id)
            self._roles[role] = entry
        return entry

    def mark(
        self,
        role: str,
        agent_id: str,
        provider: str,
        model: str,
        state: str,
        detail: str = "",
        unavailable_for: float = 0.0,
    ) -> None:
        with self._lock:
            entry = self._entry(role, agent_id)
            entry.agent_id = agent_id
            entry.provider = provider
            entry.model = model
            entry.state = state
            entry.detail = detail
            entry.available_at = time.time() + unavailable_for if unavailable_for else 0.0

    def is_available(self, role: str) -> bool:
        with self._lock:
            entry = self._roles.get(role)
            return True if entry is None else entry.is_available()

    def reset_expired(self) -> List[str]:
        """Return roles whose cooldown has elapsed, clearing them to OK."""
        recovered = []
        with self._lock:
            for role, entry in self._roles.items():
                if entry.state == QUOTA_EXHAUSTED and time.time() >= entry.available_at:
                    entry.state = OK
                    entry.detail = "quota window reset"
                    entry.available_at = 0.0
                    recovered.append(role)
        return recovered

    def snapshot(self) -> List[ProviderRoleHealth]:
        with self._lock:
            return [
                ProviderRoleHealth(
                    role=entry.role,
                    provider=entry.provider,
                    model=entry.model,
                    state=entry.state,
                    reset_at_display=(
                        time.strftime("%H:%M", time.localtime(entry.available_at))
                        if entry.available_at
                        else None
                    ),
                    detail=entry.detail,
                )
                for entry in sorted(self._roles.values(), key=lambda item: item.role)
            ]


_registry: Optional[ProviderHealthRegistry] = None


def get_provider_health() -> ProviderHealthRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderHealthRegistry()
    return _registry


# ---------------------------------------------------------------------------
# Calling a role with visible presence
# ---------------------------------------------------------------------------


class InvalidModelOutput(RuntimeError):
    """The call succeeded but the response was unusable.

    Raised by a candidate so the resilience loop moves on to the next provider,
    exactly as it would for a transport error. Classified as a hard error, so it
    is recorded and never retried against the same provider.
    """


class AllProvidersUnavailableError(RuntimeError):
    """Every provider for a role failed. Callers must report, never fabricate."""

    def __init__(self, role: str, notes: List[str]) -> None:
        self.role = role
        self.notes = notes
        super().__init__(f"No provider available for {role}: {'; '.join(notes)}")


@dataclass
class RoleProvider:
    """One way to fulfil a role, with the attribution it earns on success."""

    label: str
    provider: str
    model: str
    call: Callable[[], Any]

    @property
    def attribution(self) -> str:
        return f"{self.provider}:{self.model}"


def _dispatch(event) -> None:
    try:
        from ai_team.spatial.event_bus import get_event_bus

        get_event_bus().dispatch(event)
    except Exception as err:  # office visuals must never break the pipeline
        print(f"  [Resilience] event dispatch skipped: {err}")


def _director():
    """The Director owns movement, so provider state has to reach it.

    Imported lazily to keep the dependency one-directional at module load.
    """
    try:
        from ai_team.spatial.director import get_director

        return get_director()
    except Exception as err:
        print(f"  [Resilience] director unavailable: {err}")
        return None


def _broadcast_health() -> None:
    from ai_team.execution.sandbox import sandbox_status

    # Cached: this is called on every provider outcome, and probing Docker
    # spawns a subprocess.
    available, _detail = sandbox_status()

    _dispatch(
        ProviderHealthEvent(
            roles=get_provider_health().snapshot(),
            sandbox_available=available,
            sandbox_backend=get_config().sandbox_backend,
        )
    )


def announce_recoveries() -> None:
    """Clock roles back in once their quota window has rolled over."""
    health = get_provider_health()
    recovered = health.reset_expired()
    if not recovered:
        return

    snapshot = {item.role: item for item in health.snapshot()}
    director = _director()
    for role in recovered:
        entry = snapshot.get(role)
        if entry is None:
            continue
        agent_id = _AGENT_FOR_ROLE.get(role, role)
        _dispatch(
            AgentClockInEvent(
                agent_id=agent_id,
                provider=entry.provider,
                reason="Quota window reset; back at their desk.",
            )
        )
        if director is not None:
            director.note_clock_in(agent_id)
    _broadcast_health()


_AGENT_FOR_ROLE = {
    "manager_rfc": "manager",
    "researcher_audit": "researcher",
    "tdd_contract": "developer",
    "main.py": "developer",
    "qa_audit": "qa",
}


def call_with_office_presence(
    role: str,
    agent_id: str,
    candidates: List[RoleProvider],
    *,
    on_wait_status: Optional[str] = None,
) -> Tuple[Any, str]:
    """Invoke the first working provider, narrating what happens.

    Returns `(result, attribution)`. Raises `AllProvidersUnavailableError` if
    nothing worked, so the caller can report the truth rather than guess.
    """
    config = get_config()
    health = get_provider_health()
    notes: List[str] = []
    clocked_out: List[RoleProvider] = []

    for index, candidate in enumerate(candidates):
        attempt = 0
        while attempt < max(1, config.provider_max_retries):
            attempt += 1
            try:
                result = candidate.call()
            except Exception as err:
                outcome = classify_provider_error(err)

                if outcome.state == RATE_LIMITED:
                    delay = min(
                        outcome.retry_after_seconds
                        or config.provider_backoff_base_seconds * (2 ** (attempt - 1)),
                        config.provider_backoff_max_seconds,
                    )
                    delay += random.uniform(0, 0.6)  # de-synchronise parallel roles

                    health.mark(
                        role,
                        agent_id,
                        candidate.provider,
                        candidate.model,
                        RATE_LIMITED,
                        detail=outcome.detail,
                    )
                    wait_reason = (
                        on_wait_status
                        or f"{candidate.provider} is rate limiting; waiting it out."
                    )
                    _dispatch(
                        AgentWaitingEvent(
                            agent_id=agent_id,
                            provider=candidate.provider,
                            model=candidate.model,
                            reason=wait_reason,
                            retry_after_seconds=round(delay, 1),
                            attempt=attempt,
                            max_attempts=config.provider_max_retries,
                        )
                    )
                    director = _director()
                    if director is not None:
                        director.note_provider_waiting(agent_id, delay, wait_reason)
                    _broadcast_health()
                    print(
                        f"  [{role}] {candidate.label} rate limited; "
                        f"waiting {delay:.1f}s (attempt {attempt})"
                    )
                    time.sleep(delay)
                    continue

                if outcome.state == QUOTA_EXHAUSTED:
                    health.mark(
                        role,
                        agent_id,
                        candidate.provider,
                        candidate.model,
                        QUOTA_EXHAUSTED,
                        detail=outcome.detail,
                        unavailable_for=outcome.reset_after_seconds,
                    )
                    clocked_out.append(candidate)
                    notes.append(f"{candidate.label} quota exhausted")
                    print(f"  [{role}] {candidate.label} quota exhausted; clocking out.")
                    _broadcast_health()
                    break

                if outcome.state == AUTH_FAILED:
                    health.mark(
                        role,
                        agent_id,
                        candidate.provider,
                        candidate.model,
                        AUTH_FAILED,
                        detail=outcome.detail,
                    )
                    notes.append(f"{candidate.label} credentials rejected")
                    _broadcast_health()
                    break

                notes.append(f"{candidate.label} failed: {outcome.detail}")
                print(f"  [{role}] {candidate.label} error: {outcome.detail}")
                break
            else:
                health.mark(
                    role, agent_id, candidate.provider, candidate.model, OK
                )
                director = _director()
                if director is not None:
                    director.note_provider_recovered(agent_id)

                # Failover is never silent: if someone covered for a colleague
                # who clocked out, the office and the report both say so.
                if clocked_out:
                    absent = clocked_out[-1]
                    _dispatch(
                        AgentClockOutEvent(
                            agent_id=agent_id,
                            provider=absent.provider,
                            reason=(
                                f"{absent.provider} quota exhausted. "
                                f"Work covered by {candidate.attribution}."
                            ),
                            covered_by=candidate.attribution,
                        )
                    )
                    _dispatch(
                        AgentStatusEvent(
                            agent_id=agent_id,
                            status_text=f"Covered by {candidate.model}",
                            animation="Type",
                        )
                    )
                _broadcast_health()
                return result, candidate.attribution

        if index == len(candidates) - 1 and clocked_out:
            # Nobody could cover, so the absence is final for this run and the
            # agent actually leaves the office.
            absent = clocked_out[-1]
            reason = f"{absent.provider} quota exhausted; out for the day."
            _dispatch(
                AgentClockOutEvent(
                    agent_id=agent_id,
                    provider=absent.provider,
                    reason=reason,
                    covered_by=None,
                )
            )
            director = _director()
            if director is not None:
                director.note_clock_out(agent_id, reason)

    if not candidates:
        notes.append("no provider credentials configured")

    _broadcast_health()
    raise AllProvidersUnavailableError(role, notes)
