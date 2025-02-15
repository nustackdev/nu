from typing import Any

from _typeshed import Incomplete

from loomi.app.exceptions import AppError

__all__ = ["StateError"]

class StateError(AppError):
    key: Incomplete
    context: Incomplete
    def __init__(
        self, message: str, key: tuple[str, ...] | None = None, **context: Any
    ) -> None: ...
