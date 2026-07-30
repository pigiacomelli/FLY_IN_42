"""Tests for the Path class."""

import pytest

from fly_in.domain.zone import Zone
from fly_in.pathfinding.path import Path


def test_rejects_empty_path() -> None:
    """Reject a path without zones."""
    with pytest.raises(
        ValueError,
        match="Path must contain at least one zone",
    ):
        Path([])


def test_preserves_zone_order() -> None:
    """Preserve the order of the zones received."""
    start = Zone("start", 0, 0)
    middle = Zone("middle", 1, 0)
    end = Zone("end", 2, 0)

    path = Path([start, middle, end])

    assert path.zones == (start, middle, end)
    assert path.start is start
    assert path.end is end
    assert path.hop_count == 2


def test_single_zone_path_has_zero_hops() -> None:
    """Return zero hops for a path containing one zone."""
    zone = Zone("only", 0, 0)

    path = Path([zone])

    assert path.start is zone
    assert path.end is zone
    assert path.hop_count == 0


def test_is_not_affected_by_original_list_mutation() -> None:
    """Remain unchanged when the original list is modified."""
    start = Zone("start", 0, 0)
    end = Zone("end", 1, 0)
    other = Zone("other", 2, 0)
    zones = [start, end]

    path = Path(zones)
    zones.append(other)

    assert path.zones == (start, end)
    assert path.end is end
    assert path.hop_count == 1
