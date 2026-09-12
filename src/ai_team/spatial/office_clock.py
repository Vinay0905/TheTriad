"""Server-owned simulated office clock.

One workday lasts twenty real minutes.  The clock is intentionally held only
in process memory: browser refreshes reconnect to the same clock, while a
server restart starts a fresh 09:00 day as requested.
"""

from dataclasses import dataclass
import time


WORKDAY_SECONDS = 20 * 60
OFF_HOURS_SECONDS = 20 * 60
WORKDAY_MINUTES = 8 * 60


@dataclass(frozen=True)
class OfficeClockSnapshot:
    phase: str
    display_time: str
    day_number: int
    seconds_remaining: int


class OfficeClock:
    def __init__(self) -> None:
        self._started_at = time.monotonic()

    def snapshot(self) -> OfficeClockSnapshot:
        elapsed = time.monotonic() - self._started_at
        cycle_seconds = WORKDAY_SECONDS + OFF_HOURS_SECONDS
        day_number = int(elapsed // cycle_seconds) + 1
        cycle_elapsed = elapsed % cycle_seconds

        if cycle_elapsed < WORKDAY_SECONDS:
            simulated_minutes = int(cycle_elapsed / WORKDAY_SECONDS * WORKDAY_MINUTES)
            total_minutes = 9 * 60 + simulated_minutes
            return OfficeClockSnapshot(
                phase="WORKDAY",
                display_time=f"{total_minutes // 60:02d}:{total_minutes % 60:02d}",
                day_number=day_number,
                seconds_remaining=max(0, int(WORKDAY_SECONDS - cycle_elapsed)),
            )

        return OfficeClockSnapshot(
            phase="OFF_HOURS",
            display_time="17:00",
            day_number=day_number,
            seconds_remaining=max(0, int(cycle_seconds - cycle_elapsed)),
        )
