"""Formatting of simulation events in the mandatory output syntax."""

from fly_in.simulation.simulation_event import SimulationEvent
from fly_in.simulation.simulation_result import SimulationResult, TurnRecord


class OutputFormatter:
    """Convert simulation events to deterministic text lines."""

    def format_event(self, event: SimulationEvent) -> str:
        """Format one event as ``D<ID>-<target>``."""
        return f"D{event.drone_id}-{event.target}"

    def format_turn(self, turn: TurnRecord) -> str:
        """Format all events occurring during one turn."""
        return " ".join(
            self.format_event(event)
            for event in turn.events
        )

    def format_result(self, result: SimulationResult) -> str:
        """Format the complete simulation as one line per turn."""
        return "\n".join(
            self.format_turn(turn)
            for turn in result.turns
        )
