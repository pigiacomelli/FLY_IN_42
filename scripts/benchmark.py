"""Run Fly-in against every bundled reference map."""

from pathlib import Path

from fly_in.application import FlyInApplication

TARGETS = {
    "easy/01_linear_path.txt": 6,
    "easy/02_simple_fork.txt": 8,
    "easy/03_basic_capacity.txt": 6,
    "medium/01_dead_end_trap.txt": 12,
    "medium/02_circular_loop.txt": 15,
    "medium/03_priority_puzzle.txt": 12,
    "hard/01_maze_nightmare.txt": 30,
    "hard/02_capacity_hell.txt": 35,
    "hard/03_ultimate_challenge.txt": 45,
    "challenger/01_the_impossible_dream.txt": 45,
}


def main() -> None:
    """Execute all maps and print actual turns against targets."""
    root = Path(__file__).resolve().parents[1] / "maps"
    application = FlyInApplication()

    for relative_path, target in TARGETS.items():
        result = application.run(root / relative_path)
        status = "PASS" if result.turn_count <= target else "MISS"
        print(
            f"{status:4} {relative_path:45} "
            f"turns={result.turn_count:3} target<={target}"
        )


if __name__ == "__main__":
    main()
