"""Drone domain model."""


class Drone:
    """Represent a drone in the simulation."""

    def __init__(self, drone_id: int) -> None:
        """Create a drone with a unique positive identifier."""
        self.drone_id = drone_id
