"""Regression tests for the bundled reference map targets."""

from pathlib import Path

import pytest

from fly_in.application import FlyInApplication

CASES = [
    ("easy/01_linear_path.txt", 6),
    ("easy/02_simple_fork.txt", 8),
    ("easy/03_basic_capacity.txt", 6),
    ("medium/01_dead_end_trap.txt", 12),
    ("medium/02_circular_loop.txt", 15),
    ("medium/03_priority_puzzle.txt", 12),
    ("hard/01_maze_nightmare.txt", 30),
    ("hard/02_capacity_hell.txt", 35),
    ("hard/03_ultimate_challenge.txt", 45),
    ("challenger/01_the_impossible_dream.txt", 45),
]


@pytest.mark.parametrize(("relative_path", "target"), CASES)
def test_reference_map_target(
    relative_path: str,
    target: int,
) -> None:
    """Meet or beat each reference map target."""
    maps_root = Path(__file__).resolve().parents[1] / "maps"

    result = FlyInApplication().run(maps_root / relative_path)

    assert result.turn_count <= target
