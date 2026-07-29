from enum import Enum


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    """Represents a zone in the drone network."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType = ZoneType.NORMAL,
        color: str | None = None,
        max_drones: int = 1,
    ) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones

    def movement_cost(self) -> int:
        """Return the number of turns required to enter the zone."""
        if self.zone_type == ZoneType.RESTRICTED:
            return 2

        return 1

    def is_accessible(self) -> bool:
        """Return whether drones are allowed to enter the zone."""
        return self.zone_type != ZoneType.BLOCKED