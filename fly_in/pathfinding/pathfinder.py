"""Shortest-path algorithms for Fly-in graphs."""

import heapq

from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone
from fly_in.errors import PathNotFoundError

from .path import Path
from .path_cost import PathCost
from .pathfinding_constraints import PathfindingConstraints


class Pathfinder:
    """Find minimum-cost paths between graph zones."""

    def find_shortest_path(
        self,
        graph: Graph,
        start: Zone,
        end: Zone,
        constraints: PathfindingConstraints | None = None,
    ) -> Path:
        """Find the preferable minimum-turn path.

        Paths are ordered primarily by their total movement cost.
        When paths have the same movement cost, the path containing
        more priority zones is preferred.

        Args:
            graph: Graph containing the zones and connections.
            start: Zone where the search begins.
            end: Destination zone.
            constraints: Optional temporary pathfinding restrictions.

        Returns:
            The preferable minimum-cost path from start to end.

        Raises:
            PathNotFoundError: If the start or end zone is forbidden,
                or if no accessible path exists between them.
        """
        if constraints is None:
            constraints = PathfindingConstraints()

        self._validate_search_endpoints(
            start,
            end,
            constraints,
        )

        start_cost = PathCost()

        best_costs: dict[str, PathCost] = {
            start.name: start_cost,
        }

        previous: dict[str, Zone | None] = {
            start.name: None,
        }

        queue: list[tuple[PathCost, int, Zone]] = []
        entry_order = 0

        heapq.heappush(
            queue,
            (
                start_cost,
                entry_order,
                start,
            ),
        )

        while queue:
            current_cost, _, current_zone = heapq.heappop(queue)

            if current_cost != best_costs[current_zone.name]:
                continue

            if current_zone.name == end.name:
                return self._reconstruct_path(
                    previous,
                    current_zone,
                )

            for neighbor in graph.get_neighbors(current_zone):
                if not self._can_visit(
                    current_zone,
                    neighbor,
                    constraints,
                ):
                    continue

                candidate_cost = current_cost.extend(neighbor)
                known_cost = best_costs.get(neighbor.name)

                if (
                    known_cost is None
                    or candidate_cost < known_cost
                ):
                    best_costs[neighbor.name] = candidate_cost
                    previous[neighbor.name] = current_zone

                    entry_order += 1

                    heapq.heappush(
                        queue,
                        (
                            candidate_cost,
                            entry_order,
                            neighbor,
                        ),
                    )

        raise PathNotFoundError(
            f"No accessible path from "
            f"'{start.name}' to '{end.name}'."
        )

    def _validate_search_endpoints(
        self,
        start: Zone,
        end: Zone,
        constraints: PathfindingConstraints,
    ) -> None:
        """Validate that the search endpoints are not forbidden.

        Args:
            start: Search origin.
            end: Search destination.
            constraints: Temporary search restrictions.

        Raises:
            PathNotFoundError: If the start or end zone is forbidden.
        """
        if constraints.is_zone_forbidden(start.name):
            raise PathNotFoundError(
                f"Start zone '{start.name}' is forbidden."
            )

        if constraints.is_zone_forbidden(end.name):
            raise PathNotFoundError(
                f"End zone '{end.name}' is forbidden."
            )

    def _can_visit(
        self,
        current_zone: Zone,
        neighbor: Zone,
        constraints: PathfindingConstraints,
    ) -> bool:
        """Return whether a neighboring zone may be visited.

        Args:
            current_zone: Zone currently being explored.
            neighbor: Neighboring zone considered by the algorithm.
            constraints: Temporary search restrictions.

        Returns:
            True if the zone and connection may be used.
        """
        if not neighbor.is_accessible():
            return False

        if constraints.is_zone_forbidden(neighbor.name):
            return False

        if constraints.is_connection_forbidden(
            current_zone.name,
            neighbor.name,
        ):
            return False

        return True

    def _reconstruct_path(
        self,
        previous: dict[str, Zone | None],
        end: Zone,
    ) -> Path:
        """Reconstruct a path from predecessor information.

        Args:
            previous: Best predecessor found for each visited zone.
            end: Final zone from which reconstruction begins.

        Returns:
            Path ordered from the origin to the destination.
        """
        zones: list[Zone] = []
        current: Zone | None = end

        while current is not None:
            zones.append(current)
            current = previous[current.name]

        zones.reverse()

        return Path(zones)
