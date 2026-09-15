"""Main parser for Fly-in map files."""

from pathlib import Path

from fly_in.domain.connection import Connection
from fly_in.domain.graph import Graph
from fly_in.domain.zone import Zone, ZoneType
from fly_in.errors import MapFileError, MapParseError
from fly_in.parsing.metadata_parser import MetadataParser
from fly_in.parsing.parsed_map import ParsedMap


class Parser:
    """Parse and validate Fly-in map files."""

    _ZONE_PREFIXES = {
        "start_hub",
        "end_hub",
        "hub",
    }

    _ZONE_METADATA_KEYS = {
        "zone",
        "color",
        "max_drones",
    }

    _CONNECTION_METADATA_KEYS = {
        "max_link_capacity",
    }

    def __init__(self) -> None:
        """Create a parser with its metadata parser dependency."""
        self._metadata_parser = MetadataParser()

    def parse(
        self,
        file_path: str | Path,
    ) -> ParsedMap:
        """Parse a map file.

        Args:
            file_path: Path to the map file.

        Returns:
            Parsed map containing the graph and drone count.

        Raises:
            MapFileError: If the file cannot be read.
            MapParseError: If the map content is invalid.
        """
        lines = self._read_lines(Path(file_path))
        meaningful_lines = self._clean_lines(lines)

        if not meaningful_lines:
            raise MapParseError(
                1,
                "Map file is empty.",
            )

        first_line_number, first_line = meaningful_lines[0]

        drone_count = self._parse_drone_count(
            first_line,
            first_line_number,
        )

        zones: dict[str, Zone] = {}
        connections: list[Connection] = []
        connection_keys: set[tuple[str, str]] = set()

        start_zone: Zone | None = None
        end_zone: Zone | None = None

        for line_number, line in meaningful_lines[1:]:
            prefix, payload = self._split_instruction(
                line,
                line_number,
            )

            if prefix in self._ZONE_PREFIXES:
                zone = self._parse_zone(
                    prefix,
                    payload,
                    line_number,
                    zones,
                )

                if prefix == "start_hub":
                    if start_zone is not None:
                        raise MapParseError(
                            line_number,
                            "Multiple start zones are not allowed.",
                        )

                    start_zone = zone

                elif prefix == "end_hub":
                    if end_zone is not None:
                        raise MapParseError(
                            line_number,
                            "Multiple end zones are not allowed.",
                        )

                    end_zone = zone

            elif prefix == "connection":
                connection = self._parse_connection(
                    payload,
                    line_number,
                    zones,
                    connection_keys,
                )

                connections.append(connection)

            elif prefix == "nb_drones":
                raise MapParseError(
                    line_number,
                    "nb_drones must appear only once "
                    "as the first instruction.",
                )

            else:
                raise MapParseError(
                    line_number,
                    f"Unknown instruction '{prefix}'.",
                )

        last_line_number = meaningful_lines[-1][0]

        if start_zone is None:
            raise MapParseError(
                last_line_number,
                "Map must contain exactly one start_hub.",
            )

        if end_zone is None:
            raise MapParseError(
                last_line_number,
                "Map must contain exactly one end_hub.",
            )

        graph = Graph(
            zones=list(zones.values()),
            connections=connections,
            start_zone=start_zone,
            end_zone=end_zone,
        )

        return ParsedMap(
            drone_count=drone_count,
            graph=graph,
        )

    def _read_lines(
        self,
        file_path: Path,
    ) -> list[str]:
        """Read all lines from a map file."""
        try:
            with file_path.open(
                "r",
                encoding="utf-8",
            ) as map_file:
                return map_file.readlines()

        except OSError as error:
            raise MapFileError(
                f"Unable to read map file "
                f"'{file_path}': {error}"
            ) from error

    def _clean_lines(
        self,
        lines: list[str],
    ) -> list[tuple[int, str]]:
        """Remove comments and blank lines."""
        cleaned_lines: list[tuple[int, str]] = []

        for line_number, raw_line in enumerate(
            lines,
            start=1,
        ):
            line = raw_line.split("#", 1)[0].strip()

            if line:
                cleaned_lines.append(
                    (line_number, line)
                )

        return cleaned_lines

    def _split_instruction(
        self,
        line: str,
        line_number: int,
    ) -> tuple[str, str]:
        """Split a line into prefix and payload."""
        if ":" not in line:
            raise MapParseError(
                line_number,
                "Instruction must contain ':'.",
            )

        prefix, payload = line.split(":", 1)

        prefix = prefix.strip()
        payload = payload.strip()

        if not prefix:
            raise MapParseError(
                line_number,
                "Instruction prefix cannot be empty.",
            )

        if not payload:
            raise MapParseError(
                line_number,
                f"Instruction '{prefix}' has no value.",
            )

        return prefix, payload

    def _parse_drone_count(
        self,
        line: str,
        line_number: int,
    ) -> int:
        """Parse the first nb_drones instruction."""
        prefix, payload = self._split_instruction(
            line,
            line_number,
        )

        if prefix != "nb_drones":
            raise MapParseError(
                line_number,
                "The first instruction must be nb_drones.",
            )

        try:
            drone_count = int(payload)

        except ValueError as error:
            raise MapParseError(
                line_number,
                "Drone count must be an integer.",
            ) from error

        if drone_count <= 0:
            raise MapParseError(
                line_number,
                "Drone count must be positive.",
            )

        return drone_count

    def _parse_zone(
        self,
        prefix: str,
        payload: str,
        line_number: int,
        zones: dict[str, Zone],
    ) -> Zone:
        """Parse and create a zone."""
        zone_data, metadata = (
            self._split_payload_and_metadata(
                payload,
                line_number,
            )
        )

        parts = zone_data.split()

        if len(parts) != 3:
            raise MapParseError(
                line_number,
                "Zone definition must contain "
                "a name, x coordinate and y coordinate.",
            )

        name, raw_x, raw_y = parts

        self._validate_zone_name(
            name,
            line_number,
        )

        if name in zones:
            raise MapParseError(
                line_number,
                f"Duplicate zone name '{name}'.",
            )

        try:
            x = int(raw_x)
            y = int(raw_y)

        except ValueError as error:
            raise MapParseError(
                line_number,
                "Zone coordinates must be integers.",
            ) from error

        self._validate_metadata_keys(
            metadata,
            self._ZONE_METADATA_KEYS,
            line_number,
            "zone",
        )

        raw_zone_type = metadata.get(
            "zone",
            ZoneType.NORMAL.value,
        )

        try:
            zone_type = ZoneType(raw_zone_type)

        except ValueError as error:
            raise MapParseError(
                line_number,
                f"Invalid zone type '{raw_zone_type}'.",
            ) from error

        color = metadata.get("color")

        if prefix in {"start_hub", "end_hub"}:
            max_drones = 1
        else:
            max_drones = self._parse_positive_capacity(
                metadata.get("max_drones", "1"),
                "max_drones",
                line_number,
            )

        zone = Zone(
            name=name,
            x=x,
            y=y,
            zone_type=zone_type,
            color=color,
            max_drones=max_drones,
        )

        zones[name] = zone

        return zone

    def _parse_connection(
        self,
        payload: str,
        line_number: int,
        zones: dict[str, Zone],
        connection_keys: set[tuple[str, str]],
    ) -> Connection:
        """Parse and create a bidirectional connection."""
        connection_data, metadata = (
            self._split_payload_and_metadata(
                payload,
                line_number,
            )
        )

        if connection_data.count("-") != 1:
            raise MapParseError(
                line_number,
                "Connection must use the format "
                "'zone1-zone2'.",
            )

        zone_a_name, zone_b_name = (
            connection_data.split("-", 1)
        )

        if not zone_a_name or not zone_b_name:
            raise MapParseError(
                line_number,
                "Connection zone names cannot be empty.",
            )

        if (
            zone_a_name not in zones
            or zone_b_name not in zones
        ):
            raise MapParseError(
                line_number,
                "Connections may reference only "
                "previously defined zones.",
            )

        first_zone_name, second_zone_name = sorted(
            (zone_a_name, zone_b_name)
        )
        connection_key = (first_zone_name, second_zone_name)

        if connection_key in connection_keys:
            raise MapParseError(
                line_number,
                f"Duplicate connection "
                f"'{zone_a_name}-{zone_b_name}'.",
            )

        self._validate_metadata_keys(
            metadata,
            self._CONNECTION_METADATA_KEYS,
            line_number,
            "connection",
        )

        max_capacity = self._parse_positive_capacity(
            metadata.get("max_link_capacity", "1"),
            "max_link_capacity",
            line_number,
        )

        connection_keys.add(connection_key)

        return Connection(
            zone_a=zones[zone_a_name],
            zone_b=zones[zone_b_name],
            max_capacity=max_capacity,
        )

    def _split_payload_and_metadata(
        self,
        payload: str,
        line_number: int,
    ) -> tuple[str, dict[str, str]]:
        """Separate instruction data from metadata."""
        if "[" not in payload and "]" not in payload:
            return payload.strip(), {}

        if (
            payload.count("[") != 1
            or payload.count("]") != 1
            or not payload.endswith("]")
        ):
            raise MapParseError(
                line_number,
                "Invalid metadata block syntax.",
            )

        data, raw_metadata_content = payload.split(
            "[",
            1,
        )

        raw_metadata = f"[{raw_metadata_content}"

        try:
            metadata = self._metadata_parser.parse(
                raw_metadata
            )

        except ValueError as error:
            raise MapParseError(
                line_number,
                str(error),
            ) from error

        if not data.strip():
            raise MapParseError(
                line_number,
                "Instruction data cannot be empty.",
            )

        return data.strip(), metadata

    def _validate_zone_name(
        self,
        name: str,
        line_number: int,
    ) -> None:
        """Validate a zone name."""
        if "-" in name:
            raise MapParseError(
                line_number,
                "Zone names cannot contain dashes.",
            )

        if any(character.isspace() for character in name):
            raise MapParseError(
                line_number,
                "Zone names cannot contain spaces.",
            )

    def _validate_metadata_keys(
        self,
        metadata: dict[str, str],
        allowed_keys: set[str],
        line_number: int,
        element_type: str,
    ) -> None:
        """Reject metadata keys not allowed for a line."""
        unknown_keys = set(metadata) - allowed_keys

        if unknown_keys:
            unknown_key = sorted(unknown_keys)[0]

            raise MapParseError(
                line_number,
                f"Unknown {element_type} metadata "
                f"key '{unknown_key}'.",
            )

    def _parse_positive_capacity(
        self,
        raw_value: str,
        field_name: str,
        line_number: int,
    ) -> int:
        """Parse a positive integer capacity."""
        try:
            value = int(raw_value)

        except ValueError as error:
            raise MapParseError(
                line_number,
                f"{field_name} must be an integer.",
            ) from error

        if value <= 0:
            raise MapParseError(
                line_number,
                f"{field_name} must be positive.",
            )

        return value
