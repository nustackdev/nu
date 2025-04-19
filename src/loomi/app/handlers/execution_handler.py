from __future__ import annotations

import inspect
from typing import cast

from loomi.descriptors.use_service import ServiceDescriptor
from loomi.interfaces.executor.context import ContextProtocol
from loomi.interfaces.executor.executor import AsyncExecutorProtocol, SyncExecutorProtocol

from ..base import AppABC, AsyncAppABC, SyncAppABC
from ..exceptions import ExecutionError
from ..types import ExecutorT, StateT, SyncExecutorT, SyncStateT


class CommonAppExecutionHandler(AppABC[StateT, ExecutorT]):
    """
    Base class for app tasks execution.
    """

    def _initialize_engine_descriptor(self) -> None:
        """Initialize engine descriptor."""

        engine_configured = False
        for name, value in self.__class__.__dict__.items():
            if not isinstance(value, ServiceDescriptor):
                continue

            if value.as_engine is not True:
                continue

            if engine_configured is True:
                raise ExecutionError("Multiple engine descriptors not supported")

            self._exec_engine_service_name = name
            engine_configured = True


class AsyncAppExecutionHandler(
    CommonAppExecutionHandler[StateT, ExecutorT], AsyncAppABC[StateT, ExecutorT]
):
    """
    App feature implementing async execution engine management.
    """

    @property
    def executor(self) -> ExecutorT:
        """Check and return app's state service."""
        if not self._exec_engine_service_name or len(self._exec_engine_service_name) == 0:
            raise ExecutionError("No execution engine adapter configured")

        executor = cast(ExecutorT, getattr(self, self._exec_engine_service_name, None))

        if not executor:
            raise ExecutionError("Execution engine not initialized")

        return executor

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
            operation = await operation_def_fn(context)
        elif inspect.isfunction(operation_def_fn):
            operation = operation_def_fn(context)
        else:
            raise ExecutionError("Operation definition is not a function")

        if isinstance(self.executor, AsyncExecutorProtocol):
            await self.executor.execute(operation, context)
        elif isinstance(self.executor, SyncExecutorProtocol):
            self.executor.execute(operation, context)


class SyncAppExecutionHandler(
    CommonAppExecutionHandler[SyncStateT, SyncExecutorT], SyncAppABC[SyncStateT, SyncExecutorT]
):
    """
    App feature implementing execution engine management.
    """

    @property
    def executor(self) -> SyncExecutorT:
        """Check and return app's state service."""
        if not self._exec_engine_service_name or len(self._exec_engine_service_name) == 0:
            raise ExecutionError("No execution engine adapter configured")

        engine = cast(SyncExecutorT, getattr(self, self._exec_engine_service_name, None))
        if not engine:
            raise ExecutionError("Execution engine not initialized")

        return engine

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
        elif inspect.isfunction(operation_def_fn):
            operation = operation_def_fn(context)
        else:
            raise ExecutionError("Operation definition is not a function")

        if isinstance(self.executor, AsyncExecutorProtocol):
            raise ExecutionError("Async execution engine not supported")
        elif isinstance(self.executor, SyncExecutorProtocol):
            self.executor.execute(operation, context)
