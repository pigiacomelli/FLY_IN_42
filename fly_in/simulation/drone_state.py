"""Dynamic state of a drone during the simulation."""

from fly_in.domain.drone import Drone
from fly_in.domain.zone import Zone

from .drone_status import DroneStatus
from .transit_state import TransitState


class DroneState:
    """Represent the current state of one drone."""

    def __init__(
        self,
        drone: Drone,
        current_zone: Zone,
    ) -> None:
        """Create a drone initially located at a zone."""
        self._drone = drone
        self._status = DroneStatus.AT_ZONE
        self._current_zone: Zone | None = current_zone
        self._transit: TransitState | None = None

    @property
    def drone(self) -> Drone:
        """Return the represented drone."""
        return self._drone

    @property
    def status(self) -> DroneStatus:
        """Return the current drone status."""
        return self._status

    @property
    def current_zone(self) -> Zone | None:
        """Return the zone currently occupied by the drone."""
        return self._current_zone

    @property
    def transit(self) -> TransitState | None:
        """Return the active transit."""
        return self._transit

    @property
    def is_at_zone(self) -> bool:
        """Return whether the drone is at a zone."""
        return self._status is DroneStatus.AT_ZONE

    @property
    def is_in_transit(self) -> bool:
        """Return whether the drone is in transit."""
        return self._status is DroneStatus.IN_TRANSIT

    @property
    def is_delivered(self) -> bool:
        """Return whether the drone reached the end zone."""
        return self._status is DroneStatus.DELIVERED

    def move_to(self, destination: Zone) -> None:
        """Move directly to a one-turn destination."""
        self._require_status(DroneStatus.AT_ZONE)

        if destination.movement_cost() > 1:
            raise ValueError(
                "A multi-turn movement must use TransitState."
            )

        self._current_zone = destination

    def start_transit(
        self,
        transit: TransitState,
    ) -> None:
        """Start a multi-turn movement."""
        self._require_status(DroneStatus.AT_ZONE)

        if self._current_zone is not transit.origin:
            raise ValueError(
                "Transit must start at the current drone zone."
            )

        self._status = DroneStatus.IN_TRANSIT
        self._current_zone = None
        self._transit = transit

    def advance_transit(self) -> None:
        """Advance the current transit by one turn."""
        self._require_status(DroneStatus.IN_TRANSIT)

        if self._transit is None:
            raise RuntimeError("Drone transit data is missing.")

        if self._transit.advance():
            destination = self._transit.destination

            self._status = DroneStatus.AT_ZONE
            self._current_zone = destination
            self._transit = None

    def mark_delivered(self, end_zone: Zone) -> None:
        """Mark the drone as delivered at the end zone."""
        self._require_status(DroneStatus.AT_ZONE)

        if self._current_zone is not end_zone:
            raise ValueError(
                "The drone must be at the end zone."
            )

        self._status = DroneStatus.DELIVERED

    def _require_status(
        self,
        expected: DroneStatus,
    ) -> None:
        """Require a specific status for a transition."""
        if self._status is not expected:
            raise RuntimeError(
                "Invalid drone state transition: "
                f"expected {expected.value}, "
                f"found {self._status.value}."
            )
