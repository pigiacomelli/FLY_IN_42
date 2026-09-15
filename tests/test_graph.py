from fly_in.domain.connection import Connection
from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone


def build_graph() -> tuple[Graph, Zone, Zone, Zone]:
    start = Zone("start", 0, 0)
    middle = Zone("middle", 1, 0)
    end = Zone("end", 2, 0)

    connections = [
        Connection(start, middle),
        Connection(middle, end),
    ]

    graph = Graph(
        zones=[start, middle, end],
        connections=connections,
        start_zone=start,
        end_zone=end,
    )

    return graph, start, middle, end


def test_graph_returns_zone_by_name() -> None:
    graph, start, _, _ = build_graph()

    assert graph.get_zone("start") is start


def test_graph_stores_start_and_end() -> None:
    graph, start, _, end = build_graph()

    assert graph.start_zone is start
    assert graph.end_zone is end


def test_graph_returns_neighbors() -> None:
    graph, start, middle, end = build_graph()

    assert graph.get_neighbors(start) == [middle]
    assert set(graph.get_neighbors(middle)) == {start, end}
    assert graph.get_neighbors(end) == [middle]


def test_connections_are_bidirectional() -> None:
    graph, start, middle, _ = build_graph()

    assert middle in graph.get_neighbors(start)
    assert start in graph.get_neighbors(middle)


def test_get_connections_returns_copy() -> None:
    graph, start, _, _ = build_graph()

    connections = graph.get_connections(start)
    connections.clear()

    assert len(graph.get_connections(start)) == 1
