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
        """Create a parsing error carrying source-line context."""
        self.line_number = line_number
        self.message = message
        super().__init__(f"Line {line_number}: {message}")


class MapValidationError(FlyInError):
    """Raised when a parsed map is semantically invalid."""


class PathNotFoundError(FlyInError):
    """Raised when no accessible path exists between two zones."""


class MovementValidationError(FlyInError):
    """Raised when a movement is invalid for the current turn."""


class RoutePlanningError(FlyInError):
    """Raised when valid routes cannot be assigned to all drones."""


class SimulationDeadlockError(FlyInError):
    """Raised when unfinished drones cannot make further progress."""


class SimulationLimitError(FlyInError):
    """Raised when a simulation exceeds its configured turn limit."""
