"""Tests for TransitState."""

import pytest

from fly_in.domain.connection import Connection
from fly_in.domain.zone import Zone, ZoneType
from fly_in.simulation.transit_state import TransitState


def test_creates_transit_for_multi_turn_destination() -> None:
    """Create transit using the destination movement cost."""
    origin = Zone("origin", 0, 0)
    destination = Zone(
        "restricted",
        1,
        0,
        ZoneType.RESTRICTED,
    )
    connection = Connection(origin, destination)

    transit = TransitState(connection, destination)

    assert transit.connection is connection
    assert transit.origin is origin
    assert transit.destination is destination
    assert transit.remaining_turns == 1
    assert not transit.is_complete


def test_advance_completes_restricted_transit() -> None:
    """Complete a restricted movement on the following turn."""
    origin = Zone("origin", 0, 0)
    destination = Zone(
        "restricted",
        1,
        0,
        ZoneType.RESTRICTED,
    )
    transit = TransitState(
        Connection(origin, destination),
        destination,
    )

    completed = transit.advance()

    assert completed
    assert transit.remaining_turns == 0
    assert transit.is_complete


def test_rejects_advance_after_transit_is_complete() -> None:
    """Reject advancing a transit that already ended."""
    origin = Zone("origin", 0, 0)
    destination = Zone(
        "restricted",
        1,
        0,
        ZoneType.RESTRICTED,
    )
    transit = TransitState(
        Connection(origin, destination),
        destination,
    )
    transit.advance()

    with pytest.raises(
        RuntimeError,
        match="completed transit",
    ):
        transit.advance()


def test_rejects_destination_outside_connection() -> None:
    """Require the destination to belong to the connection."""
    origin = Zone("origin", 0, 0)
    other = Zone("other", 1, 0)
    destination = Zone(
        "restricted",
        2,
        0,
        ZoneType.RESTRICTED,
    )
    connection = Connection(origin, other)

    with pytest.raises(
        ValueError,
        match="contain the destination zone",
    ):
        TransitState(connection, destination)


def test_rejects_transit_for_one_turn_destination() -> None:
    """Use direct movement for normal and priority destinations."""
    origin = Zone("origin", 0, 0)
    destination = Zone("normal", 1, 0)
    connection = Connection(origin, destination)

    with pytest.raises(
        ValueError,
        match="multi-turn movements",
    ):
        TransitState(connection, destination)
