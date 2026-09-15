"""Tests for simultaneous movement validation."""

import pytest

from fly_in.domain.connection import Connection
from fly_in.domain.drone import Drone
from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone, ZoneType
from fly_in.errors import MovementValidationError
from fly_in.simulation.movement import Movement
from fly_in.simulation.movement_validator import MovementValidator
from fly_in.simulation.simulation_state import SimulationState
from fly_in.simulation.transit_state import TransitState


def make_graph(
    zones: list[Zone],
    connections: list[Connection],
    start: Zone,
    end: Zone,
) -> Graph:
    """Create a graph for movement-validator tests."""
    return Graph(
        zones=zones,
        connections=connections,
        start_zone=start,
        end_zone=end,
    )


def make_state(
    drone_count: int,
    start: Zone,
) -> SimulationState:
    """Create a simulation state with sequential drone IDs."""
    drones = [
        Drone(drone_id)
        for drone_id in range(1, drone_count + 1)
    ]
    return SimulationState(drones, start)


def test_accepts_empty_movement_list() -> None:
    """Allow a turn where no drone starts a movement."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    graph = make_graph(
        [start, end],
        [Connection(start, end)],
        start,
        end,
    )
    state = make_state(1, start)

    MovementValidator().validate(graph, state, [])


def test_accepts_valid_normal_movement() -> None:
    """Accept a movement matching the current drone state."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    connection = Connection(start, end)
    graph = make_graph(
        [start, end],
        [connection],
        start,
        end,
    )
    state = make_state(1, start)
    movement = Movement(1, start, end, connection)

    MovementValidator().validate(
        graph,
        state,
        [movement],
    )


def test_rejects_multiple_movements_for_same_drone() -> None:
    """Prevent one drone from moving twice in one turn."""
    start = Zone("start", 0, 0)
    zone_a = Zone("zone_a", 1, 0)
    zone_b = Zone("zone_b", 1, 1)
    end = Zone("end", 2, 0)
    connection_a = Connection(start, zone_a)
    connection_b = Connection(start, zone_b)
    graph = make_graph(
        [start, zone_a, zone_b, end],
        [connection_a, connection_b],
        start,
        end,
    )
    state = make_state(1, start)
    movements = [
        Movement(1, start, zone_a, connection_a),
        Movement(1, start, zone_b, connection_b),
    ]

    with pytest.raises(
        MovementValidationError,
        match="multiple movements",
    ):
        MovementValidator().validate(
            graph,
            state,
            movements,
        )


def test_rejects_unknown_drone() -> None:
    """Reject a movement whose drone is absent from the state."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    connection = Connection(start, end)
    graph = make_graph(
        [start, end],
        [connection],
        start,
        end,
    )
    state = make_state(1, start)
    movement = Movement(2, start, end, connection)

    with pytest.raises(
        MovementValidationError,
        match="Unknown drone identifier",
    ):
        MovementValidator().validate(
            graph,
            state,
            [movement],
        )


def test_rejects_drone_currently_in_transit() -> None:
    """Prevent a drone in transit from starting another movement."""
    start = Zone("start", 0, 0)
    restricted = Zone(
        "restricted",
        1,
        0,
        zone_type=ZoneType.RESTRICTED,
    )
    end = Zone("end", 2, 0)
    connection = Connection(start, restricted)
    graph = make_graph(
        [start, restricted, end],
        [connection],
        start,
        end,
    )
    state = make_state(1, start)
    state.get_drone_state(1).start_transit(
        TransitState(connection, restricted)
    )
    movement = Movement(1, start, restricted, connection)

    with pytest.raises(
        MovementValidationError,
        match="not available at a zone",
    ):
        MovementValidator().validate(
            graph,
            state,
            [movement],
        )


def test_rejects_delivered_drone() -> None:
    """Prevent a delivered drone from moving again."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    connection = Connection(start, end)
    graph = make_graph(
        [start, end],
        [connection],
        start,
        end,
    )
    state = make_state(1, start)
    drone_state = state.get_drone_state(1)
    drone_state.move_to(end)
    drone_state.mark_delivered(end)
    movement = Movement(1, end, start, connection)

    with pytest.raises(
        MovementValidationError,
        match="not available at a zone",
    ):
        MovementValidator().validate(
            graph,
            state,
            [movement],
        )


