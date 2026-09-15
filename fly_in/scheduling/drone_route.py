"""Immutable route assigned to one drone."""

from fly_in.domain.zone import Zone
from fly_in.pathfinding.path import Path
from fly_in.pathfinding.path_cost import PathCost


class DroneRoute:
    """Associate one drone identifier with a simple path."""

    def __init__(self, drone_id: int, path: Path) -> None:
        """Create a route for a drone.

        Raises:
            ValueError: If the identifier is invalid or the path
                repeats a zone.
        """
        if drone_id <= 0:
            raise ValueError("Drone identifier must be positive.")

        zone_names = [zone.name for zone in path.zones]
        if len(zone_names) != len(set(zone_names)):
            raise ValueError(
                "Drone routes must be simple paths."
            )

        self._drone_id = drone_id
        self._path = path
        self._indices = {
            zone.name: index
            for index, zone in enumerate(path.zones)
        }

    @property
    def drone_id(self) -> int:
        """Return the associated drone identifier."""
        return self._drone_id

    @property
    def path(self) -> Path:
        """Return the assigned immutable path."""
        return self._path

    @property
    def total_cost(self) -> PathCost:
        """Return the weighted cost of the full route."""
        return PathCost.from_path(self._path)

    def index_of(self, zone: Zone) -> int:
        """Return a zone position in the route.

        Raises:
            ValueError: If the zone is not part of the route.
        """
        try:
            return self._indices[zone.name]
        except KeyError as error:
            raise ValueError(
                f"Zone '{zone.name}' is not part of drone "
                f"{self.drone_id}'s route."
            ) from error

    def next_zone(self, current_zone: Zone) -> Zone | None:
        """Return the next route zone after the current one."""
        current_index = self.index_of(current_zone)
        next_index = current_index + 1

        if next_index >= len(self._path.zones):
            return None

        return self._path.zones[next_index]

    def remaining_cost(self, current_zone: Zone) -> int:
        """Return movement turns remaining from a route zone."""
        current_index = self.index_of(current_zone)
        return sum(
            zone.movement_cost()
            for zone in self._path.zones[current_index + 1:]
        )
