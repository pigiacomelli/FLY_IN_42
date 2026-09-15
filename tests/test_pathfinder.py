"""Tests for the Pathfinder class."""

import pytest

from fly_in.domain.connection import Connection
from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone, ZoneType
from fly_in.errors import PathNotFoundError
from fly_in.pathfinding.pathfinder import Pathfinder


def make_graph(
    zones: list[Zone],
    connections: list[Connection],
    start: Zone,
    end: Zone,
) -> Graph:
    """Create a graph for pathfinder tests."""
    return Graph(
        zones=zones,
        connections=connections,
        start_zone=start,
        end_zone=end,
    )


def test_finds_direct_path() -> None:
    """Find a direct path between start and end."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    graph = make_graph(
        [start, end],
        [Connection(start, end)],
        start,
        end,
    )

    path = Pathfinder().find_shortest_path(graph, start, end)

    assert path.zones == (start, end)
    assert path.hop_count == 1


def test_prefers_lower_turn_cost_over_fewer_hops() -> None:
    """Choose a longer route when its weighted cost is lower."""
    start = Zone("start", 0, 0)
    restricted_a = Zone(
        "restricted_a",
        1,
        0,
        ZoneType.RESTRICTED,
    )
    restricted_b = Zone(
        "restricted_b",
        2,
        0,
        ZoneType.RESTRICTED,
    )
    normal_a = Zone("normal_a", 0, 1)
    normal_b = Zone("normal_b", 1, 1)
    normal_c = Zone("normal_c", 2, 1)
    end = Zone("end", 3, 0)
    zones = [
        start,
        restricted_a,
        restricted_b,
        normal_a,
        normal_b,
        normal_c,
        end,
    ]
    connections = [
        Connection(start, restricted_a),
        Connection(restricted_a, restricted_b),
        Connection(restricted_b, end),
        Connection(start, normal_a),
        Connection(normal_a, normal_b),
        Connection(normal_b, normal_c),
        Connection(normal_c, end),
    ]
    graph = make_graph(zones, connections, start, end)

    path = Pathfinder().find_shortest_path(graph, start, end)

    assert path.zones == (
        start,
        normal_a,
        normal_b,
        normal_c,
        end,
    )


def test_avoids_blocked_zones() -> None:
    """Ignore paths that require entering blocked zones."""
    start = Zone("start", 0, 0)
    blocked = Zone("blocked", 1, 0, ZoneType.BLOCKED)
    safe = Zone("safe", 1, 1)
    end = Zone("end", 2, 0)
    graph = make_graph(
        [start, blocked, safe, end],
        [
            Connection(start, blocked),
            Connection(blocked, end),
            Connection(start, safe),
            Connection(safe, end),
        ],
        start,
        end,
    )

    path = Pathfinder().find_shortest_path(graph, start, end)

    assert path.zones == (start, safe, end)


def test_prefers_priority_route_when_turns_tie() -> None:
    """Prefer priority zones between paths with equal turns."""
    start = Zone("start", 0, 0)
    normal = Zone("normal", 1, 0)
    priority = Zone("priority", 1, 1, ZoneType.PRIORITY)
    end = Zone("end", 2, 0)
    graph = make_graph(
        [start, normal, priority, end],
        [
            Connection(start, normal),
            Connection(normal, end),
            Connection(start, priority),
            Connection(priority, end),
        ],
        start,
        end,
    )

    path = Pathfinder().find_shortest_path(graph, start, end)

    assert path.zones == (start, priority, end)


def test_returns_single_zone_when_start_is_end() -> None:
    """Return a zero-hop path when origin equals destination."""
    start = Zone("start", 0, 0)
    graph = make_graph([start], [], start, start)

    path = Pathfinder().find_shortest_path(graph, start, start)

    assert path.zones == (start,)
    assert path.hop_count == 0


def test_handles_cycles_without_repeating_zones() -> None:
    """Find the best path in a graph containing a cycle."""
    start = Zone("start", 0, 0)
    a = Zone("a", 1, 0)
    b = Zone("b", 1, 1)
    end = Zone("end", 2, 0)
    graph = make_graph(
        [start, a, b, end],
        [
            Connection(start, a),
            Connection(a, b),
            Connection(b, start),
            Connection(a, end),
        ],
        start,
        end,
    )

    path = Pathfinder().find_shortest_path(graph, start, end)

    assert path.zones == (start, a, end)


def test_raises_when_destination_is_unreachable() -> None:
    """Raise an error when no accessible path exists."""
    start = Zone("start", 0, 0)
    isolated = Zone("isolated", 1, 0)
    end = Zone("end", 2, 0)
    graph = make_graph(
        [start, isolated, end],
        [Connection(start, isolated)],
        start,
        end,
    )

    with pytest.raises(
        PathNotFoundError,
        match="No accessible path from 'start' to 'end'",
    ):
        Pathfinder().find_shortest_path(graph, start, end)
