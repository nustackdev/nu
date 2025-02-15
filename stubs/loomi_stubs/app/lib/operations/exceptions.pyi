from typing import Any

from _typeshed import Incomplete

from loomi.app.exceptions import AppError as AppError

class OperationError(AppError):
    operation_id: Incomplete
    context: Incomplete
    def __init__(self, message: str, operation_id: str | None = None, **context: Any) -> None: ...
