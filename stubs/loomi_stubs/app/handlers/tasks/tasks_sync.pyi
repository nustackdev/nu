import abc
from typing import Any, Callable

from loomi.app.base import SyncApp

from .base import AppCommonTasks
from .protocols import SyncOperationProtocol

__all__ = ["SyncAppTasks"]

class SyncAppTasks(AppCommonTasks, SyncApp, metaclass=abc.ABCMeta):
    async def execute(self, operation: SyncOperationProtocol) -> Any: ...
    def function(self, func: Callable, *, name: str | None = None) -> SyncOperationProtocol: ...
    def sequence(
        self, *operations: SyncOperationProtocol, delay: float = 0, continue_on_error: bool = False
    ) -> SyncOperationProtocol: ...
