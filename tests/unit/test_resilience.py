"""Provider failures must be classified correctly and never invented around."""

import pytest

from ai_team.providers.resilience import (
    AUTH_FAILED,
    HARD_ERROR,
    QUOTA_EXHAUSTED,
    RATE_LIMITED,
    AllProvidersUnavailableError,
    InvalidModelOutput,
    ProviderHealthRegistry,
    RoleProvider,
    call_with_office_presence,
    classify_provider_error,
)


class FakeHttpError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


@pytest.fixture(autouse=True)
def fast_backoff(monkeypatch):
    """Keep the retry loop instant and silent during tests."""
    monkeypatch.setattr("ai_team.providers.resilience.time.sleep", lambda _s: None)
    monkeypatch.setattr("ai_team.providers.resilience._dispatch", lambda _event: None)
    monkeypatch.setattr("ai_team.providers.resilience._broadcast_health", lambda: None)
    monkeypatch.setattr("ai_team.providers.resilience._director", lambda: None)


# -- classification ----------------------------------------------------


@pytest.mark.parametrize(
    "error",
    [
        FakeHttpError("Rate limit reached for model", 429),
        FakeHttpError("Too Many Requests"),
        Exception("Error code: 1305 - concurrency limit"),
        Exception("tokens per minute exceeded, slow down"),
        Exception("RESOURCE_EXHAUSTED"),
    ],
)
def test_transient_limits_are_retryable(error):
    outcome = classify_provider_error(error)
    assert outcome.state == RATE_LIMITED
    assert outcome.is_transient
    assert outcome.retry_after_seconds > 0


@pytest.mark.parametrize(
    "error",
    [
        FakeHttpError("Insufficient credits to continue", 402),
        Exception("You exceeded your current quota, please check your billing"),
        Exception("Free tier limit reached: requests per day"),
        Exception("insufficient_quota"),
        Exception("daily limit reached for this key"),
    ],
)
def test_hard_quota_is_not_retried(error):
    outcome = classify_provider_error(error)
    assert outcome.state == QUOTA_EXHAUSTED
    assert not outcome.is_transient
    assert outcome.reset_after_seconds > 0


def test_daily_quota_reported_as_429_is_still_a_quota_error():
    """Google returns 429 for both cases; the body is the deciding signal."""
    outcome = classify_provider_error(
        FakeHttpError("429 RESOURCE_EXHAUSTED: quota exceeded, requests per day", 429)
    )
    assert outcome.state == QUOTA_EXHAUSTED


def test_ambiguous_429_prefers_waiting_over_clocking_out():
    """Misreading a rate limit as a day-long outage is the worse mistake."""
    outcome = classify_provider_error(FakeHttpError("429", 429))
    assert outcome.state == RATE_LIMITED


@pytest.mark.parametrize(
    "error",
    [
        FakeHttpError("Invalid API key provided", 401),
        FakeHttpError("Forbidden", 403),
        Exception("API key not valid. Please pass a valid API key."),
    ],
)
def test_credential_failures_are_distinct(error):
    assert classify_provider_error(error).state == AUTH_FAILED


def test_unknown_errors_are_hard_errors():
    assert classify_provider_error(ValueError("something odd")).state == HARD_ERROR


def test_invalid_output_is_a_hard_error_not_a_retry():
    outcome = classify_provider_error(InvalidModelOutput("unusable test contract"))
    assert outcome.state == HARD_ERROR
    assert not outcome.is_transient


# -- the calling loop --------------------------------------------------


def _provider(label, behaviour, model="m"):
    return RoleProvider(label=label, provider=label.lower(), model=model, call=behaviour)


def test_first_working_provider_wins_and_is_attributed():
    result, attribution = call_with_office_presence(
        role="main.py",
        agent_id="developer",
        candidates=[_provider("Groq", lambda: "code", model="llama")],
    )
    assert result == "code"
    assert attribution == "groq:llama"


def test_rate_limit_is_retried_then_succeeds():
    attempts = {"count": 0}

    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise FakeHttpError("rate limit", 429)
        return "code"

    result, _ = call_with_office_presence(
        role="main.py", agent_id="developer", candidates=[_provider("Groq", flaky)]
    )
    assert result == "code"
    assert attempts["count"] == 3


def test_exhausted_quota_fails_over_to_the_next_provider():
    def dead():
        raise Exception("You exceeded your current quota")

    result, attribution = call_with_office_presence(
        role="main.py",
        agent_id="developer",
        candidates=[
            _provider("Groq", dead, model="llama"),
            _provider("Gemini", lambda: "covered", model="flash"),
        ],
    )
    assert result == "covered"
    # Attribution names the substitute, so failover is never silent.
    assert attribution == "gemini:flash"


def test_quota_error_is_not_retried_against_the_same_provider():
    calls = {"count": 0}

    def dead():
        calls["count"] += 1
        raise Exception("insufficient_quota")

    with pytest.raises(AllProvidersUnavailableError):
        call_with_office_presence(
            role="qa_audit", agent_id="qa", candidates=[_provider("GLM", dead)]
        )
    assert calls["count"] == 1


def test_all_providers_failing_raises_rather_than_returning_a_default():
    with pytest.raises(AllProvidersUnavailableError) as excinfo:
        call_with_office_presence(
            role="qa_audit",
            agent_id="qa",
            candidates=[
                _provider("GLM", lambda: (_ for _ in ()).throw(Exception("insufficient_quota"))),
                _provider("Groq", lambda: (_ for _ in ()).throw(ValueError("broken"))),
            ],
        )
    assert "qa_audit" in str(excinfo.value)


def test_no_candidates_raises_with_an_explanation():
    with pytest.raises(AllProvidersUnavailableError) as excinfo:
        call_with_office_presence(role="qa_audit", agent_id="qa", candidates=[])
    assert "no provider credentials configured" in str(excinfo.value)


# -- health registry ---------------------------------------------------


def test_registry_reports_unknown_roles_as_available():
    registry = ProviderHealthRegistry()
    assert registry.is_available("qa_audit") is True


def test_quota_exhaustion_marks_a_role_unavailable():
    registry = ProviderHealthRegistry()
    registry.mark(
        "qa_audit", "qa", "zhipuai", "glm-4-flash", QUOTA_EXHAUSTED, unavailable_for=3600
    )
    assert registry.is_available("qa_audit") is False

    snapshot = {item.role: item for item in registry.snapshot()}
    assert snapshot["qa_audit"].state == QUOTA_EXHAUSTED
    assert snapshot["qa_audit"].reset_at_display is not None


def test_rate_limited_role_is_still_considered_available():
    """A transient limit means wait, not that the role has gone away."""
    registry = ProviderHealthRegistry()
    registry.mark("main.py", "developer", "groq", "llama", RATE_LIMITED)
    assert registry.is_available("main.py") is True


def test_cooldown_expiry_recovers_the_role():
    registry = ProviderHealthRegistry()
    registry.mark(
        "qa_audit", "qa", "zhipuai", "glm", QUOTA_EXHAUSTED, unavailable_for=-1
    )
    assert registry.reset_expired() == ["qa_audit"]
    assert registry.is_available("qa_audit") is True
    # Already recovered, so nothing to announce a second time.
    assert registry.reset_expired() == []
