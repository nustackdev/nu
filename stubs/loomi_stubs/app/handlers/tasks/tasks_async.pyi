import abc
from typing import Any, Callable

from loomi.app.base import AsyncApp

from .base import AppCommonTasks
from .protocols import AsyncOperationProtocol

__all__ = ["AsyncAppTasks"]

class AsyncAppTasks(AppCommonTasks, AsyncApp, metaclass=abc.ABCMeta):
    async def execute(self, operation: AsyncOperationProtocol) -> Any: ...
    def function(self, func: Callable, *, name: str | None = None) -> AsyncOperationProtocol: ...
    def sequence(
        self, *operations: AsyncOperationProtocol, delay: float = 0, continue_on_error: bool = False
    ) -> AsyncOperationProtocol: ...
    def repeat(
        self,
        operation: AsyncOperationProtocol,
        times: int | None = None,
        while_key: str | tuple[str, ...] | None = None,
        max_iterations: int | None = None,
        delay: float = 0,
        ignore_errors: bool = False,
    ) -> AsyncOperationProtocol: ...
    def parallel(
        self,
        *operations: AsyncOperationProtocol,
        max_concurrent: int | None = None,
        timeout: float | None = None,
        ignore_errors: bool = False,
    ) -> AsyncOperationProtocol: ...
