from pathlib import Path

import pytest

from fly_in.domain.zone import ZoneType
from fly_in.errors import MapParseError
from fly_in.parsing.parser import Parser


def write_map(
    tmp_path: Path,
    content: str,
) -> Path:
    """Create a temporary map file."""
    map_path = tmp_path / "map.txt"
    map_path.write_text(content, encoding="utf-8")

    return map_path


def test_parse_valid_map(
    tmp_path: Path,
) -> None:
    map_path = write_map(
        tmp_path,
        """
        nb_drones: 5
        start_hub: start 0 0 [color=green]
        hub: roof 1 0 [zone=restricted max_drones=2]
        end_hub: goal 2 0 [color=yellow]
        connection: start-roof
        connection: roof-goal [max_link_capacity=2]
        """,
    )

    result = Parser().parse(map_path)

    assert result.drone_count == 5
    assert result.graph.start_zone.name == "start"
    assert result.graph.end_zone.name == "goal"

    roof = result.graph.get_zone("roof")

    assert roof.zone_type == ZoneType.RESTRICTED
    assert roof.max_drones == 2


def test_parser_ignores_comments(
    tmp_path: Path,
) -> None:
    map_path = write_map(
        tmp_path,
        """
        # Map comment
        nb_drones: 2

        start_hub: start 0 0
        end_hub: goal 1 0  # Inline comment
        connection: start-goal
        """,
    )

    result = Parser().parse(map_path)

    assert result.drone_count == 2


@pytest.mark.parametrize(
    "content",
    [
        """
        nb_drones: 0
        start_hub: start 0 0
        end_hub: goal 1 0
        connection: start-goal
        """,
        """
        nb_drones: invalid
        start_hub: start 0 0
        end_hub: goal 1 0
        connection: start-goal
        """,
        """
        hub: zone 0 0
        """,
    ],
)
def test_reject_invalid_drone_count(
    tmp_path: Path,
    content: str,
) -> None:
    map_path = write_map(tmp_path, content)

    with pytest.raises(MapParseError):
        Parser().parse(map_path)


def test_reject_duplicate_zone(
    tmp_path: Path,
) -> None:
    map_path = write_map(
        tmp_path,
        """
        nb_drones: 2
        start_hub: start 0 0
        hub: start 1 0
        end_hub: goal 2 0
        """,
    )

    with pytest.raises(
        MapParseError,
        match="Duplicate zone",
    ):
        Parser().parse(map_path)


def test_reject_unknown_connection_zone(
    tmp_path: Path,
) -> None:
    map_path = write_map(
        tmp_path,
        """
        nb_drones: 2
        start_hub: start 0 0
        end_hub: goal 1 0
        connection: start-unknown
        """,
    )

    with pytest.raises(
        MapParseError,
        match="previously defined",
    ):
        Parser().parse(map_path)


def test_reject_duplicate_connection(
    tmp_path: Path,
) -> None:
    map_path = write_map(
        tmp_path,
        """
        nb_drones: 2
        start_hub: start 0 0
        end_hub: goal 1 0
        connection: start-goal
        connection: goal-start
        """,
    )

    with pytest.raises(
        MapParseError,
        match="Duplicate connection",
    ):
        Parser().parse(map_path)


def test_reject_invalid_zone_type(
    tmp_path: Path,
) -> None:
    map_path = write_map(
        tmp_path,
        """
        nb_drones: 2
        start_hub: start 0 0
        hub: roof 1 0 [zone=dangerous]
        end_hub: goal 2 0
        """,
    )

    with pytest.raises(
        MapParseError,
        match="Invalid zone type",
    ):
        Parser().parse(map_path)


def test_reject_non_positive_capacity(
    tmp_path: Path,
) -> None:
    map_path = write_map(
        tmp_path,
        """
        nb_drones: 2
        start_hub: start 0 0
        hub: roof 1 0 [max_drones=0]
        end_hub: goal 2 0
        """,
    )

    with pytest.raises(
        MapParseError,
        match="max_drones must be positive",
    ):
        Parser().parse(map_path)


def test_reject_missing_start(
    tmp_path: Path,
) -> None:
    map_path = write_map(
        tmp_path,
        """
        nb_drones: 2
        end_hub: goal 1 0
        """,
    )

    with pytest.raises(
        MapParseError,
        match="start_hub",
    ):
        Parser().parse(map_path)


def test_reject_missing_end(
    tmp_path: Path,
) -> None:
    map_path = write_map(
        tmp_path,
        """
        nb_drones: 2
        start_hub: start 0 0
        """,
    )

    with pytest.raises(
        MapParseError,
        match="end_hub",
    ):
        Parser().parse(map_path)


def test_ignores_max_drones_metadata_on_start_and_end(
    tmp_path: Path,
) -> None:
    """Ignore even non-numeric max_drones on unlimited endpoint hubs."""
    map_path = write_map(
        tmp_path,
        """
        nb_drones: 2
        start_hub: start 0 0 [max_drones=ignored]
        end_hub: goal 1 0 [max_drones=also_ignored]
        connection: start-goal
        """,
    )

    result = Parser().parse(map_path)

    assert result.graph.start_zone.name == "start"
    assert result.graph.end_zone.name == "goal"


def test_reject_non_positive_connection_capacity(
    tmp_path: Path,
) -> None:
    """Require max_link_capacity to be a positive integer."""
    map_path = write_map(
        tmp_path,
        """
        nb_drones: 2
        start_hub: start 0 0
        end_hub: goal 1 0
        connection: start-goal [max_link_capacity=0]
        """,
    )

    with pytest.raises(
        MapParseError,
        match="max_link_capacity must be positive",
    ):
        Parser().parse(map_path)


def test_reject_zone_name_with_dash(
    tmp_path: Path,
) -> None:
    """Reject zone names that conflict with connection syntax."""
    map_path = write_map(
        tmp_path,
        """
        nb_drones: 1
        start_hub: start-zone 0 0
        end_hub: goal 1 0
        """,
    )

    with pytest.raises(
        MapParseError,
        match="cannot contain dashes",
    ):
        Parser().parse(map_path)


def test_reject_multiple_start_hubs(
    tmp_path: Path,
) -> None:
    """Require exactly one start hub."""
    map_path = write_map(
        tmp_path,
        """
        nb_drones: 1
        start_hub: start 0 0
        start_hub: start2 1 0
        end_hub: goal 2 0
        """,
    )

    with pytest.raises(
        MapParseError,
        match="Multiple start zones",
    ):
        Parser().parse(map_path)


def test_reject_unknown_zone_metadata_key(
    tmp_path: Path,
) -> None:
    """Reject unsupported metadata fields with a line-specific parse error."""
    map_path = write_map(
        tmp_path,
        """
        nb_drones: 1
        start_hub: start 0 0
        hub: middle 1 0 [speed=3]
        end_hub: goal 2 0
        """,
    )

    with pytest.raises(
        MapParseError,
        match="Unknown zone metadata key 'speed'",
    ):
        Parser().parse(map_path)
