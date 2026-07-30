"""Semantic validation for parsed Fly-in maps."""

from collections import deque

from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone
from fly_in.errors import MapValidationError
from fly_in.parsing.parsed_map import ParsedMap


class MapValidator:
    """Validate global semantic invariants of a parsed map."""

    def validate(self, parsed_map: ParsedMap) -> None:
        """Validate whether a parsed map can be used by the application.

        Args:
            parsed_map: Parsed map containing the drone count and graph.

        Raises:
            MapValidationError: If the map violates a semantic invariant.
        """
        self._validate_drone_count(parsed_map.drone_count)
        self._validate_reachability(parsed_map.graph)

    def _validate_drone_count(self, drone_count: int) -> None:
        """Validate that the map contains at least one drone."""
        if drone_count <= 0:
            raise MapValidationError(
                "Drone count must be a positive integer."
            )

    def _validate_reachability(self, graph: Graph) -> None:
        """Validate that the end zone is reachable from the start zone."""
        queue: deque[Zone] = deque([graph.start_zone])
        visited: set[str] = {graph.start_zone.name}

        while queue:
            current = queue.popleft()

            if current is graph.end_zone:
                return

            for neighbor in graph.get_neighbors(current):
                if not neighbor.is_accessible():
                    continue

                if neighbor.name in visited:
                    continue

                visited.add(neighbor.name)
                queue.append(neighbor)

        raise MapValidationError(
            "End zone is unreachable from start zone."
        )