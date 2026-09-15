"""Tests for DroneState."""

import pytest

from fly_in.domain.connection import Connection
from fly_in.domain.drone import Drone
from fly_in.domain.zone import Zone, ZoneType
from fly_in.simulation.drone_state import DroneState, DroneStatus
from fly_in.simulation.transit_state import TransitState


def test_drone_starts_at_supplied_zone() -> None:
    """Initialize a drone as occupying its starting zone."""
    drone = Drone(1)
    start = Zone("start", 0, 0)

    state = DroneState(drone, start)

    assert state.drone is drone
    assert state.status is DroneStatus.AT_ZONE
    assert state.current_zone is start
    assert state.transit is None
    assert state.is_at_zone
    assert not state.is_in_transit
    assert not state.is_delivered


def test_move_to_changes_current_zone() -> None:
    """Move directly between one-turn zones."""
    start = Zone("start", 0, 0)
    destination = Zone("destination", 1, 0)
    state = DroneState(Drone(1), start)

    state.move_to(destination)

    assert state.status is DroneStatus.AT_ZONE
    assert state.current_zone is destination
    assert state.transit is None


def test_move_to_rejects_multi_turn_destination() -> None:
    """Require TransitState for a restricted destination."""
    start = Zone("start", 0, 0)
    destination = Zone(
        "restricted",
        1,
        0,
        ZoneType.RESTRICTED,
    )
    state = DroneState(Drone(1), start)

    with pytest.raises(
        ValueError,
        match="must use TransitState",
    ):
        state.move_to(destination)


def test_start_transit_removes_drone_from_current_zone() -> None:
    """Store transit data while the drone occupies no zone."""
    start = Zone("start", 0, 0)
    destination = Zone(
        "restricted",
        1,
        0,
        ZoneType.RESTRICTED,
    )
    transit = TransitState(
        Connection(start, destination),
        destination,
    )
    state = DroneState(Drone(1), start)

    state.start_transit(transit)

    assert state.status is DroneStatus.IN_TRANSIT
    assert state.current_zone is None
    assert state.transit is transit
    assert state.is_in_transit
    assert not state.is_at_zone


def test_start_transit_requires_current_zone_as_origin() -> None:
    """Reject a transit beginning at another zone."""
    current = Zone("current", 0, 0)
    origin = Zone("origin", 1, 0)
    destination = Zone(
        "restricted",
        2,
        0,
        ZoneType.RESTRICTED,
    )
    transit = TransitState(
        Connection(origin, destination),
        destination,
    )
    state = DroneState(Drone(1), current)

    with pytest.raises(
        ValueError,
        match="current drone zone",
    ):
        state.start_transit(transit)


def test_advance_transit_places_drone_at_destination() -> None:
    """Enter the destination when the active transit completes."""
    start = Zone("start", 0, 0)
    destination = Zone(
        "restricted",
        1,
        0,
        ZoneType.RESTRICTED,
    )
    transit = TransitState(
        Connection(start, destination),
        destination,
    )
    state = DroneState(Drone(1), start)
    state.start_transit(transit)

    state.advance_transit()

    assert state.status is DroneStatus.AT_ZONE
    assert state.current_zone is destination
    assert state.transit is None
    assert state.is_at_zone


def test_rejects_direct_move_while_in_transit() -> None:
    """Prevent a drone from starting another move in transit."""
    start = Zone("start", 0, 0)
    destination = Zone(
        "restricted",
        1,
        0,
        ZoneType.RESTRICTED,
    )
    other = Zone("other", 2, 0)
    transit = TransitState(
        Connection(start, destination),
        destination,
    )
    state = DroneState(Drone(1), start)
    state.start_transit(transit)

    with pytest.raises(
        RuntimeError,
        match="expected at_zone, found in_transit",
    ):
        state.move_to(other)


def test_mark_delivered_requires_end_zone_occupancy() -> None:
    """Reject delivery while the drone occupies another zone."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    state = DroneState(Drone(1), start)

    with pytest.raises(
        ValueError,
        match="must be at the end zone",
    ):
        state.mark_delivered(end)


def test_mark_delivered_preserves_end_zone() -> None:
    """Mark arrival while retaining the final zone for queries."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    state = DroneState(Drone(1), start)
    state.move_to(end)

    state.mark_delivered(end)

    assert state.status is DroneStatus.DELIVERED
    assert state.current_zone is end
    assert state.transit is None
    assert state.is_delivered


def test_rejects_movement_after_delivery() -> None:
    """Prevent delivered drones from moving again."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    other = Zone("other", 2, 0)
    state = DroneState(Drone(1), start)
    state.move_to(end)
    state.mark_delivered(end)

    with pytest.raises(
        RuntimeError,
        match="expected at_zone, found delivered",
    ):
        state.move_to(other)


def test_rejects_advance_without_active_transit() -> None:
    """Advance transit only while the drone is moving."""
    state = DroneState(
        Drone(1),
        Zone("start", 0, 0),
    )

    with pytest.raises(
        RuntimeError,
        match="expected in_transit, found at_zone",
    ):
        state.advance_transit()
