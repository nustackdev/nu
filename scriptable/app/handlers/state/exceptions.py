from __future__ import annotations

from typing import Any

from scriptable.app.exceptions import AppError

__all__ = [
    "StateError",
]


class StateError(AppError):
    """
    Raised for state-related errors.

    Examples:
    - Invalid state access
    - State modification failure
    - State adapter errors
    """

    def __init__(self, message: str, key: tuple[str, ...] | None = None, **context: Any) -> None:
        self.key = key
        self.context = context
        super().__init__(message)
