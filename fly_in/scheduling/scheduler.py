"""Turn-by-turn movement scheduling for Fly-in simulations."""

from collections.abc import Mapping, Sequence

from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone
from fly_in.errors import MovementValidationError, RoutePlanningError
from fly_in.simulation.drone_state import DroneState
from fly_in.simulation.movement import Movement
from fly_in.simulation.movement_validator import MovementValidator
from fly_in.simulation.simulation_state import SimulationState

from .drone_route import DroneRoute


class Scheduler:
    """Build the largest safe greedy set of forward route movements."""

    def __init__(
        self,
        graph: Graph,
        routes: Mapping[int, DroneRoute],
        validator: MovementValidator | None = None,
    ) -> None:
        """Create a scheduler for preassigned drone routes."""
        self._graph = graph
        self._routes = dict(routes)
        self._validator = validator or MovementValidator()

    def plan_turn(
        self,
        state: SimulationState,
    ) -> tuple[Movement, ...]:
        """Return a valid set of simultaneous movements for one turn.

        Drones nearer to the end are considered first so that downstream
        zones are released before upstream drones attempt to enter them.
        Every tentative addition is checked by the same validator used by
        the simulation engine.
        """
        pending = self._movement_candidates(state)
        scheduled: list[Movement] = []
        made_progress = True

        while pending and made_progress:
            made_progress = False
            blocked: list[Movement] = []

            for candidate in pending:
                tentative = [*scheduled, candidate]

                if not self._restricted_arrival_is_safe(
                    state,
                    tentative,
                    candidate,
                ):
                    blocked.append(candidate)
                    continue

                try:
                    self._validator.validate(
                        self._graph,
                        state,
                        tentative,
                    )
                except MovementValidationError:
                    blocked.append(candidate)
                    continue

                scheduled.append(candidate)
                made_progress = True

            pending = blocked

        return tuple(scheduled)

    def _movement_candidates(
        self,
        state: SimulationState,
    ) -> list[Movement]:
        """Create deterministic forward movement candidates."""
        available = [
            drone_state
            for drone_state in state.drone_states
            if drone_state.is_at_zone
            and not drone_state.is_delivered
        ]
        available.sort(
            key=lambda drone_state: self._priority_key(drone_state),
        )

        candidates: list[Movement] = []

        for drone_state in available:
            current_zone = drone_state.current_zone
            if current_zone is None:
                continue

            route = self._route_for(drone_state)
            destination = route.next_zone(current_zone)

            if destination is None:
                continue

            connection = self._graph.find_connection(
                current_zone,
                destination,
            )
            candidates.append(
                Movement(
                    drone_id=drone_state.drone.drone_id,
                    origin=current_zone,
                    destination=destination,
                    connection=connection,
                )
            )

        return candidates

    def _priority_key(
        self,
        drone_state: DroneState,
    ) -> tuple[int, int, int]:
        """Prioritize downstream and shorter remaining routes."""
        current_zone = drone_state.current_zone
        if current_zone is None:
            return (0, 0, drone_state.drone.drone_id)

        route = self._route_for(drone_state)
        index = route.index_of(current_zone)
        remaining = route.remaining_cost(current_zone)

        return (
            remaining,
            -index,
            drone_state.drone.drone_id,
        )

    def _route_for(self, drone_state: DroneState) -> DroneRoute:
        """Return and validate the route associated with a state."""
        drone_id = drone_state.drone.drone_id

        try:
            return self._routes[drone_id]
        except KeyError as error:
            raise RoutePlanningError(
                f"Drone {drone_id} has no assigned route."
            ) from error

    def _restricted_arrival_is_safe(
        self,
        state: SimulationState,
        movements: Sequence[Movement],
        candidate: Movement,
    ) -> bool:
        """Conservatively reserve capacity for next-turn arrivals.

        A newly started restricted movement must arrive on the next turn.
        We only start it when the destination capacity remaining after the
        current turn can hold every already reserved and newly reserved
        arrival. This prevents a drone from becoming stuck on a connection.
        """
        if not candidate.requires_transit:
            return True

        destination = candidate.destination
        if destination is self._graph.end_zone:
            return True

        projected = self._projected_occupancy(
            state,
            movements,
            destination,
        )
        future_arrivals = self._future_arrivals(
            state,
            movements,
            destination,
        )

        return projected + future_arrivals <= destination.max_drones

    def _projected_occupancy(
        self,
        state: SimulationState,
        movements: Sequence[Movement],
        zone: Zone,
    ) -> int:
        """Return occupancy at the end of the current turn."""
        occupancy = state.zone_occupancy(zone)

        for drone_state in state.states_in_transit():
            transit = drone_state.transit
            if (
                transit is not None
                and transit.remaining_turns == 1
                and transit.destination is zone
            ):
                occupancy += 1

        for movement in movements:
            if movement.origin is zone:
                occupancy -= 1

            if (
                not movement.requires_transit
                and movement.destination is zone
            ):
                occupancy += 1

        return occupancy

    def _future_arrivals(
        self,
        state: SimulationState,
        movements: Sequence[Movement],
        zone: Zone,
    ) -> int:
        """Count arrivals reserved for the turn after this one."""
        arrivals = 0

        for drone_state in state.states_in_transit():
            transit = drone_state.transit
            if (
                transit is not None
                and transit.remaining_turns == 2
                and transit.destination is zone
            ):
                arrivals += 1

        for movement in movements:
            if (
                movement.requires_transit
                and movement.destination is zone
            ):
                arrivals += 1

        return arrivals
