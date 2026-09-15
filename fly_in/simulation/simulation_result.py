"""Turn history and aggregate results of a simulation."""

from dataclasses import dataclass

from .simulation_event import SimulationEvent


@dataclass(frozen=True)
class TurnRecord:
    """Events produced during one numbered simulation turn."""

    turn_number: int
    events: tuple[SimulationEvent, ...]


@dataclass(frozen=True)
class SimulationResult:
    """Immutable history returned by a completed simulation."""

    turns: tuple[TurnRecord, ...]
    drone_count: int

    @property
    def turn_count(self) -> int:
        """Return the number of simulation turns."""
        return len(self.turns)

    @property
    def movement_count(self) -> int:
        """Return the number of emitted drone updates."""
        return sum(len(turn.events) for turn in self.turns)

    @property
    def average_updates_per_drone(self) -> float:
        """Return the average number of emitted updates per drone."""
        if self.drone_count == 0:
            return 0.0

        return self.movement_count / self.drone_count
