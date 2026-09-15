"""Tests for congestion-aware route assignment."""

from fly_in.domain.connection import Connection
from fly_in.domain.drone import Drone
from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone
from fly_in.pathfinding.path import Path
from fly_in.scheduling.route_planner import RoutePlanner


def test_assigns_all_drones_when_only_one_path_exists() -> None:
    """Use the only valid route for every drone."""
    start = Zone("start", 0, 0)
    middle = Zone("middle", 1, 0)
    end = Zone("end", 2, 0)
    connections = [Connection(start, middle), Connection(middle, end)]
    graph = Graph([start, middle, end], connections, start, end)
    path = Path([start, middle, end])
    drones = [Drone(1), Drone(2)]

    routes = RoutePlanner().plan(graph, drones, [path])

    assert routes[1].path is path
    assert routes[2].path is path


def test_distributes_drones_across_parallel_bottlenecks() -> None:
    """Use secondary pressure to avoid overloading one equal path."""
    start = Zone("start", 0, 0)
    left = Zone("left", 1, -1)
    right = Zone("right", 1, 1)
    end = Zone("end", 2, 0)
    connections = [
        Connection(start, left),
        Connection(left, end),
        Connection(start, right),
        Connection(right, end),
    ]
    graph = Graph(
        [start, left, right, end],
        connections,
        start,
        end,
    )
    left_path = Path([start, left, end])
    right_path = Path([start, right, end])
    drones = [Drone(1), Drone(2)]

    routes = RoutePlanner().plan(
        graph,
        drones,
        [left_path, right_path],
    )

    assert {routes[1].path, routes[2].path} == {
        left_path,
        right_path,
    }
