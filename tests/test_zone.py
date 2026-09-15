from fly_in.domain.zone import Zone, ZoneType


def test_normal_zone_defaults() -> None:
    zone = Zone("roof", 2, 3)

    assert zone.name == "roof"
    assert zone.x == 2
    assert zone.y == 3
    assert zone.zone_type == ZoneType.NORMAL
    assert zone.color is None
    assert zone.max_drones == 1
    assert zone.movement_cost() == 1
    assert zone.is_accessible()


def test_restricted_zone_costs_two_turns() -> None:
    zone = Zone(
        "restricted_area",
        4,
        5,
        ZoneType.RESTRICTED,
    )

    assert zone.movement_cost() == 2
    assert zone.is_accessible()


def test_blocked_zone_is_not_accessible() -> None:
    zone = Zone(
        "obstacle",
        5,
        5,
        ZoneType.BLOCKED,
    )

    assert not zone.is_accessible()


def test_priority_zone_costs_one_turn() -> None:
    zone = Zone(
        "priority_area",
        1,
        1,
        ZoneType.PRIORITY,
    )

    assert zone.movement_cost() == 1
