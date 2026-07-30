"""Tests for the PathCost class."""

import pytest

from fly_in.domain.zone import Zone, ZoneType
from fly_in.pathfinding.path_cost import PathCost


def test_default_cost_is_zero() -> None:
    """Create a zero-valued path cost by default."""
    cost = PathCost()

    assert cost.turns == 0
    assert cost.priority_zones == 0


def test_rejects_negative_values() -> None:
    """Reject negative turn and priority values."""
    with pytest.raises(
        ValueError,
        match="Turns cannot be negative",
    ):
        PathCost(turns=-1)

    with pytest.raises(
        ValueError,
        match="Priority zone count cannot be negative",
    ):
        PathCost(priority_zones=-1)


def test_extends_cost_for_normal_zone() -> None:
    """Add one turn when entering a normal zone."""
    normal = Zone("normal", 0, 0)

    result = PathCost().extend(normal)

    assert result == PathCost(turns=1, priority_zones=0)


def test_extends_cost_for_restricted_zone() -> None:
    """Add two turns when entering a restricted zone."""
    restricted = Zone(
        "restricted",
        0,
        0,
        ZoneType.RESTRICTED,
    )

    result = PathCost().extend(restricted)

    assert result == PathCost(turns=2, priority_zones=0)


def test_extends_cost_for_priority_zone() -> None:
    """Add one turn and one preference when entering priority."""
    priority = Zone(
        "priority",
        0,
        0,
        ZoneType.PRIORITY,
    )

    result = PathCost().extend(priority)

    assert result == PathCost(turns=1, priority_zones=1)


def test_extend_does_not_modify_original_cost() -> None:
    """Return a new cost without modifying the original."""
    original = PathCost(turns=2, priority_zones=1)
    normal = Zone("normal", 0, 0)

    result = original.extend(normal)

    assert original == PathCost(turns=2, priority_zones=1)
    assert result == PathCost(turns=3, priority_zones=1)
    assert result is not original


def test_fewer_turns_are_preferred() -> None:
    """Prefer fewer turns regardless of priority count."""
    faster = PathCost(turns=2, priority_zones=0)
    slower = PathCost(turns=3, priority_zones=10)

    assert faster < slower
    assert not slower < faster


def test_more_priority_zones_win_when_turns_tie() -> None:
    """Prefer more priority zones when turn counts are equal."""
    preferred = PathCost(turns=3, priority_zones=2)
    other = PathCost(turns=3, priority_zones=0)

    assert preferred < other
    assert not other < preferred


def test_equal_costs_compare_as_equal() -> None:
    """Treat identical turns and priority counts as equal."""
    left = PathCost(turns=4, priority_zones=2)
    right = PathCost(turns=4, priority_zones=2)

    assert left == right
    assert not left < right
    assert not right < left
