"""Cost representation for Fly-in paths."""

from fly_in.domain.zone import Zone, ZoneType


class PathCost:
    """Represent the weighted cost of a path."""

    def __init__(
        self,
        turns: int = 0,
        priority_zones: int = 0,
    ) -> None:
        """Create a path cost.

        Args:
            turns: Total movement turns required by the path.
            priority_zones: Number of priority zones in the path.

        Raises:
            ValueError: If either value is negative.
        """
        if turns < 0:
            raise ValueError("Turns cannot be negative.")

        if priority_zones < 0:
            raise ValueError(
                "Priority zone count cannot be negative."
            )

        self._turns: int = turns
        self._priority_zones: int = priority_zones

    @property
    def turns(self) -> int:
        """Return the total number of movement turns."""
        return self._turns

    @property
    def priority_zones(self) -> int:
        """Return the number of priority zones used."""
        return self._priority_zones

    def extend(self, zone: Zone) -> "PathCost":
        """Return the cost obtained after entering a zone."""
        turns = self.turns + zone.movement_cost()
        priority_zones = self.priority_zones

        if zone.zone_type == ZoneType.PRIORITY:
            priority_zones += 1

        return PathCost(
            turns=turns,
            priority_zones=priority_zones,
        )

    def __lt__(self, other: object) -> bool:
        """Return whether this cost is preferable to another."""
        if not isinstance(other, PathCost):
            return NotImplemented

        if self.turns != other.turns:
            return self.turns < other.turns

        return self.priority_zones > other.priority_zones
    def __eq__(self, other: object) -> bool:
        """Return whether two path costs are equal."""
        if not isinstance(other, PathCost):
            return NotImplemented

        return self.turns == other.turns and self.priority_zones == other.priority_zones
