"""Observable events produced during a simulation turn."""

from dataclasses import dataclass
from enum import Enum

from fly_in.domain.connection import Connection
from fly_in.domain.zone import Zone


class EventKind(Enum):
    """Kinds of movement output supported by the subject format."""

    ZONE = "zone"
    CONNECTION = "connection"


@dataclass(frozen=True)
class SimulationEvent:
    """Represent one drone position update printed for a turn."""

    drone_id: int
    kind: EventKind
    target: str
    destination: Zone
    connection: Connection | None = None
