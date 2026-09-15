"""Composition root for parsing, planning, and running Fly-in maps."""

from collections.abc import Callable
from pathlib import Path

from fly_in.domain.drone import Drone
from fly_in.parsing.parser import Parser
from fly_in.pathfinding.k_shortest_pathfinder import KShortestPathfinder
from fly_in.scheduling.route_planner import RoutePlanner
from fly_in.scheduling.scheduler import Scheduler
from fly_in.simulation.runner import SimulationRunner
from fly_in.simulation.simulation import Simulation
from fly_in.simulation.simulation_result import SimulationResult, TurnRecord
from fly_in.simulation.simulation_state import SimulationState
from fly_in.validator.map_validator import MapValidator

TurnObserver = Callable[[TurnRecord], None]


class FlyInApplication:
    """Build and execute a complete simulation from one map file."""

    def __init__(
        self,
        parser: Parser | None = None,
        map_validator: MapValidator | None = None,
        pathfinder: KShortestPathfinder | None = None,
        route_planner: RoutePlanner | None = None,
    ) -> None:
        """Create the application with replaceable components."""
        self._parser = parser or Parser()
        self._map_validator = map_validator or MapValidator()
        self._pathfinder = pathfinder or KShortestPathfinder()
        self._route_planner = route_planner or RoutePlanner()

    def run(
        self,
        map_path: str | Path,
        path_count: int = 16,
        max_turns: int = 100_000,
        observer: TurnObserver | None = None,
    ) -> SimulationResult:
        """Parse a map, construct routes, and run the simulation.

        Args:
            map_path: Input map path.
            path_count: Maximum number of candidate paths.
            max_turns: Defensive simulation turn limit.
            observer: Optional callback receiving completed turns.

        Returns:
            Complete immutable simulation result.

        Raises:
            ValueError: If a numeric argument is invalid.
        """
        if path_count <= 0:
            raise ValueError("Path count must be positive.")

        parsed_map = self._parser.parse(map_path)
        self._map_validator.validate(parsed_map)
        graph = parsed_map.graph

        drones = [
            Drone(drone_id)
            for drone_id in range(1, parsed_map.drone_count + 1)
        ]
        paths = self._pathfinder.find_k_shortest_paths(
            graph,
            graph.start_zone,
            graph.end_zone,
            path_count,
        )
        routes = self._route_planner.plan(graph, drones, paths)
        state = SimulationState(drones, graph.start_zone)
        simulation = Simulation(graph, state)
        scheduler = Scheduler(graph, routes)
        runner = SimulationRunner(
            simulation,
            scheduler,
            max_turns=max_turns,
        )
        return runner.run(observer=observer)
