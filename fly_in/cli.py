"""Command-line interface for the Fly-in application."""

import argparse
import sys
from collections.abc import Sequence

from fly_in.application import FlyInApplication
from fly_in.errors import FlyInError
from fly_in.visualization.terminal_renderer import TerminalRenderer


def build_argument_parser() -> argparse.ArgumentParser:
    """Return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="fly-in",
        description=(
            "Route all drones from the start hub to the end hub while "
            "respecting zone and connection capacities."
        ),
    )
    parser.add_argument("map_file", help="path to a Fly-in map file")
    parser.add_argument(
        "--paths",
        type=int,
        default=16,
        help="maximum candidate paths to generate (default: 16)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=100_000,
        help="defensive simulation turn limit",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable ANSI terminal colors",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="print aggregate metrics to stderr",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the command-line program and return an exit status."""
    parser = build_argument_parser()
    namespace = parser.parse_args(arguments)
    application = FlyInApplication()
    renderer = TerminalRenderer(use_color=not namespace.no_color)

    try:
        result = application.run(
            namespace.map_file,
            path_count=namespace.paths,
            max_turns=namespace.max_turns,
            observer=renderer.render_turn,
        )
    except (FlyInError, ValueError, KeyError) as error:
        print(f"fly-in: error: {error}", file=sys.stderr)
        return 1

    if namespace.stats:
        print(
            "turns="
            f"{result.turn_count} "
            "updates="
            f"{result.movement_count} "
            "average_updates_per_drone="
            f"{result.average_updates_per_drone:.2f}",
            file=sys.stderr,
        )

    return 0
