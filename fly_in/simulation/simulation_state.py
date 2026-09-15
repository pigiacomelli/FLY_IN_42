"""Global dynamic state of the Fly-in simulation."""

from fly_in.domain.connection import Connection
from fly_in.domain.drone import Drone
from fly_in.domain.zone import Zone

from .drone_state import DroneState


class SimulationState:
    """Represent the dynamic state of all drones."""

    def __init__(
        self,
        drones: list[Drone],
        start_zone: Zone,
    ) -> None:
        """Create the initial simulation state.

        Every drone starts at the start zone.

        Args:
            drones: Drones participating in the simulation.
            start_zone: Initial zone occupied by all drones.

        Raises:
            ValueError: If two drones have the same identifier.
        """
        self._turn_number = 0
        self._drone_states: dict[int, DroneState] = {}

        for drone in drones:
            drone_id = drone.drone_id

            if drone_id in self._drone_states:
                raise ValueError(
                    f"Duplicate drone identifier: {drone_id}."
                )

            self._drone_states[drone_id] = DroneState(
                drone,
                start_zone,
            )

    @property
    def turn_number(self) -> int:
        """Return the current turn number."""
        return self._turn_number

    @property
    def drone_count(self) -> int:
        """Return the total number of drones."""
        return len(self._drone_states)

    @property
    def drone_states(self) -> tuple[DroneState, ...]:
        """Return all drone states."""
        return tuple(self._drone_states.values())

    def get_drone_state(
        self,
        drone_id: int,
    ) -> DroneState:
        """Return the state associated with a drone.

        Args:
            drone_id: Identifier of the requested drone.

        Returns:
            Current state of the drone.

        Raises:
            KeyError: If the drone does not exist.
        """
        try:
            return self._drone_states[drone_id]
        except KeyError as error:
            raise KeyError(
                f"Unknown drone identifier: {drone_id}."
            ) from error

    def states_at_zone(
        self,
        zone: Zone,
    ) -> tuple[DroneState, ...]:
        """Return states of drones occupying a zone."""
        return tuple(
            state
            for state in self._drone_states.values()
            if state.current_zone is zone
        )

    def zone_occupancy(
        self,
        zone: Zone,
    ) -> int:
        """Return the number of drones occupying a zone."""
        return len(self.states_at_zone(zone))

    def states_in_transit(
        self,
    ) -> tuple[DroneState, ...]:
        """Return states of drones currently in transit."""
        return tuple(
            state
            for state in self._drone_states.values()
            if state.is_in_transit
        )

    def states_using_connection(
        self,
        connection: Connection,
    ) -> tuple[DroneState, ...]:
        """Return drones currently using a connection."""
        return tuple(
            state
            for state in self._drone_states.values()
            if (
                state.transit is not None
                and state.transit.connection is connection
            )
        )

    def connection_occupancy(
        self,
        connection: Connection,
    ) -> int:
        """Return the number of drones using a connection."""
        return len(
            self.states_using_connection(connection)
        )

    def delivered_states(
        self,
    ) -> tuple[DroneState, ...]:
        """Return states of delivered drones."""
        return tuple(
            state
            for state in self._drone_states.values()
            if state.is_delivered
        )

    @property
    def delivered_count(self) -> int:
        """Return the number of delivered drones."""
        return len(self.delivered_states())

    @property
    def all_delivered(self) -> bool:
        """Return whether every drone has been delivered."""
        return all(
            state.is_delivered
            for state in self._drone_states.values()
        )

    def advance_turn(self) -> None:
        """Advance the simulation turn counter."""
        self._turn_number += 1
