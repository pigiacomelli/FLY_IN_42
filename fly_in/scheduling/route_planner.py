"""Assignment of drones to candidate paths."""

from collections.abc import Sequence

from fly_in.domain.connection import Connection
from fly_in.domain.drone import Drone
from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone
from fly_in.errors import RoutePlanningError
from fly_in.pathfinding.path import Path
from fly_in.pathfinding.path_cost import PathCost

from .drone_route import DroneRoute

Resource = Connection | Zone


class RoutePlanner:
    """Assign drones using projected congestion-aware completion times."""

    def plan(
        self,
        graph: Graph,
        drones: Sequence[Drone],
        paths: Sequence[Path],
    ) -> dict[int, DroneRoute]:
        """Assign one valid path to each drone.

        Candidate paths are scored by their weighted path cost plus the
        largest projected queue delay on any zone or connection they use.
        This accounts for shared prefixes and bottlenecks without running a
        complete simulation for every possible assignment.
        """
        valid_paths = self._validate_paths(graph, paths)
        self._validate_drones(drones)

        resource_loads: dict[Resource, int] = {}
        routes: dict[int, DroneRoute] = {}

        for drone in sorted(drones, key=lambda item: item.drone_id):
            selected = min(
                valid_paths,
                key=lambda path: self._path_score(
                    graph,
                    path,
                    resource_loads,
                ),
            )
            routes[drone.drone_id] = DroneRoute(
                drone.drone_id,
                selected,
            )
            self._reserve_path_resources(
                graph,
                selected,
                resource_loads,
            )

        return routes

    def _validate_paths(
        self,
        graph: Graph,
        paths: Sequence[Path],
    ) -> tuple[Path, ...]:
        """Return valid start-to-end paths or raise a clear error."""
        if not paths:
            raise RoutePlanningError(
                "At least one candidate path is required."
            )

        valid_paths: list[Path] = []
        signatures: set[tuple[str, ...]] = set()

        for path in paths:
            if path.start is not graph.start_zone:
                raise RoutePlanningError(
                    "Every route must start at the graph start zone."
                )

            if path.end is not graph.end_zone:
                raise RoutePlanningError(
                    "Every route must end at the graph end zone."
                )

            signature = tuple(zone.name for zone in path.zones)
            if len(signature) != len(set(signature)):
                raise RoutePlanningError(
                    "Candidate routes must be simple paths."
                )

            if signature in signatures:
                continue

            for origin, destination in zip(
                path.zones,
                path.zones[1:],
            ):
                try:
                    graph.find_connection(origin, destination)
                except KeyError as error:
                    raise RoutePlanningError(
                        "A candidate route contains non-adjacent zones."
                    ) from error

                if not destination.is_accessible():
                    raise RoutePlanningError(
                        "A candidate route contains a blocked zone."
                    )

            signatures.add(signature)
            valid_paths.append(path)

        if not valid_paths:
            raise RoutePlanningError("No usable candidate paths remain.")

        return tuple(valid_paths)

    def _validate_drones(self, drones: Sequence[Drone]) -> None:
        """Ensure identifiers are positive and unique."""
        identifiers: set[int] = set()

        for drone in drones:
            if drone.drone_id <= 0:
                raise RoutePlanningError(
                    "Drone identifiers must be positive."
                )

            if drone.drone_id in identifiers:
                raise RoutePlanningError(
                    f"Duplicate drone identifier: {drone.drone_id}."
                )

            identifiers.add(drone.drone_id)

    def _path_score(
        self,
        graph: Graph,
        path: Path,
        resource_loads: dict[Resource, int],
    ) -> tuple[int, int, int, int, tuple[str, ...]]:
        """Return a deterministic projected completion score."""
        cost = PathCost.from_path(path)
        queue_delay = 0
        total_pressure = 0

        for resource, capacity in self._path_resources(graph, path):
            load = resource_loads.get(resource, 0)
            resource_delay = load // capacity
            queue_delay = max(queue_delay, resource_delay)
            total_pressure += resource_delay

        return (
            cost.turns + queue_delay,
            total_pressure,
            -cost.priority_zones,
            path.hop_count,
            tuple(zone.name for zone in path.zones),
        )

    def _reserve_path_resources(
        self,
        graph: Graph,
        path: Path,
        resource_loads: dict[Resource, int],
    ) -> None:
        """Increase projected load for resources used by a path."""
        for resource, _ in self._path_resources(graph, path):
            resource_loads[resource] = (
                resource_loads.get(resource, 0) + 1
            )

    def _path_resources(
        self,
        graph: Graph,
        path: Path,
    ) -> tuple[tuple[Resource, int], ...]:
        """Return capacity-limited resources traversed by a path."""
        resources: list[tuple[Resource, int]] = []

        for origin, destination in zip(
            path.zones,
            path.zones[1:],
        ):
            connection = graph.find_connection(origin, destination)
            resources.append((connection, connection.max_capacity))

            if destination is graph.end_zone:
                continue

            resources.append((destination, destination.max_drones))

        return tuple(resources)
