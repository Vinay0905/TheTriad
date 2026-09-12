"""Unit tests for hard-stop budget limits enforcement."""

import pytest
import time
from ai_team.domain.budgets import BudgetLimits, BudgetTracker, BudgetExceededError


def test_budget_within_limits():
    limits = BudgetLimits(max_provider_calls=5, max_total_tokens=1000)
    tracker = BudgetTracker(limits=limits)

    tracker.record_call(tokens=200)
    tracker.record_call(tokens=300)
    assert tracker.provider_calls == 2
    assert tracker.total_tokens == 500


def test_budget_exceeded_provider_calls():
    limits = BudgetLimits(max_provider_calls=2)
    tracker = BudgetTracker(limits=limits)

    tracker.record_call()
    tracker.record_call()
    with pytest.raises(BudgetExceededError) as exc_info:
        tracker.record_call()
    assert "provider_calls" in str(exc_info.value)


def test_budget_exceeded_tokens():
    limits = BudgetLimits(max_total_tokens=500)
    tracker = BudgetTracker(limits=limits)

    with pytest.raises(BudgetExceededError) as exc_info:
        tracker.record_call(tokens=600)
    assert "total_tokens" in str(exc_info.value)


def test_budget_exceeded_wall_clock():
    limits = BudgetLimits(max_wall_clock_seconds=0.1)
    tracker = BudgetTracker(limits=limits)

    time.sleep(0.15)
    with pytest.raises(BudgetExceededError) as exc_info:
        tracker.check_limits()
    assert "wall_clock_seconds" in str(exc_info.value)
