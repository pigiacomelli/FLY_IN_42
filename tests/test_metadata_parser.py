import pytest

from fly_in.parsing.metadata_parser import MetadataParser


def test_parse_empty_metadata() -> None:
    parser = MetadataParser()

    assert parser.parse("") == {}


def test_parse_empty_block() -> None:
    parser = MetadataParser()

    assert parser.parse("[]") == {}


def test_parse_valid_metadata() -> None:
    parser = MetadataParser()

    result = parser.parse(
        "[zone=restricted color=red max_drones=2]"
    )

    assert result == {
        "zone": "restricted",
        "color": "red",
        "max_drones": "2",
    }


def test_parse_metadata_with_extra_spaces() -> None:
    parser = MetadataParser()

    result = parser.parse(
        "  [zone=normal   color=blue]  "
    )

    assert result == {
        "zone": "normal",
        "color": "blue",
    }


@pytest.mark.parametrize(
    "metadata",
    [
        "[zone]",
        "[=normal]",
        "[zone=]",
        "[zone=normal=extra]",
        "[zone=normal zone=blocked]",
        "[zone=normal",
        "zone=normal]",
    ],
)
def test_reject_invalid_metadata(metadata: str) -> None:
    parser = MetadataParser()

    with pytest.raises(ValueError):
        parser.parse(metadata)
