"""Execution of complete Fly-in simulation turns."""

from collections.abc import Sequence

from fly_in.domain.graph import Graph

from .movement import Movement
from .movement_validator import MovementValidator
from .simulation_event import EventKind, SimulationEvent
from .simulation_state import SimulationState
from .transit_state import TransitState


class Simulation:
    """Apply validated movements and maintain simulation state."""

    def __init__(
        self,
        graph: Graph,
        state: SimulationState,
        validator: MovementValidator | None = None,
    ) -> None:
        """Create a simulation engine."""
        self._graph = graph
        self._state = state
        self._validator = validator or MovementValidator()

    @property
    def graph(self) -> Graph:
        """Return the graph used by the simulation."""
        return self._graph

    @property
    def state(self) -> SimulationState:
        """Return the current dynamic simulation state."""
        return self._state

    @property
    def is_complete(self) -> bool:
        """Return whether every drone has reached the end zone."""
        return self._state.all_delivered

    def apply_turn(
        self,
        movements: Sequence[Movement],
    ) -> tuple[SimulationEvent, ...]:
        """Validate and atomically apply one complete simulation turn.

        Returns:
            Position updates produced by explicit movements and transit
            arrivals during this turn.
        """
        turn_movements = tuple(movements)
        self._validator.validate(
            self._graph,
            self._state,
            turn_movements,
        )

        transits_to_advance = self._state.states_in_transit()
        events: list[SimulationEvent] = []

        for movement in turn_movements:
            events.append(self._apply_movement(movement))

        for drone_state in transits_to_advance:
            transit = drone_state.transit
            if transit is None:
                raise RuntimeError("Drone transit data is missing.")

            drone_state.advance_transit()

            if drone_state.is_at_zone:
                events.append(
                    SimulationEvent(
                        drone_id=drone_state.drone.drone_id,
                        kind=EventKind.ZONE,
                        target=transit.destination.name,
                        destination=transit.destination,
                        connection=transit.connection,
                    )
                )
            else:
                events.append(
                    self._transit_event(
                        drone_state.drone.drone_id,
                        transit,
                    )
                )

        self._mark_delivered_drones()
        self._state.advance_turn()
        events.sort(key=lambda event: event.drone_id)
        return tuple(events)

    def _apply_movement(
        self,
        movement: Movement,
    ) -> SimulationEvent:
        """Apply one validated movement and return its output event."""
        drone_state = self._state.get_drone_state(movement.drone_id)

        if movement.requires_transit:
            transit = TransitState(
                movement.connection,
                movement.destination,
            )
            drone_state.start_transit(transit)
            return self._transit_event(movement.drone_id, transit)

        drone_state.move_to(movement.destination)
        return SimulationEvent(
            drone_id=movement.drone_id,
            kind=EventKind.ZONE,
            target=movement.destination.name,
            destination=movement.destination,
            connection=movement.connection,
        )

    def _transit_event(
        self,
        drone_id: int,
        transit: TransitState,
    ) -> SimulationEvent:
        """Create the output event for a drone on a connection."""
        target = f"{transit.origin.name}-{transit.destination.name}"
        return SimulationEvent(
            drone_id=drone_id,
            kind=EventKind.CONNECTION,
            target=target,
            destination=transit.destination,
            connection=transit.connection,
        )

    def _mark_delivered_drones(self) -> None:
        """Mark drones occupying the end zone as delivered."""
        for drone_state in self._state.drone_states:
            if (
                drone_state.is_at_zone
                and drone_state.current_zone is self._graph.end_zone
            ):
                drone_state.mark_delivered(self._graph.end_zone)
