"""Unit test for simulated office clock progression."""

import pytest
from ai_team.spatial.office_clock import OfficeClock


def test_office_clock_progression(monkeypatch):
    clock = OfficeClock()

    # Initial start: 09:00
    snap = clock.snapshot()
    assert snap.phase == 'WORKDAY'
    assert snap.display_time == '09:00'
    assert snap.day_number == 1

    # Simulate 5 real minutes elapsed (300 seconds) -> 2 hours into workday -> 11:00
    fake_time = clock._started_at + 300
    monkeypatch.setattr('time.monotonic', lambda: fake_time)

    snap_mid = clock.snapshot()
    assert snap_mid.phase == 'WORKDAY'
    assert snap_mid.display_time == '11:00'

    # Simulate 10 real minutes elapsed (600 seconds) -> 4 hours into workday -> 13:00
    fake_time = clock._started_at + 600
    monkeypatch.setattr('time.monotonic', lambda: fake_time)

    snap_noon = clock.snapshot()
    assert snap_noon.phase == 'WORKDAY'
    assert snap_noon.display_time == '13:00'

    # Simulate 20 real minutes elapsed (1200 seconds) -> 17:00 OFF_HOURS
    fake_time = clock._started_at + 1201
    monkeypatch.setattr('time.monotonic', lambda: fake_time)

    snap_close = clock.snapshot()
    assert snap_close.phase == 'OFF_HOURS'
    assert snap_close.display_time == '17:00'
