"""Tests for Pathfinder searches with temporary constraints."""

import pytest

from fly_in.domain.connection import Connection
from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone, ZoneType
from fly_in.errors import PathNotFoundError
from fly_in.pathfinding.pathfinder import Pathfinder
from fly_in.pathfinding.pathfinding_constraints import (
    PathfindingConstraints,
)


def make_graph(
    zones: list[Zone],
    connections: list[Connection],
    start: Zone,
    end: Zone,
) -> Graph:
    """Create a graph for constrained-pathfinder tests."""
    return Graph(
        zones=zones,
        connections=connections,
        start_zone=start,
        end_zone=end,
    )


def make_two_route_graph() -> tuple[Graph, Zone, Zone, Zone, Zone]:
    """Create two routes where the priority route is preferred."""
    start = Zone("start", 0, 0)
    priority = Zone("priority", 1, 0, ZoneType.PRIORITY)
    alternative = Zone("alternative", 1, 1)
    end = Zone("end", 2, 0)

    graph = make_graph(
        [start, priority, alternative, end],
        [
            Connection(start, priority),
            Connection(priority, end),
            Connection(start, alternative),
            Connection(alternative, end),
        ],
        start,
        end,
    )

    return graph, start, priority, alternative, end


def test_uses_normal_shortest_path_without_constraints() -> None:
    """Preserve the original Dijkstra behavior by default."""
    graph, start, priority, _, end = make_two_route_graph()

    path = Pathfinder().find_shortest_path(graph, start, end)

    assert path.zones == (start, priority, end)


def test_uses_alternative_route_when_connection_is_forbidden() -> None:
    """Avoid a temporarily forbidden connection."""
    graph, start, priority, alternative, end = make_two_route_graph()
    constraints = PathfindingConstraints(
        forbidden_connections=frozenset({
            (start.name, priority.name),
        }),
    )

    path = Pathfinder().find_shortest_path(
        graph,
        start,
        end,
        constraints,
    )

    assert path.zones == (start, alternative, end)


def test_uses_alternative_route_when_zone_is_forbidden() -> None:
    """Avoid a temporarily forbidden zone."""
    graph, start, priority, alternative, end = make_two_route_graph()
    constraints = PathfindingConstraints(
        forbidden_zones=frozenset({priority.name}),
    )

    path = Pathfinder().find_shortest_path(
        graph,
        start,
        end,
        constraints,
    )

    assert path.zones == (start, alternative, end)


def test_raises_when_constraints_block_every_route() -> None:
    """Raise when temporary restrictions make the end unreachable."""
    graph, start, priority, alternative, end = make_two_route_graph()
    constraints = PathfindingConstraints(
        forbidden_zones=frozenset({
            priority.name,
            alternative.name,
        }),
    )

    with pytest.raises(
        PathNotFoundError,
        match="No accessible path",
    ):
        Pathfinder().find_shortest_path(
            graph,
            start,
            end,
            constraints,
        )


def test_raises_when_start_zone_is_forbidden() -> None:
    """Reject a search whose origin is temporarily forbidden."""
    graph, start, _, _, end = make_two_route_graph()
    constraints = PathfindingConstraints(
        forbidden_zones=frozenset({start.name}),
    )

    with pytest.raises(
        PathNotFoundError,
        match="Start zone 'start' is forbidden",
    ):
        Pathfinder().find_shortest_path(
            graph,
            start,
            end,
            constraints,
        )


def test_raises_when_end_zone_is_forbidden() -> None:
    """Reject a search whose destination is temporarily forbidden."""
    graph, start, _, _, end = make_two_route_graph()
    constraints = PathfindingConstraints(
        forbidden_zones=frozenset({end.name}),
    )

    with pytest.raises(
        PathNotFoundError,
        match="End zone 'end' is forbidden",
    ):
        Pathfinder().find_shortest_path(
            graph,
            start,
            end,
            constraints,
        )


def test_constraints_do_not_modify_the_graph() -> None:
    """Keep all graph connections available after a constrained search."""
    graph, start, priority, alternative, end = make_two_route_graph()
    constraints = PathfindingConstraints(
        forbidden_connections=frozenset({
            (start.name, priority.name),
        }),
    )
    pathfinder = Pathfinder()

    constrained_path = pathfinder.find_shortest_path(
        graph,
        start,
        end,
        constraints,
    )
    normal_path = pathfinder.find_shortest_path(
        graph,
        start,
        end,
    )

    assert constrained_path.zones == (start, alternative, end)
    assert normal_path.zones == (start, priority, end)
    assert set(graph.get_neighbors(start)) == {
        priority,
        alternative,
    }
