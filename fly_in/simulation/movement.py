"""Movement decisions for Fly-in simulations."""

from dataclasses import dataclass

from fly_in.domain.connection import Connection
from fly_in.domain.zone import Zone


@dataclass(frozen=True)
class Movement:
    """Represent one drone movement between adjacent zones."""

    drone_id: int
    origin: Zone
    destination: Zone
    connection: Connection

    def __post_init__(self) -> None:
        """Validate the basic structure of the movement."""
        if self.drone_id <= 0:
            raise ValueError(
                "The drone identifier must be positive."
            )

        if self.origin is self.destination:
            raise ValueError(
                "Movement origin and destination must differ."
            )

        if not self.connection.connects(self.origin):
            raise ValueError(
                "The connection must contain the origin zone."
            )

        if not self.connection.connects(self.destination):
            raise ValueError(
                "The connection must contain the destination zone."
            )

    @property
    def movement_cost(self) -> int:
        """Return the number of turns required by the movement."""
        return self.destination.movement_cost()

    @property
    def requires_transit(self) -> bool:
        """Return whether the movement requires a transit state."""
        return self.movement_cost > 1
