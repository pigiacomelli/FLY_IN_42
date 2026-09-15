"""Graph representation for Fly-in maps."""

from .connection import Connection
from .zone import Zone


class Graph:
    """Represent the network of zones and bidirectional connections."""

    def __init__(
        self,
        zones: list[Zone],
        connections: list[Connection],
        start_zone: Zone,
        end_zone: Zone,
    ) -> None:
        """Create an adjacency-list graph from validated domain objects."""
        self._zones = {zone.name: zone for zone in zones}
        self._connections = tuple(connections)
        self._adjacency: dict[str, list[Connection]] = {
            zone.name: [] for zone in zones
        }
        self.start_zone = start_zone
        self.end_zone = end_zone

        for connection in connections:
            self._adjacency[connection.zone_a.name].append(connection)
            self._adjacency[connection.zone_b.name].append(connection)

    @property
    def zones(self) -> tuple[Zone, ...]:
        """Return every zone in insertion order."""
        return tuple(self._zones.values())

    @property
    def connections(self) -> tuple[Connection, ...]:
        """Return every connection in the graph."""
        return self._connections

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

    def find_connection(
        self,
        zone_a: Zone,
        zone_b: Zone,
    ) -> Connection:
        """Return the connection joining two adjacent zones.

        Raises:
            KeyError: If the zones are not directly connected.
        """
        for connection in self.get_connections(zone_a):
            if connection.connects(zone_b):
                return connection

        raise KeyError(
            f"Zones '{zone_a.name}' and '{zone_b.name}' "
            "are not directly connected."
        )
