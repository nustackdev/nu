from __future__ import annotations

__all__ = [
    "FleetError",
]


class FleetError(Exception):
    """
    Base exception for fleet errors.

    This is the root exception class for all fleet-related errors.
    All other fleet exceptions should inherit from this class.
    """

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        """
        Initialize the fleet error.

        Args:
            message: Human-readable error message
            cause: Optional underlying exception that caused this error
        """
        super().__init__(message)
        self.cause = cause

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.cause:
            return f"{super().__str__()} (caused by: {self.cause})"
        return super().__str__()
