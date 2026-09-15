"""Tests for temporary pathfinding constraints."""

from fly_in.pathfinding.pathfinding_constraints import (
    PathfindingConstraints,
)


def test_empty_constraints_forbid_nothing() -> None:
    """Allow every zone and connection when no restrictions exist."""
    constraints = PathfindingConstraints()

    assert not constraints.is_zone_forbidden("a")
    assert not constraints.is_connection_forbidden("a", "b")


def test_forbids_configured_zones_only() -> None:
    """Reject configured zones while allowing all other zones."""
    constraints = PathfindingConstraints(
        forbidden_zones=frozenset({"a", "blocked_area"}),
    )

    assert constraints.is_zone_forbidden("a")
    assert constraints.is_zone_forbidden("blocked_area")
    assert not constraints.is_zone_forbidden("normal")


def test_forbids_connection_in_both_directions() -> None:
    """Treat a forbidden connection as bidirectional."""
    constraints = PathfindingConstraints(
        forbidden_connections=frozenset({("start", "a")}),
    )

    assert constraints.is_connection_forbidden("start", "a")
    assert constraints.is_connection_forbidden("a", "start")


def test_canonicalizes_all_forbidden_connections() -> None:
    """Normalize connection keys independently of input order."""
    constraints = PathfindingConstraints(
        forbidden_connections=frozenset({
            ("d", "c"),
            ("a", "b"),
        }),
    )

    assert constraints.is_connection_forbidden("c", "d")
    assert constraints.is_connection_forbidden("d", "c")
    assert constraints.is_connection_forbidden("a", "b")
    assert constraints.is_connection_forbidden("b", "a")
    assert not constraints.is_connection_forbidden("a", "d")
