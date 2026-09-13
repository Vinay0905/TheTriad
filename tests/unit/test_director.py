"""The Director arbitrates behaviour and, crucially, never double-books a seat."""

import pytest

from ai_team.spatial.director import (
    DESTINATIONS,
    HOME_DESKS,
    Intent,
    OccupancyTable,
    OfficeDirector,
    Priority,
)
from ai_team.spatial.office_clock import OfficeClock


@pytest.fixture(autouse=True)
def silent_bus(monkeypatch):
    """Swallow office events; these tests are about decisions, not broadcasts."""
    dispatched = []

    class FakeBus:
        def dispatch(self, event):
            dispatched.append(event)

    monkeypatch.setattr(
        "ai_team.spatial.director.get_event_bus", lambda: FakeBus()
    )
    return dispatched


@pytest.fixture
def director():
    return OfficeDirector(OfficeClock())


# -- occupancy ---------------------------------------------------------


def test_single_occupancy_desk_admits_one_agent():
    table = OccupancyTable()
    assert table.reserve("developer", "desk_alex") == "desk_alex#0"
    assert table.reserve("qa", "desk_alex") is None


def test_reserving_twice_is_idempotent_for_the_same_agent():
    table = OccupancyTable()
    first = table.reserve("developer", "desk_alex")
    assert table.reserve("developer", "desk_alex") == first


def test_shared_destination_hands_out_distinct_slots():
    """Two people at the espresso bar must not occupy the same point."""
    table = OccupancyTable()
    first = table.reserve("developer", "pantry")
    second = table.reserve("manager", "pantry")

    assert first is not None and second is not None
    assert first != second

    # Capacity is two, so a third has to wait.
    assert table.reserve("qa", "pantry") is None


def test_release_frees_the_slot():
    table = OccupancyTable()
    table.reserve("developer", "desk_alex")
    table.release("developer")
    assert table.reserve("qa", "desk_alex") == "desk_alex#0"


def test_alternates_are_used_when_the_preferred_station_is_taken():
    table = OccupancyTable()
    table.reserve("qa", "whiteboard_qa")

    # whiteboard_qa is taken, so its declared sibling is offered instead.
    destination, slot = table.reserve_with_alternates("manager", "whiteboard_qa")
    assert destination == "whiteboard_researcher"
    assert slot == "whiteboard_researcher#0"


def test_reserve_with_alternates_gives_up_when_everything_is_taken():
    table = OccupancyTable()
    table.reserve("qa", "whiteboard_qa")
    table.reserve("manager", "whiteboard_researcher")

    destination, slot = table.reserve_with_alternates("researcher", "whiteboard_qa")
    assert destination is None
    assert slot is None


def test_feasibility_probe_does_not_move_an_existing_claim():
    """`find_free` must be side-effect free, or probing would steal slots."""
    table = OccupancyTable()
    table.reserve("developer", "desk_alex")

    assert table.find_free("developer", "pantry") == "pantry"
    # The developer still holds their desk after the probe.
    assert table.reserve("qa", "desk_alex") is None


def test_every_choreographed_destination_exists():
    """A typo in the choreography table would silently strand an agent."""
    from ai_team.spatial.director import NODE_CHOREOGRAPHY, _needs_for

    for intents in NODE_CHOREOGRAPHY.values():
        for _agent, destination, _status, _animation in intents:
            assert destination in DESTINATIONS, destination

    for agent_id in HOME_DESKS:
        for need in _needs_for(agent_id):
            assert need.destination in DESTINATIONS, need.destination


# -- arbitration -------------------------------------------------------