def test_rejects_origin_different_from_drone_position() -> None:
    """Require the movement origin to match the current zone."""
    start = Zone("start", 0, 0)
    zone_a = Zone("zone_a", 1, 0)
    end = Zone("end", 2, 0)
    connection = Connection(zone_a, end)
    graph = make_graph(
        [start, zone_a, end],
        [connection],
        start,
        end,
    )
    state = make_state(1, start)
    movement = Movement(1, zone_a, end, connection)

    with pytest.raises(
        MovementValidationError,
        match="is not at zone",
    ):
        MovementValidator().validate(
            graph,
            state,
            [movement],
        )


def test_rejects_blocked_destination() -> None:
    """Prevent movement into a blocked zone."""
    start = Zone("start", 0, 0)
    blocked = Zone(
        "blocked",
        1,
        0,
        zone_type=ZoneType.BLOCKED,
    )
    end = Zone("end", 2, 0)
    connection = Connection(start, blocked)
    graph = make_graph(
        [start, blocked, end],
        [connection],
        start,
        end,
    )
    state = make_state(1, start)
    movement = Movement(1, start, blocked, connection)

    with pytest.raises(
        MovementValidationError,
        match="is not accessible",
    ):
        MovementValidator().validate(
            graph,
            state,
            [movement],
        )


def test_rejects_connection_outside_graph() -> None:
    """Require the exact movement connection to belong to the graph."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    graph_connection = Connection(start, end)
    external_connection = Connection(start, end)
    graph = make_graph(
        [start, end],
        [graph_connection],
        start,
        end,
    )
    state = make_state(1, start)
    movement = Movement(
        1,
        start,
        end,
        external_connection,
    )

    with pytest.raises(
        MovementValidationError,
        match="does not belong to the graph",
    ):
        MovementValidator().validate(
            graph,
            state,
            [movement],
        )


def test_rejects_zone_capacity_overflow() -> None:
    """Reject simultaneous entries beyond a zone capacity."""
    start = Zone("start", 0, 0)
    target = Zone("target", 1, 0, max_drones=1)
    end = Zone("end", 2, 0)
    connection = Connection(
        start,
        target,
        max_capacity=2,
    )
    graph = make_graph(
        [start, target, end],
        [connection],
        start,
        end,
    )
    state = make_state(2, start)
    movements = [
        Movement(1, start, target, connection),
        Movement(2, start, target, connection),
    ]

    with pytest.raises(
        MovementValidationError,
        match="exceeds its capacity",
    ):
        MovementValidator().validate(
            graph,
            state,
            movements,
        )


def test_allows_simultaneous_zone_exit_and_entry() -> None:
    """Count a zone vacancy released in the same turn."""
    start = Zone("start", 0, 0)
    target = Zone("target", 1, 0, max_drones=1)
    end = Zone("end", 2, 0)
    start_target = Connection(start, target)
    target_end = Connection(target, end)
    graph = make_graph(
        [start, target, end],
        [start_target, target_end],
        start,
        end,
    )
    state = make_state(2, start)
    state.get_drone_state(1).move_to(target)
    movements = [
        Movement(1, target, end, target_end),
        Movement(2, start, target, start_target),
    ]

    MovementValidator().validate(
        graph,
        state,
        movements,
    )


def test_start_zone_has_unlimited_capacity() -> None:
    """Ignore the configured capacity of the start zone."""
    start = Zone("start", 0, 0, max_drones=1)
    middle = Zone("middle", 1, 0)
    end = Zone("end", 2, 0)
    connection = Connection(start, middle)
    graph = make_graph(
        [start, middle, end],
        [connection],
        start,
        end,
    )
    state = make_state(2, start)
    state.get_drone_state(1).move_to(middle)
    movement = Movement(1, middle, start, connection)

    MovementValidator().validate(
        graph,
        state,
        [movement],
    )


def test_end_zone_has_unlimited_capacity() -> None:
    """Allow many drones to enter the end zone together."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0, max_drones=1)
    connection = Connection(
        start,
        end,
        max_capacity=2,
    )
    graph = make_graph(
        [start, end],
        [connection],
        start,
        end,
    )
    state = make_state(2, start)
    movements = [
        Movement(1, start, end, connection),
        Movement(2, start, end, connection),
    ]

    MovementValidator().validate(
        graph,
        state,
        movements,
    )


