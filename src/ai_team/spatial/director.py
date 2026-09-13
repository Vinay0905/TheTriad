"""The OfficeDirector: one authoritative owner of agent behaviour.

Choreography used to live in three places that fought each other — a hardcoded
`if/elif` chain inside the graph loop (which also slept on the worker thread
for up to seven seconds of pure cosmetics), a routine loop in the browser that
switched itself off during live runs, and the clock-out logic. Nothing
arbitrated between them.

Everything now emits *semantic* events ("QA audit started", "Groq is rate
limiting", "the gate opened") and the Director decides who moves where. It owns
three things the old code had none of:

1. **Priority arbitration.** A coffee break can never preempt a gate
   presentation, and ambient wandering never preempts anything.
2. **Slot reservation.** Two agents are never *dispatched* to the same seat.
   Local collision avoidance in the browser cannot fix a bad destination.
3. **Sim-time routines chosen by utility**, not a fixed rotation, so behaviour
   does not visibly loop.

The Director never blocks the pipeline. It runs on its own asyncio task.
"""

import asyncio
import random
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Deque, Dict, List, Optional, Tuple

from ai_team.domain.contracts import (
    AgentBreakEvent,
    AgentMoveEvent,
    AgentStatusEvent,
    OfficeScheduleTickEvent,
)
from ai_team.spatial.event_bus import get_event_bus
from ai_team.spatial.office_clock import OfficeClock, format_sim_time


class Priority(IntEnum):
    """Higher wins. Equal priority is first-come."""

    AMBIENT_IDLE = 0
    SCHEDULED_BREAK = 1
    PROVIDER_STATE = 2
    PIPELINE_CRITICAL = 3


PRIORITY_NAMES = {
    Priority.AMBIENT_IDLE: "AMBIENT_IDLE",
    Priority.SCHEDULED_BREAK: "SCHEDULED_BREAK",
    Priority.PROVIDER_STATE: "PROVIDER_STATE",
    Priority.PIPELINE_CRITICAL: "PIPELINE_CRITICAL",
}


@dataclass(frozen=True)
class Destination:
    """A place an agent can stand, with how many can stand there.

    `capacity` is why two colleagues never merge into one body at the espresso
    bar: the second one is given a different sub-slot, or waits.
    """

    capacity: int = 1
    alternates: Tuple[str, ...] = ()


# Mirrors the named destinations in frontend/src/components/office/OfficeGeometry.ts.
DESTINATIONS: Dict[str, Destination] = {
    "desk_david": Destination(),
    "desk_elena": Destination(),
    "desk_alex": Destination(),
    "desk_maya": Destination(),
    "desk_alex_review": Destination(),
    "pantry": Destination(capacity=2),
    "whiteboard_manager": Destination(alternates=("whiteboard_researcher",)),
    "whiteboard_qa": Destination(alternates=("whiteboard_researcher",)),
    "whiteboard_researcher": Destination(alternates=("whiteboard_manager",)),
    "meeting_david": Destination(),
    "meeting_elena": Destination(),
    "meeting_alex": Destination(),
    "meeting_maya": Destination(),
    "boss_room": Destination(),
    # The door is a threshold, not a seat.
    "exit": Destination(capacity=4),
}

HOME_DESKS: Dict[str, str] = {
    "manager": "desk_david",
    "researcher": "desk_elena",
    "developer": "desk_alex",
    "qa": "desk_maya",
}

AGENT_NAMES: Dict[str, str] = {
    "manager": "David",
    "researcher": "Elena",
    "developer": "Alex",
    "qa": "Maya",
}


@dataclass
class Need:
    """A drive that accumulates in sim-time and is satisfied by going somewhere.

    Scoring rather than scheduling is what stops the office looping visibly:
    the same routine recurs on roughly the right cadence without ever repeating
    the same order.
    """

    name: str
    destination: str
    break_type: str
    status: str
    animation: str
    # Sim-minutes to go from satisfied to wanting it.
    period_sim_minutes: float
    dwell_sim_minutes: int
    level: float = 0.0

    def accumulate(self, sim_minutes: float) -> None:
        if self.period_sim_minutes > 0:
            self.level += sim_minutes / self.period_sim_minutes

    def satisfy(self) -> None:
        # Slight overshoot so the next occurrence is not perfectly periodic.
        self.level = -random.uniform(0.0, 0.25)


