from typing import Any

from _typeshed import Incomplete

from loomi.service.exceptions import ServiceError

__all__ = ["DependencyError"]

class DependencyError(ServiceError):
    dependency_type: Incomplete
    context: Incomplete
    def __init__(
        self, message: str, dependency_type: type | None = None, **context: Any
    ) -> None: ...
