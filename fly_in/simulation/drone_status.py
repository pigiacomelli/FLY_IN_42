"""Possible dynamic statuses of a drone."""

from enum import Enum


class DroneStatus(Enum):
    """Possible states of a drone."""

    AT_ZONE = "at_zone"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
