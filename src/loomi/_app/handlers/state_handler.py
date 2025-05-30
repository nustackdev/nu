from __future__ import annotations

from typing import final

from ..base import AppABC, AsyncAppABC, SyncAppABC
from ..exceptions import StateError
from ..types import ExecutorT, StateT, SyncExecutorT, SyncStateT

__all__ = [
    "CommonAppStateHandler",
    "AsyncCommonAppStateHandler",
    "SyncCommonAppStateHandler",
]


class CommonAppStateHandler(AppABC[StateT, ExecutorT]):
    """
    Base class for app state management.
    """

    pass


class AsyncCommonAppStateHandler(
    CommonAppStateHandler[StateT, ExecutorT], AsyncAppABC[StateT, ExecutorT]
):
    """
    App feature implementing state management.

    Features:
    - State adapter handling
    - State management methods
    - State subscription management
    - State transaction management

    Example:
        class DataApp(AsyncApp):
            ...

            def exec_data_process(self, key: str) -> Any:
                await self.set(("status",), "processing")
                result = self.process_data(key)
                await self.set(("status,), "done")
    """

    @final
    @property
    def state(self) -> StateT:
        """Check and return app's state service."""
        if "EXECUTOR" not in self._services:
            raise StateError("No state adapter configured")

        state = self.get_service_dependency("STATE")

        if not state:
            raise StateError("State not initialized")

        return getattr(state, "state")

    @final
    @property
    def s(self) -> StateT:
        """Short alias for state adapter."""
        return self.state


class SyncCommonAppStateHandler(
    CommonAppStateHandler[SyncStateT, SyncExecutorT], SyncAppABC[SyncStateT, SyncExecutorT]
):
    @final
    @property
    def state(self) -> SyncStateT:
        """Check and return app's state service."""
        if "EXECUTOR" not in self._services:
            raise StateError("No state adapter configured")

        state = self.get_service_dependency("STATE")

        if not state:
            raise StateError("State not initialized")

        return getattr(state, "state")

    @final
    @property
    def s(self) -> SyncStateT:
        """Short alias for state adapter."""
        return self.state
