from __future__ import annotations

from loomi.app.base import AsyncApp

from .base import AppCommonState
from .exceptions import StateError
from .protocols import AsyncStateProtocol

__all__ = [
    "AsyncAppState",
]


class AsyncAppState(AppCommonState, AsyncApp):
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
    def state(self) -> AsyncStateProtocol:
        """Check and return app's state service."""
        if not self._state_service_name or len(self._state_service_name) == 0:
            raise StateError("No state adapter configured")

        state = getattr(self, self._state_service_name, None)
        if not state:
            raise StateError("State adapter not initialized")

        return state

    @property
    def s(self) -> AsyncStateProtocol:
        """Short alias for state adapter."""
        return self.state
