from __future__ import annotations

from scriptable.app.exceptions import AppError

__all__ = [
    "ExecutionError",
]


class ExecutionError(AppError):
    """
    Raised for execution-related errors.

    Examples:
    - Execution failure
    - Invalid execution type
    - Platform errors
    """

    pass
