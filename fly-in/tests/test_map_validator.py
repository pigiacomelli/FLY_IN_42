"""Tests for the MapValidator."""

import pytest

from fly_in.domain.connection import Connection
from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone, ZoneType
from fly_in.errors import MapValidationError
from fly_in.parsing.parsed_map import ParsedMap
from fly_in.validator import MapValidator


def make_graph(
    zones: list[Zone],
    connections: list[Connection],
    start: Zone,
    end: Zone,
) -> Graph:
    """Create a graph for validator tests."""
    return Graph(
        zones=zones,
        connections=connections,
        start_zone=start,
        end_zone=end,
    )


def test_accepts_directly_connected_map() -> None:
    """Accept a map whose end is directly reachable."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)

    graph = make_graph(
        zones=[start, end],
        connections=[Connection(start, end)],
        start=start,
        end=end,
    )

    MapValidator().validate(
        ParsedMap(drone_count=1, graph=graph)
    )


def test_accepts_map_with_accessible_intermediate_zone() -> None:
    """Accept a map with an accessible path to the end."""
    start = Zone("start", 0, 0)
    middle = Zone(
        "middle",
        1,
        0,
        ZoneType.RESTRICTED,
    )
    end = Zone("end", 2, 0)

    graph = make_graph(
        zones=[start, middle, end],
        connections=[
            Connection(start, middle),
            Connection(middle, end),
        ],
        start=start,
        end=end,
    )

    MapValidator().validate(
        ParsedMap(drone_count=2, graph=graph)
    )


def test_rejects_zero_drones() -> None:
    """Reject a parsed map with no drones."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)

    graph = make_graph(
        zones=[start, end],
        connections=[Connection(start, end)],
        start=start,
        end=end,
    )

    with pytest.raises(
        MapValidationError,
        match="Drone count must be a positive integer",
    ):
        MapValidator().validate(
            ParsedMap(drone_count=0, graph=graph)
        )


def test_rejects_disconnected_end_zone() -> None:
    """Reject a map whose end zone is disconnected."""
    start = Zone("start", 0, 0)
    isolated = Zone("isolated", 1, 0)
    end = Zone("end", 2, 0)

    graph = make_graph(
        zones=[start, isolated, end],
        connections=[
            Connection(start, isolated),
        ],
        start=start,
        end=end,
    )

    with pytest.raises(
        MapValidationError,
        match="End zone is unreachable from start zone",
    ):
        MapValidator().validate(
            ParsedMap(drone_count=1, graph=graph)
        )


def test_rejects_path_through_blocked_zone() -> None:
    """Reject a map whose only path crosses a blocked zone."""
    start = Zone("start", 0, 0)
    blocked = Zone(
        "blocked",
        1,
        0,
        ZoneType.BLOCKED,
    )
    end = Zone("end", 2, 0)

    graph = make_graph(
        zones=[start, blocked, end],
        connections=[
            Connection(start, blocked),
            Connection(blocked, end),
        ],
        start=start,
        end=end,
    )

    with pytest.raises(
        MapValidationError,
        match="End zone is unreachable from start zone",
    ):
        MapValidator().validate(
            ParsedMap(drone_count=1, graph=graph)
        )


def test_accepts_alternative_route_around_blocked_zone() -> None:
    """Accept a map with an accessible alternative route."""
    start = Zone("start", 0, 0)

    blocked = Zone(
        "blocked",
        1,
        0,
        ZoneType.BLOCKED,
    )

    priority = Zone(
        "priority",
        1,
        1,
        ZoneType.PRIORITY,
    )

    end = Zone("end", 2, 0)

    graph = make_graph(
        zones=[start, blocked, priority, end],
        connections=[
            Connection(start, blocked),
            Connection(blocked, end),
            Connection(start, priority),
            Connection(priority, end),
        ],
        start=start,
        end=end,
    )

    MapValidator().validate(
        ParsedMap(drone_count=3, graph=graph)
    )