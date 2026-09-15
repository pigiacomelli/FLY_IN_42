"""Metadata-block parsing for Fly-in map lines."""


class MetadataParser:
    """Parse metadata blocks from map lines."""

    def parse(self, raw_metadata: str) -> dict[str, str]:
        """Convert a metadata block into key-value pairs."""
        raw_metadata = raw_metadata.strip()

        if not raw_metadata:
            return {}

        if (
            not raw_metadata.startswith("[")
            or not raw_metadata.endswith("]")
        ):
            raise ValueError(
                "Metadata block must start with '[' and end with ']'."
            )

        content = raw_metadata[1:-1].strip()

        if not content:
            return {}

        elements = content.split()
        metadata: dict[str, str] = {}

        for element in elements:
            if element.count("=") != 1:
                raise ValueError(
                    f"Metadata element '{element}' must contain "
                    "exactly one '='."
                )

            key, value = element.split("=", 1)

            if not key:
                raise ValueError("Metadata key cannot be empty.")

            if not value:
                raise ValueError(
                    f"Metadata value for key '{key}' cannot be empty."
                )

            if key in metadata:
                raise ValueError(
                    f"Duplicate metadata key: '{key}'."
                )

            metadata[key] = value

        return metadata
