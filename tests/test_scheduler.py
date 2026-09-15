"""Tests for safe greedy movement scheduling."""

from fly_in.domain.connection import Connection
from fly_in.domain.drone import Drone
from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone
from fly_in.pathfinding.path import Path
from fly_in.scheduling.drone_route import DroneRoute
from fly_in.scheduling.scheduler import Scheduler
from fly_in.simulation.simulation import Simulation
from fly_in.simulation.simulation_state import SimulationState


def test_pipelines_drones_through_capacity_one_zones() -> None:
    """Move downstream first and release a zone in the same turn."""
    start = Zone("start", 0, 0)
    middle = Zone("middle", 1, 0)
    end = Zone("end", 2, 0)
    start_middle = Connection(start, middle)
    middle_end = Connection(middle, end)
    graph = Graph(
        [start, middle, end],
        [start_middle, middle_end],
        start,
        end,
    )
    drones = [Drone(1), Drone(2)]
    path = Path([start, middle, end])
    routes = {
        drone.drone_id: DroneRoute(drone.drone_id, path)
        for drone in drones
    }
    state = SimulationState(drones, start)
    scheduler = Scheduler(graph, routes)
    simulation = Simulation(graph, state)

    first_turn = scheduler.plan_turn(state)
    assert [movement.drone_id for movement in first_turn] == [1]
    simulation.apply_turn(first_turn)

    second_turn = scheduler.plan_turn(state)
    assert {movement.drone_id for movement in second_turn} == {1, 2}
