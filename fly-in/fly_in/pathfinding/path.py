"""Path representation for Fly-in pathfinding."""

from fly_in.domain.zone import Zone


class Path:
    """Represent an immutable ordered sequence of zones."""

    def __init__(self, zones: list[Zone]) -> None:
        """Create a path from an ordered list of zones.

        Args:
            zones: Zones ordered from origin to destination.

        Raises:
            ValueError: If the path contains no zones.
        """
        if not zones:
            raise ValueError("Path must contain at least one zone.")

        self._zones: tuple[Zone, ...] = tuple(zones)

    @property
    def zones(self) -> tuple[Zone, ...]:
        """Return the ordered zones in the path."""
        return self._zones

    @property
    def start(self) -> Zone:
        """Return the first zone in the path."""
        return self._zones[0]

    @property
    def end(self) -> Zone:
        """Return the final zone in the path."""
        return self._zones[-1]

    @property
    def hop_count(self) -> int:
        """Return the number of connections traversed."""
        return len(self._zones) - 1