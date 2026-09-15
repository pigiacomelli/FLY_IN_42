"""Result produced by the map parser."""

from fly_in.domain.graph import Graph


class ParsedMap:
    """Represent a successfully parsed Fly-in map."""

    def __init__(
        self,
        drone_count: int,
        graph: Graph,
    ) -> None:
        """Store a validated drone count and graph."""
        self._drone_count = drone_count
        self._graph = graph

    @property
    def drone_count(self) -> int:
        """Return the number of drones in the map."""
        return self._drone_count

    @property
    def graph(self) -> Graph:
        """Return the parsed graph."""
        return self._graph
