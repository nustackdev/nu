from __future__ import annotations

import inspect
from typing import cast, final

from loomi.interfaces.executor.context import ContextProtocol
from loomi.interfaces.executor.executor import SyncExecutorProtocol
from loomi.interfaces.executor.operations import OperationProtocol

from .base import AppABC, AsyncAppABC, SyncAppABC
from .exceptions import ExecutionError
from .types import ExecutorT, StateT, SyncExecutorT, SyncStateT


class CommonAppExecutionHandler(AppABC[StateT, ExecutorT]):
    """
    Base class for app tasks execution.
    """


class AsyncAppExecutionHandler(
    CommonAppExecutionHandler[StateT, ExecutorT], AsyncAppABC[StateT, ExecutorT]
):
    """
    App feature implementing async execution engine management.
    """

    @final
    @property
    def executor(self) -> ExecutorT:
        """Check and return app's state service."""
        if "EXECUTOR" not in self._get_dependencies():
            raise ExecutionError("No execution engine adapter configured")

        executor = cast(ExecutorT, self._get_dependency("EXECUTOR"))

        if not executor:
            raise ExecutionError("Execution engine not initialized")

        return executor

    @final
    @property
    def ex(self) -> ExecutorT:
        """Short alias for state adapter."""
        return self.executor

    async def start(self, context: ContextProtocol | None = None) -> None:
        """Run the app."""
        operation_def_fn = getattr(self, "define", None)
        if not operation_def_fn:
            raise ExecutionError("No operation defined")

        operation = None
        if inspect.iscoroutinefunction(operation_def_fn):
            operation = await operation_def_fn()
        elif inspect.ismethod(operation_def_fn):
            operation = operation_def_fn()
        else:
            raise ExecutionError("Operation definition is not a function")

        if inspect.iscoroutinefunction(self.executor.execute):
            await self.executor.execute(operation, context)
        else:
            self.executor.execute(operation, context)

    def define(self) -> OperationProtocol:
        """Define the operation to execute."""
        raise NotImplementedError("Subclasses must implement this method")


class SyncAppExecutionHandler(
    CommonAppExecutionHandler[SyncStateT, SyncExecutorT], SyncAppABC[SyncStateT, SyncExecutorT]
):
    """
    App feature implementing execution engine management.
    """

    @final
    @property
    def executor(self) -> SyncExecutorT:
        """Check and return app's state service."""
        if "EXECUTOR" not in self._get_dependencies():
            raise ExecutionError("No execution engine adapter configured")

        executor = cast(SyncExecutorT, self._get_dependency("EXECUTOR"))

        if not executor:
            raise ExecutionError("Execution engine not initialized")

        return executor

    @final
    @property
    def ex(self) -> SyncExecutorT:
        """Short alias for state adapter."""
        return self.executor

    def start(self, context: ContextProtocol | None = None) -> None:
        """Run the app."""
        operation_def_fn = getattr(self, "define", None)
        if not operation_def_fn:
            raise ExecutionError("No operation defined")

        operation = None
        if inspect.iscoroutinefunction(operation_def_fn):
            raise ExecutionError("Async operation definition not supported")
        elif inspect.ismethod(operation_def_fn):
            operation = operation_def_fn()
        else:
            raise ExecutionError("Operation definition is not a function")

        if inspect.iscoroutinefunction(self.executor.execute):
            raise ExecutionError("Async execution engine not supported")
        elif isinstance(self.executor, SyncExecutorProtocol):
            self.executor.execute(operation, context)

    def define(self) -> OperationProtocol:
        """Define the operation to execute."""
        raise NotImplementedError("Subclasses must implement this method")