def _needs_for(agent_id: str) -> List[Need]:
    """Per-role habits. Offsets keep two people out of the pantry at once."""
    if agent_id == "manager":
        return [
            Need("air", "exit", "AIR", "{name}: Out for air - reports will wait.", "Walk", 120, 20),
            Need("coffee", "pantry", "COFFEE", "{name}: Refilling coffee.", "Coffee", 210, 12),
        ]
    if agent_id == "developer":
        return [
            Need("coffee", "pantry", "COFFEE", "{name}: Espresso before the next pass.", "Coffee", 120, 15),
            Need("movement", "whiteboard_researcher", "STRETCH", "{name}: Sketching an approach on the board.", "Type", 200, 10),
        ]
    if agent_id == "qa":
        return [
            Need("movement", "desk_alex_review", "STRETCH", "{name}: One more edge case for Alex.", "Type", 180, 12),
            Need("coffee", "pantry", "COFFEE", "{name}: Tea break.", "Coffee", 240, 10),
        ]
    return [
        Need("reading", "whiteboard_researcher", "READING", "{name}: Re-reading the research board.", "Type", 150, 12),
        Need("coffee", "pantry", "COFFEE", "{name}: Coffee and a think.", "Coffee", 260, 12),
    ]


@dataclass
class Intent:
    """A request to put an agent somewhere, with a reason and a priority."""

    agent_id: str
    destination: str
    status_text: str
    animation: str = "Walk"
    priority: Priority = Priority.AMBIENT_IDLE
    reason: str = ""
    dwell_sim_minutes: int = 0
    break_type: Optional[str] = None
    return_home: bool = False


@dataclass
class Actor:
    agent_id: str
    location: str
    slot_id: Optional[str] = None
    priority: Priority = Priority.AMBIENT_IDLE
    present: bool = True
    # Sim-minute deadline for the current dwell, or None to stay put.
    #
    # A preempted break is deliberately not queued for resumption. Its need
    # stays partially elevated, so it simply recurs sooner, which is both
    # simpler and reads more naturally than teleporting someone back to a
    # coffee they abandoned twenty simulated minutes ago.
    dwell_until: Optional[float] = None
    waiting_on_provider: bool = False
    clocked_out: bool = False
    needs: List[Need] = field(default_factory=list)


