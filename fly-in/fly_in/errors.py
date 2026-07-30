"""Custom exceptions used by the Fly-in project."""


class FlyInError(Exception):
    """Base exception for all project errors."""


class MapFileError(FlyInError):
    """Raised when a map file cannot be read."""


class MapParseError(FlyInError):
    """Raised when a map contains invalid syntax or data."""

    def __init__(
        self,
        line_number: int,
        message: str,
    ) -> None:
        self.line_number = line_number
        self.message = message

        super().__init__(
            f"Line {line_number}: {message}"
        )
