from __future__ import annotations

from loomi.descriptors.use_service import ServiceDescriptor

from .base import AppABC, AsyncAppABC, SyncAppABC
from .exceptions import StateError
from .types import ExecutorProtocolT, StateProtocolT

__all__ = [
    "CommonAppStateHandler",
    "AsyncCommonAppStateHandler",
    "SyncCommonAppStateHandler",
]


class CommonAppStateHandler(AppABC[StateProtocolT, ExecutorProtocolT]):
    """
    Base class for app state management.
    """

    def _initialize_state_descriptor(self) -> None:
        """Initialize state descriptor."""

        state_configured = False
        for name, value in self.__class__.__dict__.items():
            if not isinstance(value, ServiceDescriptor):
                continue

            if value.as_state is not True:
                continue

            if state_configured is True:
                raise StateError("Multiple state descriptors not supported")

            self._state_service_name = name
            state_configured = True


class AsyncCommonAppStateHandler(
    CommonAppStateHandler[StateProtocolT, ExecutorProtocolT], AsyncAppABC
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

    @property
    def state(self) -> StateProtocolT:
        """Check and return app's state service."""
        if not self._state_service_name or len(self._state_service_name) == 0:
            raise StateError("No state adapter configured")

        state = getattr(self, self._state_service_name, None)
        if not state:
            raise StateError("State adapter not initialized")

        return state

    @property
    def s(self) -> StateProtocolT:
        """Short alias for state adapter."""
        return self.state


class SyncCommonAppStateHandler(
    CommonAppStateHandler[StateProtocolT, ExecutorProtocolT], SyncAppABC
):
    @property
    def state(self) -> StateProtocolT:
        """Check and return app's state service."""
        if not self._state_service_name or len(self._state_service_name) == 0:
            raise StateError("No state adapter configured")

        state = getattr(self, self._state_service_name, None)
        if not state:
            raise StateError("State adapter not initialized")

        return state

    @property
    def s(self) -> StateProtocolT:
        """Short alias for state adapter."""
        return self.state
