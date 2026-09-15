"""High-level loop coordinating a scheduler and simulation engine."""

from collections.abc import Callable

from fly_in.errors import (
    MovementValidationError,
    SimulationDeadlockError,
    SimulationLimitError,
)
from fly_in.scheduling.scheduler import Scheduler

from .simulation import Simulation
from .simulation_result import SimulationResult, TurnRecord

TurnObserver = Callable[[TurnRecord], None]


class SimulationRunner:
    """Run scheduled turns until all drones are delivered."""

    def __init__(
        self,
        simulation: Simulation,
        scheduler: Scheduler,
        max_turns: int = 100_000,
    ) -> None:
        """Create a runner with a defensive turn limit."""
        if max_turns <= 0:
            raise ValueError("Maximum turn count must be positive.")

        self._simulation = simulation
        self._scheduler = scheduler
        self._max_turns = max_turns

    def run(
        self,
        observer: TurnObserver | None = None,
    ) -> SimulationResult:
        """Execute turns until completion and return the full history."""
        records: list[TurnRecord] = []

        while not self._simulation.is_complete:
            if len(records) >= self._max_turns:
                raise SimulationLimitError(
                    "Simulation exceeded the maximum of "
                    f"{self._max_turns} turns."
                )

            movements = self._scheduler.plan_turn(
                self._simulation.state
            )

            if (
                not movements
                and not self._simulation.state.states_in_transit()
            ):
                raise SimulationDeadlockError(
                    "No unfinished drone can make progress."
                )

            try:
                events = self._simulation.apply_turn(movements)
            except MovementValidationError as error:
                raise SimulationDeadlockError(
                    "The scheduler could not produce a valid turn: "
                    f"{error}"
                ) from error

            record = TurnRecord(
                turn_number=self._simulation.state.turn_number,
                events=events,
            )
            records.append(record)

            if observer is not None:
                observer(record)

        return SimulationResult(
            turns=tuple(records),
            drone_count=self._simulation.state.drone_count,
        )