def test_restricted_entry_does_not_fill_zone_immediately() -> None:
    """Keep a new restricted movement outside its destination."""
    start = Zone("start", 0, 0)
    restricted = Zone(
        "restricted",
        1,
        0,
        zone_type=ZoneType.RESTRICTED,
        max_drones=1,
    )
    end = Zone("end", 2, 0)
    connection = Connection(start, restricted)
    graph = make_graph(
        [start, restricted, end],
        [connection],
        start,
        end,
    )
    state = make_state(2, start)
    first_state = state.get_drone_state(1)
    first_state.start_transit(
        TransitState(connection, restricted)
    )
    first_state.advance_transit()
    movement = Movement(2, start, restricted, connection)

    MovementValidator().validate(
        graph,
        state,
        [movement],
    )


def test_rejects_forced_arrivals_beyond_zone_capacity() -> None:
    """Reject unavoidable arrivals exceeding future capacity."""
    start = Zone("start", 0, 0)
    restricted = Zone(
        "restricted",
        1,
        0,
        zone_type=ZoneType.RESTRICTED,
        max_drones=1,
    )
    end = Zone("end", 2, 0)
    connection = Connection(
        start,
        restricted,
        max_capacity=2,
    )
    graph = make_graph(
        [start, restricted, end],
        [connection],
        start,
        end,
    )
    state = make_state(2, start)
    movements = [
        Movement(1, start, restricted, connection),
        Movement(2, start, restricted, connection),
    ]

    with pytest.raises(
        MovementValidationError,
        match="forced arrivals",
    ):
        MovementValidator().validate(
            graph,
            state,
            movements,
        )


def test_counts_transit_arrival_in_current_zone_projection() -> None:
    """Include a transit completing during the current turn."""
    start = Zone("start", 0, 0)
    restricted = Zone(
        "restricted",
        1,
        0,
        zone_type=ZoneType.RESTRICTED,
        max_drones=1,
    )
    end = Zone("end", 2, 0)
    connection = Connection(
        start,
        restricted,
        max_capacity=2,
    )
    graph = make_graph(
        [start, restricted, end],
        [connection],
        start,
        end,
    )
    state = make_state(2, start)
    arriving_state = state.get_drone_state(1)
    occupying_state = state.get_drone_state(2)
    arriving_state.start_transit(
        TransitState(connection, restricted)
    )
    occupying_state.start_transit(
        TransitState(connection, restricted)
    )
    occupying_state.advance_transit()

    with pytest.raises(
        MovementValidationError,
        match="exceeds its capacity",
    ):
        MovementValidator().validate(
            graph,
            state,
            [],
        )


def test_rejects_new_connection_capacity_overflow() -> None:
    """Reject too many new users of one connection."""
    start = Zone("start", 0, 0)
    target = Zone("target", 1, 0, max_drones=2)
    end = Zone("end", 2, 0)
    connection = Connection(
        start,
        target,
        max_capacity=1,
    )
    graph = make_graph(
        [start, target, end],
        [connection],
        start,
        end,
    )
    state = make_state(2, start)
    movements = [
        Movement(1, start, target, connection),
        Movement(2, start, target, connection),
    ]

    with pytest.raises(
        MovementValidationError,
        match="Connection between",
    ):
        MovementValidator().validate(
            graph,
            state,
            movements,
        )


def test_counts_existing_transit_in_connection_capacity() -> None:
    """Count drones already occupying a connection."""
    start = Zone("start", 0, 0)
    restricted = Zone(
        "restricted",
        1,
        0,
        zone_type=ZoneType.RESTRICTED,
        max_drones=2,
    )
    end = Zone("end", 2, 0)
    connection = Connection(
        start,
        restricted,
        max_capacity=1,
    )
    graph = make_graph(
        [start, restricted, end],
        [connection],
        start,
        end,
    )
    state = make_state(2, start)
    state.get_drone_state(1).start_transit(
        TransitState(connection, restricted)
    )
    movement = Movement(2, start, restricted, connection)

    with pytest.raises(
        MovementValidationError,
        match="Connection between",
    ):
        MovementValidator().validate(
            graph,
            state,
            [movement],
        )


def test_accepts_movements_on_independent_connections() -> None:
    """Validate simultaneous movements on separate connections."""
    start = Zone("start", 0, 0)
    zone_a = Zone("zone_a", 1, 0)
    zone_b = Zone("zone_b", 1, 1)
    end = Zone("end", 2, 0)
    connection_a = Connection(start, zone_a)
    connection_b = Connection(start, zone_b)
    graph = make_graph(
        [start, zone_a, zone_b, end],
        [connection_a, connection_b],
        start,
        end,
    )
    state = make_state(2, start)
    movements = [
        Movement(1, start, zone_a, connection_a),
        Movement(2, start, zone_b, connection_b),
    ]

    MovementValidator().validate(
        graph,
        state,
        movements,
    )
