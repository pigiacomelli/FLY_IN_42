"""Tests for the Movement value object."""

from dataclasses import FrozenInstanceError

import pytest

from fly_in.domain.connection import Connection
from fly_in.domain.zone import Zone, ZoneType
from fly_in.simulation.movement import Movement


def test_create_valid_movement() -> None:
    origin = Zone("origin", 0, 0)
    destination = Zone("destination", 1, 0)
    connection = Connection(origin, destination)

    movement = Movement(
        drone_id=1,
        origin=origin,
        destination=destination,
        connection=connection,
    )

    assert movement.drone_id == 1
    assert movement.origin is origin
    assert movement.destination is destination
    assert movement.connection is connection


def test_normal_movement_costs_one_turn() -> None:
    origin = Zone("origin", 0, 0)
    destination = Zone("destination", 1, 0)
    connection = Connection(origin, destination)

    movement = Movement(
        drone_id=1,
        origin=origin,
        destination=destination,
        connection=connection,
    )

    assert movement.movement_cost == 1
    assert movement.requires_transit is False


def test_restricted_movement_requires_transit() -> None:
    origin = Zone("origin", 0, 0)
    destination = Zone(
        "restricted",
        1,
        0,
        zone_type=ZoneType.RESTRICTED,
    )
    connection = Connection(origin, destination)

    movement = Movement(
        drone_id=1,
        origin=origin,
        destination=destination,
        connection=connection,
    )

    assert movement.movement_cost == 2
    assert movement.requires_transit is True


@pytest.mark.parametrize("drone_id", [0, -1])
def test_drone_identifier_must_be_positive(
    drone_id: int,
) -> None:
    origin = Zone("origin", 0, 0)
    destination = Zone("destination", 1, 0)
    connection = Connection(origin, destination)

    with pytest.raises(ValueError):
        Movement(
            drone_id=drone_id,
            origin=origin,
            destination=destination,
            connection=connection,
        )


def test_origin_and_destination_must_differ() -> None:
    origin = Zone("origin", 0, 0)
    other = Zone("other", 1, 0)
    connection = Connection(origin, other)

    with pytest.raises(ValueError):
        Movement(
            drone_id=1,
            origin=origin,
            destination=origin,
            connection=connection,
        )


def test_connection_must_contain_origin() -> None:
    origin = Zone("origin", 0, 0)
    destination = Zone("destination", 1, 0)
    unrelated = Zone("unrelated", 2, 0)
    connection = Connection(unrelated, destination)

    with pytest.raises(ValueError):
        Movement(
            drone_id=1,
            origin=origin,
            destination=destination,
            connection=connection,
        )


def test_connection_must_contain_destination() -> None:
    origin = Zone("origin", 0, 0)
    destination = Zone("destination", 1, 0)
    unrelated = Zone("unrelated", 2, 0)
    connection = Connection(origin, unrelated)

    with pytest.raises(ValueError):
        Movement(
            drone_id=1,
            origin=origin,
            destination=destination,
            connection=connection,
        )


def test_movement_is_immutable() -> None:
    origin = Zone("origin", 0, 0)
    destination = Zone("destination", 1, 0)
    connection = Connection(origin, destination)

    movement = Movement(
        drone_id=1,
        origin=origin,
        destination=destination,
        connection=connection,
    )

    with pytest.raises(FrozenInstanceError):
        setattr(movement, "drone_id", 2)
