"""Tests for SimulationState."""

import pytest

from fly_in.domain.connection import Connection
from fly_in.domain.drone import Drone
from fly_in.domain.zone import Zone, ZoneType
from fly_in.simulation.drone_state import DroneStatus
from fly_in.simulation.simulation_state import SimulationState
from fly_in.simulation.transit_state import TransitState


def make_drones(count: int) -> list[Drone]:
    """Create drones with identifiers starting at one."""
    return [Drone(drone_id) for drone_id in range(1, count + 1)]


def test_initializes_every_drone_at_start_zone() -> None:
    """Create the initial state at turn zero."""
    start = Zone("start", 0, 0)
    drones = make_drones(3)

    state = SimulationState(drones, start)

    assert state.turn_number == 0
    assert state.drone_count == 3
    assert state.zone_occupancy(start) == 3
    assert len(state.drone_states) == 3
    assert not state.all_delivered

    for drone_state in state.drone_states:
        assert drone_state.status is DroneStatus.AT_ZONE
        assert drone_state.current_zone is start


def test_rejects_duplicate_drone_identifiers() -> None:
    """Require each drone identifier to be unique."""
    start = Zone("start", 0, 0)
    drones = [Drone(1), Drone(1)]

    with pytest.raises(
        ValueError,
        match="Duplicate drone identifier: 1",
    ):
        SimulationState(drones, start)


def test_returns_state_by_drone_identifier() -> None:
    """Retrieve the state associated with one drone."""
    start = Zone("start", 0, 0)
    drones = make_drones(2)
    state = SimulationState(drones, start)

    drone_state = state.get_drone_state(2)

    assert drone_state.drone is drones[1]
    assert drone_state.current_zone is start


def test_rejects_unknown_drone_identifier() -> None:
    """Raise a clear error for an unknown drone."""
    state = SimulationState(
        make_drones(1),
        Zone("start", 0, 0),
    )

    with pytest.raises(
        KeyError,
        match="Unknown drone identifier: 99",
    ):
        state.get_drone_state(99)


def test_zone_queries_reflect_current_drone_states() -> None:
    """Derive zone occupancy from the individual states."""
    start = Zone("start", 0, 0)
    middle = Zone("middle", 1, 0)
    state = SimulationState(make_drones(3), start)

    state.get_drone_state(1).move_to(middle)
    state.get_drone_state(2).move_to(middle)

    middle_states = state.states_at_zone(middle)

    assert state.zone_occupancy(start) == 1
    assert state.zone_occupancy(middle) == 2
    assert {
        drone_state.drone.drone_id
        for drone_state in middle_states
    } == {1, 2}


def test_transit_queries_reflect_active_connection_use() -> None:
    """Count drones currently occupying a connection."""
    start = Zone("start", 0, 0)
    restricted = Zone(
        "restricted",
        1,
        0,
        ZoneType.RESTRICTED,
    )
    connection = Connection(start, restricted, max_capacity=2)
    state = SimulationState(make_drones(3), start)

    for drone_id in (1, 2):
        transit = TransitState(connection, restricted)
        state.get_drone_state(drone_id).start_transit(transit)

    transit_states = state.states_in_transit()
    connection_states = state.states_using_connection(connection)

    assert len(transit_states) == 2
    assert len(connection_states) == 2
    assert state.connection_occupancy(connection) == 2
    assert state.zone_occupancy(start) == 1
    assert {
        drone_state.drone.drone_id
        for drone_state in connection_states
    } == {1, 2}


def test_completed_transit_updates_occupancy_queries() -> None:
    """Move occupancy from the connection to the destination."""
    start = Zone("start", 0, 0)
    restricted = Zone(
        "restricted",
        1,
        0,
        ZoneType.RESTRICTED,
    )
    connection = Connection(start, restricted)
    state = SimulationState(make_drones(1), start)
    drone_state = state.get_drone_state(1)
    drone_state.start_transit(
        TransitState(connection, restricted)
    )

    drone_state.advance_transit()

    assert state.connection_occupancy(connection) == 0
    assert state.zone_occupancy(start) == 0
    assert state.zone_occupancy(restricted) == 1
    assert state.states_in_transit() == ()


def test_delivered_queries_and_all_delivered() -> None:
    """Track delivered drones and completion of the simulation."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    state = SimulationState(make_drones(2), start)

    first = state.get_drone_state(1)
    first.move_to(end)
    first.mark_delivered(end)

    assert state.delivered_count == 1
    assert len(state.delivered_states()) == 1
    assert not state.all_delivered
    assert state.zone_occupancy(end) == 1

    second = state.get_drone_state(2)
    second.move_to(end)
    second.mark_delivered(end)

    assert state.delivered_count == 2
    assert state.all_delivered
    assert state.zone_occupancy(end) == 2


def test_advance_turn_only_changes_turn_counter() -> None:
    """Advance the turn without replacing drone states."""
    start = Zone("start", 0, 0)
    state = SimulationState(make_drones(1), start)
    drone_state = state.get_drone_state(1)

    state.advance_turn()
    state.advance_turn()

    assert state.turn_number == 2
    assert state.get_drone_state(1) is drone_state
    assert state.zone_occupancy(start) == 1
