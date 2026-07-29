# created by layout generator
from .connection import Connection
from .zone import Zone


class Graph:
    """Represents the network of zones and connections."""

    def __init__(
        self,
        zones: list[Zone],
        connections: list[Connection],
        start_zone: Zone,
        end_zone: Zone,
    ) -> None:
        self._zones = {
            zone.name: zone
            for zone in zones
        }

        self._connections = connections
        self._adjacency: dict[str, list[Connection]] = {
            zone.name: []
            for zone in zones
        }

        self.start_zone = start_zone
        self.end_zone = end_zone

        for connection in connections:
            self._adjacency[connection.zone_a.name].append(connection)
            self._adjacency[connection.zone_b.name].append(connection)

    def get_zone(self, name: str) -> Zone:
        """Return a zone by its name."""
        return self._zones[name]

    def get_connections(self, zone: Zone) -> list[Connection]:
        """Return connections attached to a zone."""
        return list(self._adjacency[zone.name])

    def get_neighbors(self, zone: Zone) -> list[Zone]:
        """Return zones directly connected to a zone."""
        return [
            connection.other_zone(zone)
            for connection in self._adjacency[zone.name]
        ]