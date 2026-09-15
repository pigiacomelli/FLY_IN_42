"""Colored terminal rendering for Fly-in simulation turns."""

from collections.abc import Callable

from fly_in.output.formatter import OutputFormatter
from fly_in.simulation.simulation_event import SimulationEvent
from fly_in.simulation.simulation_result import TurnRecord

from .renderer import Renderer

Writer = Callable[[str], None]


class TerminalRenderer(Renderer):
    """Print mandatory movement lines with optional ANSI colors."""

    _ANSI_COLORS = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "purple": "35",
        "cyan": "36",
        "white": "37",
        "gray": "90",
        "grey": "90",
        "orange": "38;5;208",
        "brown": "38;5;94",
        "gold": "38;5;220",
        "lime": "38;5;118",
        "maroon": "38;5;88",
        "violet": "38;5;177",
        "crimson": "38;5;161",
        "darkred": "38;5;88",
    }

    _FALLBACK_COLORS = (
        "31",
        "32",
        "33",
        "34",
        "35",
        "36",
        "91",
        "92",
        "93",
        "94",
        "95",
        "96",
    )

    def __init__(
        self,
        use_color: bool = True,
        writer: Writer = print,
        formatter: OutputFormatter | None = None,
    ) -> None:
        """Create a terminal renderer."""
        self._use_color = use_color
        self._writer = writer
        self._formatter = formatter or OutputFormatter()

    def render_turn(self, turn: TurnRecord) -> None:
        """Print all drone updates for one turn."""
        if not self._use_color:
            self._writer(self._formatter.format_turn(turn))
            return

        tokens = [self._format_colored(event) for event in turn.events]
        self._writer(" ".join(tokens))

    def _format_colored(self, event: SimulationEvent) -> str:
        """Apply a destination zone color when it is supported."""
        token = self._formatter.format_event(event)
        color = event.destination.color

        if color is None:
            return token

        normalized = color.lower()
        ansi_code = self._ANSI_COLORS.get(normalized)
        if ansi_code is None:
            checksum = sum(
                (index + 1) * ord(character)
                for index, character in enumerate(normalized)
            )
            ansi_code = self._FALLBACK_COLORS[
                checksum % len(self._FALLBACK_COLORS)
            ]

        return f"\033[{ansi_code}m{token}\033[0m"
