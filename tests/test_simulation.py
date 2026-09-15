"""Tests for complete simulation-turn execution."""

import pytest

from fly_in.domain.connection import Connection
from fly_in.domain.drone import Drone
from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone, ZoneType
from fly_in.errors import MovementValidationError
from fly_in.simulation.movement import Movement
from fly_in.simulation.simulation import Simulation
from fly_in.simulation.simulation_state import SimulationState


def make_simulation(
    zones: list[Zone],
    connections: list[Connection],
    start: Zone,
    end: Zone,
    drone_count: int = 1,
) -> Simulation:
    """Create a simulation with sequential drone identifiers."""
    graph = Graph(
        zones=zones,
        connections=connections,
        start_zone=start,
        end_zone=end,
    )
    drones = [
        Drone(drone_id)
        for drone_id in range(1, drone_count + 1)
    ]
    state = SimulationState(drones, start)

    return Simulation(graph, state)


def test_applies_one_turn_movement() -> None:
    """Move a drone immediately into a normal zone."""
    start = Zone("start", 0, 0)
    middle = Zone("middle", 1, 0)
    end = Zone("end", 2, 0)
    connection = Connection(start, middle)
    simulation = make_simulation(
        [start, middle, end],
        [connection],
        start,
        end,
    )

    simulation.apply_turn(
        [Movement(1, start, middle, connection)]
    )

    drone_state = simulation.state.get_drone_state(1)

    assert drone_state.current_zone is middle
    assert drone_state.is_at_zone
    assert simulation.state.turn_number == 1


def test_starts_restricted_transit_without_advancing_it() -> None:
    """Keep a new restricted movement in transit for this turn."""
    start = Zone("start", 0, 0)
    restricted = Zone(
        "restricted",
        1,
        0,
        zone_type=ZoneType.RESTRICTED,
    )
    end = Zone("end", 2, 0)
    connection = Connection(start, restricted)
    simulation = make_simulation(
        [start, restricted, end],
        [connection],
        start,
        end,
    )

    simulation.apply_turn(
        [Movement(1, start, restricted, connection)]
    )

    drone_state = simulation.state.get_drone_state(1)

    assert drone_state.is_in_transit
    assert drone_state.current_zone is None
    assert drone_state.transit is not None
    assert drone_state.transit.remaining_turns == 1
    assert simulation.state.turn_number == 1


def test_advances_transit_existing_at_turn_start() -> None:
    """Complete a restricted movement on the following turn."""
    start = Zone("start", 0, 0)
    restricted = Zone(
        "restricted",
        1,
        0,
        zone_type=ZoneType.RESTRICTED,
    )
    end = Zone("end", 2, 0)
    connection = Connection(start, restricted)
    simulation = make_simulation(
        [start, restricted, end],
        [connection],
        start,
        end,
    )

    simulation.apply_turn(
        [Movement(1, start, restricted, connection)]
    )
    simulation.apply_turn([])

    drone_state = simulation.state.get_drone_state(1)

    assert drone_state.is_at_zone
    assert drone_state.current_zone is restricted
    assert drone_state.transit is None
    assert simulation.state.turn_number == 2


def test_moves_multiple_drones_simultaneously() -> None:
    """Apply independent movements in one turn."""
    start = Zone("start", 0, 0)
    zone_a = Zone("zone_a", 1, 0)
    zone_b = Zone("zone_b", 1, 1)
    end = Zone("end", 2, 0)
    connection_a = Connection(start, zone_a)
    connection_b = Connection(start, zone_b)
    simulation = make_simulation(
        [start, zone_a, zone_b, end],
        [connection_a, connection_b],
        start,
        end,
        drone_count=2,
    )

    simulation.apply_turn(
        [
            Movement(1, start, zone_a, connection_a),
            Movement(2, start, zone_b, connection_b),
        ]
    )

    assert (
        simulation.state.get_drone_state(1).current_zone
        is zone_a
    )
    assert (
        simulation.state.get_drone_state(2).current_zone
        is zone_b
    )
    assert simulation.state.turn_number == 1


