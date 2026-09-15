"""Generation of multiple shortest paths for Fly-in graphs."""

import heapq

from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone
from fly_in.errors import PathNotFoundError

from .path import Path
from .path_cost import PathCost
from .pathfinder import Pathfinder
from .pathfinding_constraints import PathfindingConstraints


class KShortestPathfinder:
    """Find multiple preferable simple paths between two zones."""

    def __init__(
        self,
        pathfinder: Pathfinder | None = None,
    ) -> None:
        """Create a k-shortest-path finder.

        Args:
            pathfinder: Shortest-path implementation used internally.
        """
        if pathfinder is None:
            self._pathfinder: Pathfinder = Pathfinder()
        else:
            self._pathfinder = pathfinder

    def find_k_shortest_paths(
        self,
        graph: Graph,
        start: Zone,
        end: Zone,
        k: int,
    ) -> list[Path]:
        """Find up to k preferable simple paths.

        Paths are ordered primarily by movement turns. When paths
        have the same movement cost, paths containing more priority
        zones are preferred.

        Args:
            graph: Graph containing the available routes.
            start: Origin zone.
            end: Destination zone.
            k: Maximum number of paths to return.

        Returns:
            Paths ordered from most to least preferable.

        Raises:
            ValueError: If k is not positive.
            PathNotFoundError: If no initial path exists.
        """
        if k <= 0:
            raise ValueError(
                "The number of requested paths must be positive."
            )

        first_path = self._pathfinder.find_shortest_path(
            graph,
            start,
            end,
        )

        shortest_paths: list[Path] = [
            first_path,
        ]

        if k == 1:
            return shortest_paths

        candidates: list[
            tuple[PathCost, int, Path]
        ] = []

        candidate_order = 0

        accepted_signatures: set[tuple[str, ...]] = {
            self._path_signature(first_path),
        }

        candidate_signatures: set[tuple[str, ...]] = set()

        for _ in range(1, k):
            previous_path = shortest_paths[-1]

            for spur_index in range(previous_path.hop_count):
                root_zones = previous_path.zones[
                    :spur_index + 1
                ]

                spur_node = root_zones[-1]

                forbidden_zones = frozenset(
                    zone.name
                    for zone in root_zones[:-1]
                )

                forbidden_connections = (
                    self._find_forbidden_connections(
                        shortest_paths,
                        root_zones,
                        spur_index,
                    )
                )

                constraints = PathfindingConstraints(
                    forbidden_zones=forbidden_zones,
                    forbidden_connections=(
                        forbidden_connections
                    ),
                )

                try:
                    spur_path = (
                        self._pathfinder.find_shortest_path(
                            graph,
                            spur_node,
                            end,
                            constraints,
                        )
                    )
                except PathNotFoundError:
                    continue

                candidate_zones = list(
                    root_zones[:-1]
                ) + list(spur_path.zones)

                candidate_path = Path(candidate_zones)
                signature = self._path_signature(
                    candidate_path
                )

                if signature in accepted_signatures:
                    continue

                if signature in candidate_signatures:
                    continue

                candidate_cost = PathCost.from_path(
                    candidate_path
                )

                candidate_order += 1

                heapq.heappush(
                    candidates,
                    (
                        candidate_cost,
                        candidate_order,
                        candidate_path,
                    ),
                )

                candidate_signatures.add(signature)

            if not candidates:
                break

            _, _, next_path = heapq.heappop(candidates)

            next_signature = self._path_signature(next_path)

            candidate_signatures.discard(next_signature)
            accepted_signatures.add(next_signature)
            shortest_paths.append(next_path)

        return shortest_paths

    def _find_forbidden_connections(
        self,
        shortest_paths: list[Path],
        root_zones: tuple[Zone, ...],
        spur_index: int,
    ) -> frozenset[tuple[str, str]]:
        """Find connections that must be excluded for a root path.

        A connection is excluded when an already accepted path has
        the same root and uses that connection immediately after the
        spur node.

        Args:
            shortest_paths: Paths already accepted by the algorithm.
            root_zones: Root prefix currently being preserved.
            spur_index: Index of the current spur node.

        Returns:
            Bidirectional connections temporarily excluded.
        """
        forbidden_connections: set[
            tuple[str, str]
        ] = set()

        root_signature = tuple(
            zone.name
            for zone in root_zones
        )

        for path in shortest_paths:
            path_zones = path.zones

            if len(path_zones) <= spur_index + 1:
                continue

            path_root_signature = tuple(
                zone.name
                for zone in path_zones[
                    :spur_index + 1
                ]
            )

            if path_root_signature != root_signature:
                continue

            zone_a = path_zones[spur_index]
            zone_b = path_zones[spur_index + 1]

            forbidden_connections.add(
                (
                    zone_a.name,
                    zone_b.name,
                )
            )

        return frozenset(forbidden_connections)

    @staticmethod
    def _path_signature(path: Path) -> tuple[str, ...]:
        """Return a unique identity for a path.

        Args:
            path: Path whose identity will be generated.

        Returns:
            Ordered tuple containing the names of the path zones.
        """
        return tuple(
            zone.name
            for zone in path.zones
        )
