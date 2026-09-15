"""Validation of simultaneous drone movements."""

from collections.abc import Sequence

from fly_in.domain.connection import Connection
from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone
from fly_in.errors import MovementValidationError

from .movement import Movement
from .simulation_state import SimulationState


class MovementValidator:
    """Validate movements proposed for one simulation turn."""

    def validate(
        self,
        graph: Graph,
        state: SimulationState,
        movements: Sequence[Movement],
    ) -> None:
        """Validate a complete set of simultaneous movements.

        Args:
            graph: Graph used by the simulation.
            state: Current dynamic simulation state.
            movements: Movements proposed for the current turn.

        Raises:
            MovementValidationError: If any movement is invalid.
        """
        self._validate_unique_drones(movements)

        for movement in movements:
            self._validate_movement(
                graph,
                state,
                movement,
            )

        self._validate_zone_capacities(
            graph,
            state,
            movements,
        )

        self._validate_forced_arrival_capacities(
            graph,
            state,
            movements,
        )

        self._validate_connection_capacities(
            state,
            movements,
        )

    def _validate_unique_drones(
        self,
        movements: Sequence[Movement],
    ) -> None:
        """Ensure that each drone moves at most once."""
        moving_drones: set[int] = set()

        for movement in movements:
            if movement.drone_id in moving_drones:
                raise MovementValidationError(
                    f"Drone {movement.drone_id} has multiple "
                    "movements in the same turn."
                )

            moving_drones.add(movement.drone_id)

    def _validate_movement(
        self,
        graph: Graph,
        state: SimulationState,
        movement: Movement,
    ) -> None:
        """Validate one movement against the current state."""
        try:
            drone_state = state.get_drone_state(
                movement.drone_id
            )
        except KeyError as error:
            raise MovementValidationError(
                "Unknown drone identifier: "
                f"{movement.drone_id}."
            ) from error

        if not drone_state.is_at_zone:
            raise MovementValidationError(
                f"Drone {movement.drone_id} is not "
                "available at a zone."
            )

        if drone_state.current_zone is not movement.origin:
            raise MovementValidationError(
                f"Drone {movement.drone_id} is not "
                f"at zone {movement.origin.name}."
            )

        if not movement.destination.is_accessible():
            raise MovementValidationError(
                f"Zone {movement.destination.name} "
                "is not accessible."
            )

        try:
            graph_connections = graph.get_connections(
                movement.origin
            )
        except KeyError as error:
            raise MovementValidationError(
                f"Zone {movement.origin.name} does not "
                "belong to the graph."
            ) from error

        if movement.connection not in graph_connections:
            raise MovementValidationError(
                "The movement connection does not "
                "belong to the graph."
            )

    def _validate_zone_capacities(
        self,
        graph: Graph,
        state: SimulationState,
        movements: Sequence[Movement],
    ) -> None:
        """Validate capacities after this turn's movements."""
        projected_occupancy: dict[Zone, int] = {}

        for drone_state in state.drone_states:
            zone = drone_state.current_zone

            if zone is None:
                continue

            projected_occupancy[zone] = (
                projected_occupancy.get(zone, 0) + 1
            )

        for drone_state in state.states_in_transit():
            transit = drone_state.transit

            if transit is None:
                raise MovementValidationError(
                    "A drone in transit has no transit data."
                )

            if transit.remaining_turns != 1:
                continue

            destination = transit.destination

            projected_occupancy[destination] = (
                projected_occupancy.get(destination, 0) + 1
            )

        for movement in movements:
            origin = movement.origin

            projected_occupancy[origin] = (
                projected_occupancy.get(origin, 0) - 1
            )

            if movement.requires_transit:
                continue

            destination = movement.destination

            projected_occupancy[destination] = (
                projected_occupancy.get(destination, 0) + 1
            )

        for zone, occupancy in projected_occupancy.items():
            if self._has_unlimited_capacity(
                graph,
                zone,
            ):
                continue

            if occupancy > zone.max_drones:
                raise MovementValidationError(
                    f"Zone {zone.name} exceeds its capacity: "
                    f"{occupancy}/{zone.max_drones} drones."
                )

    def _validate_forced_arrival_capacities(
        self,
        graph: Graph,
        state: SimulationState,
        movements: Sequence[Movement],
    ) -> None:
        """Prevent unavoidable future arrival conflicts."""
        arrivals: dict[
            tuple[Zone, int],
            int,
        ] = {}

        for drone_state in state.states_in_transit():
            transit = drone_state.transit

            if transit is None:
                raise MovementValidationError(
                    "A drone in transit has no transit data."
                )

            arrival_offset = (
                transit.remaining_turns - 1
            )

            key = (
                transit.destination,
                arrival_offset,
            )

            arrivals[key] = arrivals.get(key, 0) + 1

        for movement in movements:
            if not movement.requires_transit:
                continue

            arrival_offset = (
                movement.movement_cost - 1
            )

            key = (
                movement.destination,
                arrival_offset,
            )

            arrivals[key] = arrivals.get(key, 0) + 1

        for (
            zone,
            arrival_offset,
        ), drone_count in arrivals.items():
            if self._has_unlimited_capacity(
                graph,
                zone,
            ):
                continue

            if drone_count > zone.max_drones:
                raise MovementValidationError(
                    f"Zone {zone.name} has "
                    f"{drone_count} forced arrivals "
                    f"after {arrival_offset} turns, but "
                    f"its capacity is {zone.max_drones}."
                )

    def _validate_connection_capacities(
        self,
        state: SimulationState,
        movements: Sequence[Movement],
    ) -> None:
        """Validate simultaneous connection usage."""
        occupancy: dict[Connection, int] = {}

        for drone_state in state.states_in_transit():
            transit = drone_state.transit

            if transit is None:
                raise MovementValidationError(
                    "A drone in transit has no transit data."
                )

            connection = transit.connection

            occupancy[connection] = (
                occupancy.get(connection, 0) + 1
            )

        for movement in movements:
            connection = movement.connection

            occupancy[connection] = (
                occupancy.get(connection, 0) + 1
            )

        for connection, drone_count in occupancy.items():
            if drone_count > connection.max_capacity:
                raise MovementValidationError(
                    "Connection between "
                    f"{connection.zone_a.name} and "
                    f"{connection.zone_b.name} exceeds its "
                    f"capacity: {drone_count}/"
                    f"{connection.max_capacity} drones."
                )

    @staticmethod
    def _has_unlimited_capacity(
        graph: Graph,
        zone: Zone,
    ) -> bool:
        """Return whether a zone ignores occupancy limits."""
        return (
            zone is graph.start_zone
            or zone is graph.end_zone
        )
