"""Tests for the Yen-based KShortestPathfinder."""

import pytest

from fly_in.domain.connection import Connection
from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone, ZoneType
from fly_in.errors import PathNotFoundError
from fly_in.pathfinding.k_shortest_pathfinder import (
    KShortestPathfinder,
)
from fly_in.pathfinding.path import Path
from fly_in.pathfinding.path_cost import PathCost


def make_graph(
    zones: list[Zone],
    connections: list[Connection],
    start: Zone,
    end: Zone,
) -> Graph:
    """Create a graph for k-shortest-path tests."""
    return Graph(
        zones=zones,
        connections=connections,
        start_zone=start,
        end_zone=end,
    )


def signature(path: Path) -> tuple[str, ...]:
    """Return the ordered zone-name identity of a path."""
    return tuple(zone.name for zone in path.zones)


def test_rejects_non_positive_k() -> None:
    """Reject zero and negative requested path counts."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    graph = make_graph(
        [start, end],
        [Connection(start, end)],
        start,
        end,
    )
    finder = KShortestPathfinder()

    with pytest.raises(
        ValueError,
        match="requested paths must be positive",
    ):
        finder.find_k_shortest_paths(graph, start, end, 0)

    with pytest.raises(
        ValueError,
        match="requested paths must be positive",
    ):
        finder.find_k_shortest_paths(graph, start, end, -1)


def test_k_one_returns_only_the_shortest_path() -> None:
    """Return only the Dijkstra result when k is one."""
    start = Zone("start", 0, 0)
    middle = Zone("middle", 1, 0)
    end = Zone("end", 2, 0)
    graph = make_graph(
        [start, middle, end],
        [
            Connection(start, middle),
            Connection(middle, end),
        ],
        start,
        end,
    )

    paths = KShortestPathfinder().find_k_shortest_paths(
        graph,
        start,
        end,
        1,
    )

    assert len(paths) == 1
    assert paths[0].zones == (start, middle, end)


def test_returns_two_distinct_routes_in_a_diamond_graph() -> None:
    """Return both simple routes without duplicating either path."""
    start = Zone("start", 0, 0)
    a = Zone("a", 1, 0)
    b = Zone("b", 1, 1)
    end = Zone("end", 2, 0)
    graph = make_graph(
        [start, a, b, end],
        [
            Connection(start, a),
            Connection(a, end),
            Connection(start, b),
            Connection(b, end),
        ],
        start,
        end,
    )

    paths = KShortestPathfinder().find_k_shortest_paths(
        graph,
        start,
        end,
        2,
    )
    signatures = {signature(path) for path in paths}

    assert len(paths) == 2
    assert signatures == {
        ("start", "a", "end"),
        ("start", "b", "end"),
    }


def test_orders_paths_by_total_turn_cost() -> None:
    """Return the faster path before a longer alternative."""
    start = Zone("start", 0, 0)
    fast = Zone("fast", 1, 0)
    slow_a = Zone("slow_a", 1, 1)
    slow_b = Zone("slow_b", 2, 1)
    end = Zone("end", 3, 0)
    graph = make_graph(
        [start, fast, slow_a, slow_b, end],
        [
            Connection(start, fast),
            Connection(fast, end),
            Connection(start, slow_a),
            Connection(slow_a, slow_b),
            Connection(slow_b, end),
        ],
        start,
        end,
    )

    paths = KShortestPathfinder().find_k_shortest_paths(
        graph,
        start,
        end,
        2,
    )

    assert signature(paths[0]) == ("start", "fast", "end")
    assert signature(paths[1]) == (
        "start",
        "slow_a",
        "slow_b",
        "end",
    )
    assert PathCost.from_path(paths[0]) < PathCost.from_path(paths[1])


def test_priority_route_wins_when_turn_costs_tie() -> None:
    """Use priority-zone count as the secondary ordering rule."""
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

    paths = KShortestPathfinder().find_k_shortest_paths(
        graph,
        start,
        end,
        2,
    )

    assert signature(paths[0]) == (
        "start",
        "priority",
        "end",
    )
    assert signature(paths[1]) == (
        "start",
        "normal",
        "end",
    )


def test_finds_candidate_that_shares_a_root_with_an_accepted_path() -> None:
    """Generate an alternative by deviating after a shared root."""
    start = Zone("start", 0, 0)
    a = Zone("a", 1, 0)
    b = Zone("b", 1, 1)
    c = Zone("c", 2, 1)
    end = Zone("end", 3, 0)
    graph = make_graph(
        [start, a, b, c, end],
        [
            Connection(start, a),
            Connection(a, end),
            Connection(start, b),
            Connection(b, end),
            Connection(a, c),
            Connection(c, end),
        ],
        start,
        end,
    )

    paths = KShortestPathfinder().find_k_shortest_paths(
        graph,
        start,
        end,
        3,
    )
    signatures = {signature(path) for path in paths}

    assert len(paths) == 3
    assert signatures == {
        ("start", "a", "end"),
        ("start", "b", "end"),
        ("start", "a", "c", "end"),
    }


def test_returns_fewer_than_k_when_no_more_paths_exist() -> None:
    """Stop cleanly when the graph has no additional simple path."""
    start = Zone("start", 0, 0)
    middle = Zone("middle", 1, 0)
    end = Zone("end", 2, 0)
    graph = make_graph(
        [start, middle, end],
        [
            Connection(start, middle),
            Connection(middle, end),
        ],
        start,
        end,
    )

    paths = KShortestPathfinder().find_k_shortest_paths(
        graph,
        start,
        end,
        5,
    )

    assert len(paths) == 1
    assert signature(paths[0]) == ("start", "middle", "end")


def test_returned_paths_are_unique_and_simple() -> None:
    """Return no duplicate paths and no path containing a cycle."""
    start = Zone("start", 0, 0)
    a = Zone("a", 1, 0)
    b = Zone("b", 1, 1)
    c = Zone("c", 2, 0)
    end = Zone("end", 3, 0)
    graph = make_graph(
        [start, a, b, c, end],
        [
            Connection(start, a),
            Connection(start, b),
            Connection(a, b),
            Connection(a, c),
            Connection(b, c),
            Connection(c, end),
        ],
        start,
        end,
    )

    paths = KShortestPathfinder().find_k_shortest_paths(
        graph,
        start,
        end,
        10,
    )
    signatures = [signature(path) for path in paths]

    assert len(signatures) == len(set(signatures))

    for path_signature in signatures:
        assert len(path_signature) == len(set(path_signature))


def test_raises_when_no_initial_path_exists() -> None:
    """Propagate the error when Dijkstra cannot find the first path."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    graph = make_graph([start, end], [], start, end)

    with pytest.raises(
        PathNotFoundError,
        match="No accessible path",
    ):
        KShortestPathfinder().find_k_shortest_paths(
            graph,
            start,
            end,
            3,
        )
