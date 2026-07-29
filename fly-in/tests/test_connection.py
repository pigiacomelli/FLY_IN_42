import pytest

from fly_in.domain.connection import Connection
from fly_in.domain.zone import Zone


def test_connection_contains_both_zones() -> None:
    zone_a = Zone("a", 0, 0)
    zone_b = Zone("b", 1, 1)

    connection = Connection(zone_a, zone_b)

    assert connection.connects(zone_a)
    assert connection.connects(zone_b)


def test_connection_returns_opposite_zone() -> None:
    zone_a = Zone("a", 0, 0)
    zone_b = Zone("b", 1, 1)

    connection = Connection(zone_a, zone_b)

    assert connection.other_zone(zone_a) is zone_b
    assert connection.other_zone(zone_b) is zone_a


def test_connection_rejects_unrelated_zone() -> None:
    zone_a = Zone("a", 0, 0)
    zone_b = Zone("b", 1, 1)
    unrelated = Zone("c", 2, 2)

    connection = Connection(zone_a, zone_b)

    with pytest.raises(ValueError):
        connection.other_zone(unrelated)


def test_default_connection_capacity() -> None:
    zone_a = Zone("a", 0, 0)
    zone_b = Zone("b", 1, 1)

    connection = Connection(zone_a, zone_b)

    assert connection.max_capacity == 1
