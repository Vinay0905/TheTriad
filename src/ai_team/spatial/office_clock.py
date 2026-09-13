"""Server-owned simulated office clock.

One workday is compressed into `AI_TEAM_WORKDAY_REAL_SECONDS` (20 real minutes
by default), so one simulated hour is 150 real seconds. Routines are declared
in *simulated* minutes and read `sim_minutes_since_open`, which means changing
the compression rescales the whole day automatically instead of silently
desynchronising every schedule.

The clock is intentionally held only in process memory: browser refreshes
reconnect to the same clock, while a server restart starts a fresh 09:00 day.
"""

import time
from dataclasses import dataclass

from ai_team.config import get_config

WORKDAY_MINUTES = 8 * 60
OPENING_HOUR = 9


@dataclass(frozen=True)
class OfficeClockSnapshot:
    phase: str
    display_time: str
    day_number: int
    seconds_remaining: int
    sim_minutes_since_open: int

    @property
    def is_workday(self) -> bool:
        return self.phase == "WORKDAY"


def format_sim_time(sim_minutes_since_open: int) -> str:
    total = OPENING_HOUR * 60 + max(0, sim_minutes_since_open)
    return f"{(total // 60) % 24:02d}:{total % 60:02d}"


class OfficeClock:
    def __init__(self) -> None:
        config = get_config()
        self._workday_seconds = max(1, config.workday_real_seconds)
        self._off_hours_seconds = max(1, config.off_hours_real_seconds)
        self._started_at = time.monotonic()

    @property
    def real_seconds_per_sim_hour(self) -> float:
        return self._workday_seconds / (WORKDAY_MINUTES / 60)

    def snapshot(self) -> OfficeClockSnapshot:
        elapsed = time.monotonic() - self._started_at
        cycle_seconds = self._workday_seconds + self._off_hours_seconds
        day_number = int(elapsed // cycle_seconds) + 1
        cycle_elapsed = elapsed % cycle_seconds

        if cycle_elapsed < self._workday_seconds:
            sim_minutes = int(cycle_elapsed / self._workday_seconds * WORKDAY_MINUTES)
            return OfficeClockSnapshot(
                phase="WORKDAY",
                display_time=format_sim_time(sim_minutes),
                day_number=day_number,
                seconds_remaining=max(0, int(self._workday_seconds - cycle_elapsed)),
                sim_minutes_since_open=sim_minutes,
            )

        return OfficeClockSnapshot(
            phase="OFF_HOURS",
            display_time=format_sim_time(WORKDAY_MINUTES),
            day_number=day_number,
            seconds_remaining=max(0, int(cycle_seconds - cycle_elapsed)),
            sim_minutes_since_open=WORKDAY_MINUTES,
        )
