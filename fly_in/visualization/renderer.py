"""Renderer abstraction for simulation turn visualization."""

from abc import ABC, abstractmethod

from fly_in.simulation.simulation_result import TurnRecord


class Renderer(ABC):
    """Receive and display completed simulation turns."""

    @abstractmethod
    def render_turn(self, turn: TurnRecord) -> None:
        """Render one simulation turn."""