def test_two_agents_are_never_sent_to_the_same_seat(director):
    director.submit(
        Intent(
            agent_id="developer",
            destination="desk_alex",
            status_text="working",
            priority=Priority.PIPELINE_CRITICAL,
        )
    )
    director.submit(
        Intent(
            agent_id="qa",
            destination="desk_alex",
            status_text="also working",
            priority=Priority.PIPELINE_CRITICAL,
        )
    )
    director.tick()

    locations = {
        actor.agent_id: (actor.location, actor.slot_id)
        for actor in director._actors.values()
    }
    occupied = [value for value in locations.values() if value[0] == "desk_alex"]
    assert len(occupied) == 1, "desk_alex must hold at most one agent"


def test_pipeline_work_outranks_a_coffee_break(director):
    actor = director._actors["developer"]

    # Put the developer on a break with a dwell.
    director.submit(
        Intent(
            agent_id="developer",
            destination="pantry",
            status_text="coffee",
            priority=Priority.SCHEDULED_BREAK,
            dwell_sim_minutes=15,
            break_type="COFFEE",
        )
    )
    director.tick()
    assert actor.location == "pantry"

    # A gate presentation must pull them back regardless.
    director.submit(
        Intent(
            agent_id="developer",
            destination="desk_alex",
            status_text="implementing",
            priority=Priority.PIPELINE_CRITICAL,
        )
    )
    director.tick()
    assert actor.location == "desk_alex"
    assert actor.priority == Priority.PIPELINE_CRITICAL


def test_ambient_intent_cannot_displace_pipeline_work(director):
    actor = director._actors["manager"]
    director.submit(
        Intent(
            agent_id="manager",
            destination="whiteboard_manager",
            status_text="presenting",
            priority=Priority.PIPELINE_CRITICAL,
            dwell_sim_minutes=30,
        )
    )
    director.tick()
    assert actor.location == "whiteboard_manager"

    director.submit(
        Intent(
            agent_id="manager",
            destination="pantry",
            status_text="coffee",
            priority=Priority.AMBIENT_IDLE,
        )
    )
    director.tick()
    assert actor.location == "whiteboard_manager"


def test_quota_exhaustion_walks_the_agent_out(director):
    director.note_clock_out("qa", "GLM quota exhausted")
    director.tick()

    actor = director._actors["qa"]
    assert actor.location == "exit"
    assert actor.clocked_out is True
    assert actor.present is False


def test_clocking_back_in_returns_them_to_their_desk(director):
    director.note_clock_out("qa", "quota exhausted")
    director.tick()
    director.note_clock_in("qa")
    director.tick()

    actor = director._actors["qa"]
    assert actor.location == HOME_DESKS["qa"]
    assert actor.clocked_out is False
    assert actor.present is True


def test_a_clocked_out_agent_does_not_take_coffee_breaks(director):
    actor = director._actors["developer"]
    actor.clocked_out = True
    for need in actor.needs:
        need.level = 5.0

    director._consider_break(actor, sim_minutes=100.0)
    assert actor.location == HOME_DESKS["developer"]


def test_a_waiting_agent_stays_at_their_desk(director):
    """A rate limit should look like waiting, not like wandering off."""
    director.note_provider_waiting("developer", 20.0, "Groq is rate limiting")
    director.tick()

    actor = director._actors["developer"]
    assert actor.waiting_on_provider is True
    assert actor.location == HOME_DESKS["developer"]

    for need in actor.needs:
        need.level = 5.0
    director._consider_break(actor, sim_minutes=100.0)
    assert actor.location == HOME_DESKS["developer"]


def test_node_choreography_never_blocks_the_caller(director):
    """note_node_finished only enqueues; it must not move anyone inline."""
    director.note_node_finished("qa_audit_node")
    assert len(director._pending) > 0
    assert director._actors["qa"].location == HOME_DESKS["qa"]


def test_needs_accumulate_in_sim_time(director):
    actor = director._actors["developer"]
    coffee = next(need for need in actor.needs if need.name == "coffee")
    assert coffee.level == 0.0

    # One full period of sim-minutes should bring it to the threshold.
    coffee.accumulate(coffee.period_sim_minutes)
    assert coffee.level >= 1.0

    coffee.satisfy()
    assert coffee.level <= 0.0