class OccupancyTable:
    """Which agent holds which sub-slot of which destination."""

    def __init__(self) -> None:
        self._held: Dict[str, Dict[int, str]] = {}

    def release(self, agent_id: str) -> None:
        for slots in self._held.values():
            for index, holder in list(slots.items()):
                if holder == agent_id:
                    del slots[index]

    def reserve(self, agent_id: str, waypoint: str) -> Optional[str]:
        """Claim a free sub-slot, or None if the destination is full."""
        destination = DESTINATIONS.get(waypoint)
        if destination is None:
            # Unknown destinations are single-occupancy by default.
            destination = Destination()

        slots = self._held.setdefault(waypoint, {})
        for index in range(destination.capacity):
            holder = slots.get(index)
            if holder is None or holder == agent_id:
                slots[index] = agent_id
                return f"{waypoint}#{index}"
        return None

    def find_free(self, agent_id: str, waypoint: str) -> Optional[str]:
        """Which destination this agent could take, without reserving anything.

        Separate from `reserve_with_alternates` so a behaviour can be *tested*
        for feasibility without the side effect of moving the agent's claim.
        """
        for candidate in (waypoint, *DESTINATIONS.get(waypoint, Destination()).alternates):
            destination = DESTINATIONS.get(candidate, Destination())
            slots = self._held.get(candidate, {})
            for index in range(destination.capacity):
                holder = slots.get(index)
                if holder is None or holder == agent_id:
                    return candidate
        return None

    def reserve_with_alternates(
        self, agent_id: str, waypoint: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Try the requested destination, then its declared siblings."""
        target = self.find_free(agent_id, waypoint)
        if target is None:
            return None, None

        self.release(agent_id)
        slot = self.reserve(agent_id, target)
        return (target, slot) if slot is not None else (None, None)


# Pipeline node -> the intents it should produce. Declarative, so adding a node
# does not mean editing a branch inside the graph driver.
NODE_CHOREOGRAPHY: Dict[str, List[Tuple[str, str, str, str]]] = {
    "manager_rfc_node": [
        ("researcher", "desk_elena", "Elena: Investigating approach and dependencies...", "Type"),
    ],
    "researcher_audit_node": [
        ("researcher", "whiteboard_researcher", "Elena: Sharing the research audit...", "Type"),
        ("developer", "desk_alex", "Alex: Turning research into a test contract...", "Type"),
    ],
    "tdd_contract_node": [
        ("researcher", "desk_elena", "Elena: Monitoring API specifications...", "Sit"),
        ("developer", "desk_alex", "Alex: Implementing main.py against the frozen suite...", "Type"),
    ],
    "developer_node": [
        ("qa", "desk_alex_review", "Maya: Scrutinising edge cases and races...", "Type"),
    ],
    "qa_audit_node": [
        ("qa", "whiteboard_qa", "Maya: Presenting audit findings...", "Walk"),
        ("manager", "whiteboard_manager", "David: Calling the team to the whiteboard...", "Sit"),
    ],
    "preflight_gate_node": [
        ("manager", "whiteboard_manager", "David: Bundle locked; digest on the board.", "Sit"),
    ],
    "sandbox_execution_node": [
        ("developer", "desk_alex", "Alex: Running the approved tests in the sandbox...", "Type"),
    ],
    "manager_final_report_node": [
        ("qa", "desk_maya", "Maya: Filing the audit record.", "Sit"),
        ("manager", "boss_room", "David: Delivering the outcome to BOSS...", "Walk"),
    ],
}


class OfficeDirector:
    """Owns every agent movement and status in the office."""

    TICK_SECONDS = 0.5

    def __init__(self, clock: OfficeClock) -> None:
        self._clock = clock
        self._bus = get_event_bus()
        self._occupancy = OccupancyTable()
        self._lock = threading.Lock()
        self._pending: Deque[Intent] = deque()
        self._actors: Dict[str, Actor] = {
            agent_id: Actor(
                agent_id=agent_id,
                location=home,
                needs=_needs_for(agent_id),
            )
            for agent_id, home in HOME_DESKS.items()
        }
        for actor in self._actors.values():
            self._occupancy.reserve(actor.agent_id, actor.location)

        self._last_sim_minutes = 0.0
        self._last_phase: Optional[str] = None
        self._pipeline_active = False

    # -- inbound, called from any thread ---------------------------------

    def submit(self, intent: Intent) -> None:
        with self._lock:
            self._pending.append(intent)

    def note_node_finished(self, node_name: str) -> None:
        """Translate pipeline progress into movement. Never blocks the caller."""
        self._pipeline_active = True
        for agent_id, destination, status, animation in NODE_CHOREOGRAPHY.get(node_name, ()):
            self.submit(
                Intent(
                    agent_id=agent_id,
                    destination=destination,
                    status_text=status,
                    animation=animation,
                    priority=Priority.PIPELINE_CRITICAL,
                    reason=f"after {node_name}",
                )
            )

    def note_gate_open(self) -> None:
        self.submit(
            Intent(
                agent_id="manager",
                destination="whiteboard_manager",
                status_text="David: Waiting for your decision at the whiteboard.",
                animation="Sit",
                priority=Priority.PIPELINE_CRITICAL,
                reason="human gate open",
            )
        )

    def note_run_finished(self) -> None:
        self._pipeline_active = False

    def note_provider_waiting(self, agent_id: str, seconds: float, reason: str) -> None:
        """A rate limit reads as a person waiting, not as a crash."""
        actor = self._actors.get(agent_id)
        if actor is None:
            return
        actor.waiting_on_provider = True
        self.submit(
            Intent(
                agent_id=agent_id,
                destination=HOME_DESKS.get(agent_id, actor.location),
                status_text=reason,
                animation="Wait",
                priority=Priority.PROVIDER_STATE,
                reason=f"rate limited for {seconds:.0f}s",
            )
        )

    def note_provider_recovered(self, agent_id: str) -> None:
        actor = self._actors.get(agent_id)
        if actor is not None:
            actor.waiting_on_provider = False

    def note_clock_out(self, agent_id: str, reason: str) -> None:
        """An exhausted quota walks the agent out through the door."""
        actor = self._actors.get(agent_id)
        if actor is None:
            return
        actor.clocked_out = True
        actor.waiting_on_provider = False
        self.submit(
            Intent(
                agent_id=agent_id,
                destination="exit",
                status_text=reason,
                animation="Walk",
                priority=Priority.PROVIDER_STATE,
                reason="quota exhausted",
            )
        )

    def note_clock_in(self, agent_id: str) -> None:
        actor = self._actors.get(agent_id)
        if actor is None:
            return
        actor.clocked_out = False
        self.submit(
            Intent(
                agent_id=agent_id,
                destination=HOME_DESKS.get(agent_id, "desk_david"),
                status_text=f"{AGENT_NAMES.get(agent_id, agent_id)}: Back at their desk.",
                animation="Walk",
                priority=Priority.PROVIDER_STATE,
                reason="quota window reset",
            )
        )

    # -- outbound --------------------------------------------------------

    def _dispatch_move(self, actor: Actor, destination: str, slot_id: str, intent: Intent) -> None:
        self._bus.dispatch(
            AgentMoveEvent(
                agent_id=actor.agent_id,
                from_node=actor.location,
                to_node=destination,
                action=intent.animation if intent.animation == "Walk" else "Walk",
                slot_id=slot_id,
                reason=intent.reason,
                priority=PRIORITY_NAMES[intent.priority],
            )
        )
        self._bus.dispatch(
            AgentStatusEvent(
                agent_id=actor.agent_id,
                status_text=intent.status_text,
                animation=intent.animation,
            )
        )

    def _apply(self, intent: Intent, sim_minutes: float) -> None:
        actor = self._actors.get(intent.agent_id)
        if actor is None:
            return

        # Arbitration: a lower-priority intent cannot displace an agent who is
        # mid-commitment at a higher priority. A coffee break therefore cannot
        # pull someone away from presenting at the gate.
        if intent.priority < actor.priority and actor.dwell_until is not None:
            return

        destination, slot_id = self._occupancy.reserve_with_alternates(
            intent.agent_id, intent.destination
        )
        if destination is None or slot_id is None:
            # Everywhere suitable is taken; re-queue and try on a later tick.
            self._occupancy.reserve(actor.agent_id, actor.location)
            with self._lock:
                self._pending.append(intent)
            return

        self._dispatch_move(actor, destination, slot_id, intent)

        actor.location = destination
        actor.slot_id = slot_id
        actor.priority = intent.priority
        actor.dwell_until = (
            sim_minutes + intent.dwell_sim_minutes if intent.dwell_sim_minutes else None
        )
        actor.present = destination != "exit"

        if intent.break_type:
            self._bus.dispatch(
                AgentBreakEvent(
                    agent_id=actor.agent_id,
                    break_type=intent.break_type,
                    destination=destination,
                    duration_sim_minutes=intent.dwell_sim_minutes,
                    returning=False,
                )
            )

    def _send_home(self, actor: Actor, sim_minutes: float) -> None:
        # Release the commitment *before* dispatching, otherwise the
        # arbitration check in `_apply` would reject this lower-priority
        # intent and the agent would never leave their break.
        actor.priority = Priority.AMBIENT_IDLE
        actor.dwell_until = None

        home = HOME_DESKS.get(actor.agent_id, "desk_david")
        name = AGENT_NAMES.get(actor.agent_id, actor.agent_id)
        self._apply(
            Intent(
                agent_id=actor.agent_id,
                destination=home,
                status_text=f"{name}: Back at their desk.",
                animation="Sit",
                priority=Priority.AMBIENT_IDLE,
                reason="returning from a break",
                return_home=True,
            ),
            sim_minutes,
        )

    def _consider_break(self, actor: Actor, sim_minutes: float) -> None:
        """Utility selection: the strongest unmet need wins, if anywhere is free."""
        if actor.clocked_out or actor.waiting_on_provider:
            return
        if actor.priority > Priority.SCHEDULED_BREAK or actor.dwell_until is not None:
            return

        ranked = sorted(actor.needs, key=lambda need: need.level, reverse=True)
        for need in ranked:
            if need.level < 1.0:
                break
            # Non-mutating feasibility check: if everywhere suitable is taken,
            # keep the need elevated and try again on a later tick.
            if self._occupancy.find_free(actor.agent_id, need.destination) is None:
                continue

            name = AGENT_NAMES.get(actor.agent_id, actor.agent_id)
            self._apply(
                Intent(
                    agent_id=actor.agent_id,
                    destination=need.destination,
                    status_text=need.status.format(name=name),
                    animation=need.animation,
                    priority=Priority.SCHEDULED_BREAK,
                    reason=f"{need.name} break",
                    dwell_sim_minutes=need.dwell_sim_minutes,
                    break_type=need.break_type,
                ),
                sim_minutes,
            )
            need.satisfy()
            return

    def _clock_out_everyone(self) -> None:
        for actor in self._actors.values():
            self._apply(
                Intent(
                    agent_id=actor.agent_id,
                    destination="exit",
                    status_text="Clocking out for the day...",
                    animation="Walk",
                    priority=Priority.PIPELINE_CRITICAL,
                    reason="end of workday",
                ),
                0.0,
            )
            actor.priority = Priority.AMBIENT_IDLE
            actor.dwell_until = None

    def _clock_in_everyone(self) -> None:
        for actor in self._actors.values():
            for need in actor.needs:
                need.satisfy()
            self._apply(
                Intent(
                    agent_id=actor.agent_id,
                    destination=HOME_DESKS[actor.agent_id],
                    status_text="Arriving for a new day...",
                    animation="Walk",
                    priority=Priority.PIPELINE_CRITICAL,
                    reason="start of workday",
                ),
                0.0,
            )
            actor.priority = Priority.AMBIENT_IDLE
            actor.dwell_until = None

    # -- the loop --------------------------------------------------------

    def tick(self) -> None:
        snapshot = self._clock.snapshot()
        sim_minutes = float(snapshot.sim_minutes_since_open)

        if snapshot.phase != self._last_phase:
            if snapshot.phase == "OFF_HOURS":
                self._clock_out_everyone()
            elif self._last_phase == "OFF_HOURS":
                self._clock_in_everyone()
            self._last_phase = snapshot.phase

        elapsed_sim = max(0.0, sim_minutes - self._last_sim_minutes)
        self._last_sim_minutes = sim_minutes

        if snapshot.phase == "WORKDAY":
            for actor in self._actors.values():
                for need in actor.needs:
                    need.accumulate(elapsed_sim)

        with self._lock:
            queued = list(self._pending)
            self._pending.clear()

        # Highest priority first, so a gate presentation is never queued behind
        # someone strolling to the espresso bar.
        for intent in sorted(queued, key=lambda item: -int(item.priority)):
            self._apply(intent, sim_minutes)

        if snapshot.phase != "WORKDAY":
            return

        for actor in self._actors.values():
            if actor.dwell_until is not None and sim_minutes >= actor.dwell_until:
                self._send_home(actor, sim_minutes)

            # Ambient life continues during a live run. The old frontend loop
            # disabled itself whenever isRunning was true, which removed all
            # office life at exactly the moment there was something to watch.
            if actor.priority <= Priority.SCHEDULED_BREAK:
                self._consider_break(actor, sim_minutes)

    async def run(self) -> None:
        """Drive the office until cancelled."""
        from ai_team.providers.resilience import announce_recoveries

        last_schedule_tick = 0.0
        while True:
            try:
                self.tick()

                now = time.monotonic()
                if now - last_schedule_tick >= 5.0:
                    last_schedule_tick = now
                    snapshot = self._clock.snapshot()
                    self._bus.dispatch(
                        OfficeScheduleTickEvent(
                            sim_minutes_since_open=snapshot.sim_minutes_since_open,
                            display_time=format_sim_time(snapshot.sim_minutes_since_open),
                            day_number=snapshot.day_number,
                        )
                    )
                    # Bring anyone back whose quota window has rolled over.
                    announce_recoveries()
            except asyncio.CancelledError:
                raise
            except Exception as err:
                print(f"  [Director] tick failed: {err}")

            await asyncio.sleep(self.TICK_SECONDS)


_director: Optional[OfficeDirector] = None


def get_director(clock: Optional[OfficeClock] = None) -> OfficeDirector:
    global _director
    if _director is None:
        _director = OfficeDirector(clock or OfficeClock())
    return _director


def reset_director() -> None:
    """Test helper: drop the singleton."""
    global _director
    _director = None
