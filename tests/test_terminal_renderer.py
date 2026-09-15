"""Tests for the mandatory colored terminal visualization."""

from fly_in.domain.connection import Connection
from fly_in.domain.zone import Zone
from fly_in.simulation.simulation_event import EventKind, SimulationEvent
from fly_in.simulation.simulation_result import TurnRecord
from fly_in.visualization.terminal_renderer import TerminalRenderer


def _turn(color: str | None) -> TurnRecord:
    """Create a one-event turn targeting a colored zone."""
    start = Zone("start", 0, 0)
    target = Zone("target", 1, 0, color=color)
    connection = Connection(start, target)
    event = SimulationEvent(
        drone_id=1,
        kind=EventKind.ZONE,
        target="target",
        destination=target,
        connection=connection,
    )
    return TurnRecord(turn_number=1, events=(event,))


def test_renders_plain_mandatory_output_when_color_disabled() -> None:
    """Preserve exact mandatory output when ANSI colors are disabled."""
    output: list[str] = []
    renderer = TerminalRenderer(use_color=False, writer=output.append)

    renderer.render_turn(_turn("red"))

    assert output == ["D1-target"]


def test_applies_supported_zone_color() -> None:
    """Use ANSI feedback for a supported zone color."""
    output: list[str] = []
    renderer = TerminalRenderer(use_color=True, writer=output.append)

    renderer.render_turn(_turn("red"))

    assert output == ["\033[31mD1-target\033[0m"]


def test_unknown_color_receives_deterministic_visual_feedback() -> None:
    """Map arbitrary single-word colors to a stable ANSI fallback."""
    first_output: list[str] = []
    second_output: list[str] = []

    TerminalRenderer(
        use_color=True,
        writer=first_output.append,
    ).render_turn(_turn("ultraviolet"))
    TerminalRenderer(
        use_color=True,
        writer=second_output.append,
    ).render_turn(_turn("ultraviolet"))

    assert first_output == second_output
    assert first_output[0].startswith("\033[")
    assert first_output[0].endswith("D1-target\033[0m")
