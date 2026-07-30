from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone
from fly_in.parsing.parsed_map import ParsedMap


def test_parsed_map_stores_result() -> None:
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)

    graph = Graph(
        zones=[start, end],
        connections=[],
        start_zone=start,
        end_zone=end,
    )

    parsed_map = ParsedMap(
        drone_count=5,
        graph=graph,
    )

    assert parsed_map.drone_count == 5
    assert parsed_map.graph is graph