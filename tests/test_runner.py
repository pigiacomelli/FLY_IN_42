"""Integration tests for the complete simulation loop."""

from fly_in.domain.connection import Connection
from fly_in.domain.drone import Drone
from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone
from fly_in.pathfinding.path import Path
from fly_in.scheduling.drone_route import DroneRoute
from fly_in.scheduling.scheduler import Scheduler
from fly_in.simulation.runner import SimulationRunner
from fly_in.simulation.simulation import Simulation
from fly_in.simulation.simulation_state import SimulationState


def test_completes_linear_two_drone_simulation_in_four_turns() -> None:
    """Pipeline two drones through a three-hop linear graph."""
    start = Zone("start", 0, 0)
    first = Zone("first", 1, 0)
    second = Zone("second", 2, 0)
    end = Zone("end", 3, 0)
    connections = [
        Connection(start, first),
        Connection(first, second),
        Connection(second, end),
    ]
    graph = Graph(
        [start, first, second, end],
        connections,
        start,
        end,
    )
    drones = [Drone(1), Drone(2)]
    path = Path([start, first, second, end])
    routes = {
        drone.drone_id: DroneRoute(drone.drone_id, path)
        for drone in drones
    }
    state = SimulationState(drones, start)
    simulation = Simulation(graph, state)
    scheduler = Scheduler(graph, routes)

    result = SimulationRunner(simulation, scheduler).run()

    assert result.turn_count == 4
    assert state.all_delivered
