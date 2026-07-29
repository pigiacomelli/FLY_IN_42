from .zone import Zone


class Connection:
    """Represents a bidirectional connection between two zones."""

    def __init__(
        self,
        zone_a: Zone,
        zone_b: Zone,
        max_capacity: int = 1,
    ) -> None:
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_capacity = max_capacity

    def connects(self, zone: Zone) -> bool:
        """Return whether the zone belongs to this connection."""
        return zone is self.zone_a or zone is self.zone_b

    def other_zone(self, zone: Zone) -> Zone:
        """Return the zone located at the opposite endpoint."""
        if zone is self.zone_a:
            return self.zone_b

        if zone is self.zone_b:
            return self.zone_a

        raise ValueError("Zone does not belong to this connection.")