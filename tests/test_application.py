"""End-to-end tests for application composition."""

from pathlib import Path

from fly_in.application import FlyInApplication
from fly_in.simulation.simulation_result import TurnRecord


def _write_map(tmp_path: Path, drone_count: int = 2) -> Path:
    """Create a minimal valid map file for application tests."""
    map_file = tmp_path / "map.txt"
    map_file.write_text(
        "\n".join(
            [
                f"nb_drones: {drone_count}",
                "start_hub: start 0 0",
                "hub: middle 1 0",
                "end_hub: goal 2 0",
                "connection: start-middle",
                "connection: middle-goal",
            ]
        ),
        encoding="utf-8",
    )
    return map_file


def test_runs_map_file_end_to_end(tmp_path: Path) -> None:
    """Compose parser, pathfinding, planning, scheduling, and simulation."""
    result = FlyInApplication().run(_write_map(tmp_path))

    assert result.turn_count == 3


def test_notifies_observer_after_each_turn(tmp_path: Path) -> None:
    """Forward completed turn records to the supplied observer."""
    observed_turns: list[int] = []

    def observer(turn: TurnRecord) -> None:
        """Record one observed turn number."""
        observed_turns.append(turn.turn_number)

    result = FlyInApplication().run(
        _write_map(tmp_path, drone_count=1),
        observer=observer,
    )

    assert result.turn_count == 2
    assert observed_turns == [1, 2]
