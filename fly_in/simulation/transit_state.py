"""State of a drone moving through a connection."""

from fly_in.domain.connection import Connection
from fly_in.domain.zone import Zone


class TransitState:
    """Represent a drone completing a multi-turn movement."""

    def __init__(
        self,
        connection: Connection,
        destination: Zone,
    ) -> None:
        """Create a transit state."""
        if not connection.connects(destination):
            raise ValueError(
                "The connection must contain the destination zone."
            )

        remaining_turns = destination.movement_cost() - 1

        if remaining_turns <= 0:
            raise ValueError(
                "Transit is only required for multi-turn movements."
            )

        self.connection = connection
        self.destination = destination
        self.remaining_turns = remaining_turns

    @property
    def origin(self) -> Zone:
        """Return the zone from which the drone departed."""
        return self.connection.other_zone(self.destination)

    @property
    def is_complete(self) -> bool:
        """Return whether the transit has finished."""
        return self.remaining_turns == 0

    def advance(self) -> bool:
        """Advance the transit and return whether it is complete."""
        if self.is_complete:
            raise RuntimeError(
                "A completed transit cannot be advanced."
            )

        self.remaining_turns -= 1

        return self.is_complete
