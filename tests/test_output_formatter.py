"""Tests for mandatory movement output formatting."""

from fly_in.domain.connection import Connection
from fly_in.domain.zone import Zone
from fly_in.output.formatter import OutputFormatter
from fly_in.simulation.simulation_event import EventKind, SimulationEvent
from fly_in.simulation.simulation_result import TurnRecord


def test_formats_zone_and_connection_events() -> None:
    """Use exactly the required D<ID>-<target> token syntax."""
    start = Zone("start", 0, 0)
    target = Zone("target", 1, 0)
    connection = Connection(start, target)
    turn = TurnRecord(
        turn_number=1,
        events=(
            SimulationEvent(
                1,
                EventKind.ZONE,
                "target",
                target,
                connection,
            ),
            SimulationEvent(
                2,
                EventKind.CONNECTION,
                "start-target",
                target,
                connection,
            ),
        ),
    )

    assert OutputFormatter().format_turn(turn) == (
        "D1-target D2-start-target"
    )


def test_simulation_emits_connection_then_restricted_zone() -> None:
    """Represent both turns of a restricted-zone movement."""
    from fly_in.domain.drone import Drone
    from fly_in.domain.graph import Graph
    from fly_in.domain.zone import ZoneType
    from fly_in.simulation.movement import Movement
    from fly_in.simulation.simulation import Simulation
    from fly_in.simulation.simulation_state import SimulationState

    start = Zone("start", 0, 0)
    restricted = Zone(
        "restricted",
        1,
        0,
        zone_type=ZoneType.RESTRICTED,
    )
    end = Zone("end", 2, 0)
    connection = Connection(start, restricted)
    graph = Graph(
        [start, restricted, end],
        [connection],
        start,
        end,
    )
    simulation = Simulation(
        graph,
        SimulationState([Drone(1)], start),
    )
    formatter = OutputFormatter()

    first_events = simulation.apply_turn(
        [Movement(1, start, restricted, connection)]
    )
    second_events = simulation.apply_turn([])

    assert formatter.format_event(first_events[0]) == (
        "D1-start-restricted"
    )
    assert formatter.format_event(second_events[0]) == "D1-restricted"
