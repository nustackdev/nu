from typing import Any

from scriptable.app.exceptions import AppError


class OperationError(AppError):
    """
    Raised for operation-related errors.

    Examples:
    - Operation execution failure
    - Invalid operation type
    - Platform errors
    """

    def __init__(self, message: str, operation_id: str | None = None, **context: Any) -> None:
        self.operation_id = operation_id
        self.context = context
        super().__init__(message)
