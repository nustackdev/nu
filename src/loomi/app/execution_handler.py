from __future__ import annotations

from typing import cast

from loomi.descriptors.use_service import ServiceDescriptor
from loomi.interfaces.executor.protocols import ContextProtocol

from .base import AppABC, AsyncAppABC, SyncAppABC
from .exceptions import ExecutionError
from .types import ExecutorProtocolT, StateProtocolT

__all__ = [
    "CommonAppExecutionHandler",
    "AsyncAppExecutionHandler",
    "SyncAppExecutionHandler",
]


class CommonAppExecutionHandler(AppABC[StateProtocolT, ExecutorProtocolT]):
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
    CommonAppExecutionHandler[StateProtocolT, ExecutorProtocolT], AsyncAppABC
):
    """
    App feature implementing async execution engine management.
    """

    @property
    def engine(self) -> ExecutorProtocolT:
        """Check and return app's state service."""
        if not self._exec_engine_service_name or len(self._exec_engine_service_name) == 0:
            raise ExecutionError("No execution engine adapter configured")

        engine = cast(ExecutorProtocolT, getattr(self, self._exec_engine_service_name, None))
        engine.state = self.state
        if not engine:
            raise ExecutionError("Execution engine not initialized")

        return engine

    @property
    def e(self) -> ExecutorProtocolT:
        """Short alias for state adapter."""
        return self.engine

    async def start(self, context: ContextProtocol | None = None) -> None:
        """Run the app."""
        await self.e.execute(await self.run(), context)

    async def run(self) -> ExecutorProtocolT:
        """Run the app."""
        ...


class SyncAppExecutionHandler(
    CommonAppExecutionHandler[StateProtocolT, ExecutorProtocolT], SyncAppABC
):
    """
    App feature implementing execution engine management.
    """

    @property
    def engine(self) -> ExecutorProtocolT:
        """Check and return app's state service."""
        if not self._exec_engine_service_name or len(self._exec_engine_service_name) == 0:
            raise ExecutionError("No execution engine adapter configured")

        engine = cast(ExecutorProtocolT, getattr(self, self._exec_engine_service_name, None))
        engine.state = self.state
        if not engine:
            raise ExecutionError("Execution engine not initialized")

        return engine

    @property
    def e(self) -> ExecutorProtocolT:
        """Short alias for state adapter."""
        return self.engine

    def start(self, context: ContextProtocol | None = None) -> None:
        """Run the app."""
        # TODO: implement sync execution
        ...

    def run(self) -> ExecutorProtocolT:
        """Run the app."""
        ...