def test_drone_without_movement_stays_in_place() -> None:
    """Keep waiting drones at their current zones."""
    start = Zone("start", 0, 0)
    middle = Zone("middle", 1, 0)
    end = Zone("end", 2, 0)
    connection = Connection(start, middle)
    simulation = make_simulation(
        [start, middle, end],
        [connection],
        start,
        end,
        drone_count=2,
    )

    simulation.apply_turn(
        [Movement(1, start, middle, connection)]
    )

    assert (
        simulation.state.get_drone_state(1).current_zone
        is middle
    )
    assert (
        simulation.state.get_drone_state(2).current_zone
        is start
    )


def test_marks_direct_arrival_as_delivered() -> None:
    """Deliver a drone that moves directly into the end zone."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    connection = Connection(start, end)
    simulation = make_simulation(
        [start, end],
        [connection],
        start,
        end,
    )

    simulation.apply_turn(
        [Movement(1, start, end, connection)]
    )

    drone_state = simulation.state.get_drone_state(1)

    assert drone_state.is_delivered
    assert drone_state.current_zone is end
    assert simulation.state.delivered_count == 1
    assert simulation.is_complete


def test_marks_transit_arrival_as_delivered() -> None:
    """Deliver a drone after a multi-turn arrival at the end."""
    start = Zone("start", 0, 0)
    end = Zone(
        "end",
        1,
        0,
        zone_type=ZoneType.RESTRICTED,
    )
    connection = Connection(start, end)
    simulation = make_simulation(
        [start, end],
        [connection],
        start,
        end,
    )

    simulation.apply_turn(
        [Movement(1, start, end, connection)]
    )

    assert not simulation.is_complete

    simulation.apply_turn([])

    drone_state = simulation.state.get_drone_state(1)

    assert drone_state.is_delivered
    assert drone_state.current_zone is end
    assert simulation.is_complete


def test_invalid_turn_does_not_modify_state() -> None:
    """Validate the complete turn before changing any drone."""
    start = Zone("start", 0, 0)
    middle = Zone("middle", 1, 0)
    blocked = Zone(
        "blocked",
        1,
        1,
        zone_type=ZoneType.BLOCKED,
    )
    end = Zone("end", 2, 0)
    middle_connection = Connection(start, middle)
    blocked_connection = Connection(start, blocked)
    simulation = make_simulation(
        [start, middle, blocked, end],
        [middle_connection, blocked_connection],
        start,
        end,
        drone_count=2,
    )

    movements = [
        Movement(1, start, middle, middle_connection),
        Movement(2, start, blocked, blocked_connection),
    ]

    with pytest.raises(MovementValidationError):
        simulation.apply_turn(movements)

    assert (
        simulation.state.get_drone_state(1).current_zone
        is start
    )
    assert (
        simulation.state.get_drone_state(2).current_zone
        is start
    )
    assert simulation.state.turn_number == 0


def test_empty_turn_advances_turn_counter() -> None:
    """Represent a complete turn where every drone waits."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    connection = Connection(start, end)
    simulation = make_simulation(
        [start, end],
        [connection],
        start,
        end,
    )

    simulation.apply_turn([])

    assert simulation.state.turn_number == 1
    assert (
        simulation.state.get_drone_state(1).current_zone
        is start
    )


def test_all_delivered_after_last_drone_arrives() -> None:
    """Complete the simulation only after every drone arrives."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    connection = Connection(
        start,
        end,
        max_capacity=2,
    )
    simulation = make_simulation(
        [start, end],
        [connection],
        start,
        end,
        drone_count=2,
    )

    simulation.apply_turn(
        [
            Movement(1, start, end, connection),
            Movement(2, start, end, connection),
        ]
    )

    assert simulation.state.delivered_count == 2
    assert simulation.state.all_delivered
    assert simulation.is_complete
