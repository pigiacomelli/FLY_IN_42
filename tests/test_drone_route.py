"""Tests for immutable per-drone routes."""

import pytest

from fly_in.domain.zone import Zone, ZoneType
from fly_in.pathfinding.path import Path
from fly_in.scheduling.drone_route import DroneRoute


def test_reports_next_zone_and_remaining_cost() -> None:
    """Follow a path without maintaining duplicated mutable progress."""
    start = Zone("start", 0, 0)
    restricted = Zone(
        "restricted",
        1,
        0,
        zone_type=ZoneType.RESTRICTED,
    )
    end = Zone("end", 2, 0)
    route = DroneRoute(1, Path([start, restricted, end]))

    assert route.next_zone(start) is restricted
    assert route.next_zone(restricted) is end
    assert route.next_zone(end) is None
    assert route.remaining_cost(start) == 3
    assert route.remaining_cost(restricted) == 1


def test_rejects_repeated_zone() -> None:
    """Require simple paths so a zone maps to one progress index."""
    start = Zone("start", 0, 0)
    middle = Zone("middle", 1, 0)

    with pytest.raises(ValueError, match="simple paths"):
        DroneRoute(1, Path([start, middle, start]))
