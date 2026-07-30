"""Shortest-path algorithms for Fly-in graphs."""

import heapq

from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone
from fly_in.errors import PathNotFoundError

from .path import Path
from .path_cost import PathCost


class Pathfinder:
    """Find minimum-cost paths between graph zones."""

    def find_shortest_path(
        self,
        graph: Graph,
        start: Zone,
        end: Zone,
    ) -> Path:
        """Find the preferable minimum-turn path.

        Args:
            graph: Graph containing the available zones.
            start: Origin zone.
            end: Destination zone.

        Returns:
            The preferable minimum-cost path.

        Raises:
            PathNotFoundError: If no accessible path exists.
        """
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
                if not neighbor.is_accessible():
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

    def _reconstruct_path(
        self,
        previous: dict[str, Zone | None],
        end: Zone,
    ) -> Path:
        """Reconstruct a path from predecessor information."""
        zones: list[Zone] = []
        current: Zone | None = end

        while current is not None:
            zones.append(current)
            current = previous[current.name]

        zones.reverse()

        return Path(zones)