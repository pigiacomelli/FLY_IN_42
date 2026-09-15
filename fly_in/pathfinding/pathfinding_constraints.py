"""Temporary restrictions used during pathfinding searches."""


class PathfindingConstraints:
    """Represent zones and connections excluded from a search."""

    def __init__(
        self,
        forbidden_zones: frozenset[str] | None = None,
        forbidden_connections: (
            frozenset[tuple[str, str]] | None
        ) = None,
    ) -> None:
        """Create temporary pathfinding constraints.

        Args:
            forbidden_zones: Zone names excluded from the search.
            forbidden_connections: Bidirectional connections excluded
                from the search.
        """
        if forbidden_zones is None:
            self._forbidden_zones: frozenset[str] = frozenset()
        else:
            self._forbidden_zones = forbidden_zones

        if forbidden_connections is None:
            self._forbidden_connections: frozenset[
                tuple[str, str]
            ] = frozenset()
        else:
            self._forbidden_connections = frozenset(
                self._connection_key(zone_a, zone_b)
                for zone_a, zone_b in forbidden_connections
            )

    def is_zone_forbidden(self, zone_name: str) -> bool:
        """Return whether a zone is excluded from the search."""
        return zone_name in self._forbidden_zones

    def is_connection_forbidden(
        self,
        zone_a: str,
        zone_b: str,
    ) -> bool:
        """Return whether a bidirectional connection is excluded."""
        key = self._connection_key(zone_a, zone_b)

        return key in self._forbidden_connections

    @staticmethod
    def _connection_key(
        zone_a: str,
        zone_b: str,
    ) -> tuple[str, str]:
        """Return a canonical key for a bidirectional connection."""
        if zone_a <= zone_b:
            return zone_a, zone_b

        return zone_b, zone_a
