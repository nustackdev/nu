from __future__ import annotations

from typing import Any

from loomi.app.base import SyncApp

from .base import AppCommonState
from .exceptions import StateError

__all__ = [
    "SyncAppState",
]


class SyncAppState(AppCommonState, SyncApp):
    @property
    def state(self) -> Any:
        """Check and return app's state service."""
        if not self._state_service_name or len(self._state_service_name) == 0:
            raise StateError("No state adapter configured")

        state = getattr(self, self._state_service_name, None)
        if not state:
            raise StateError("State adapter not initialized")

        return state

    @property
    def s(self) -> Any:
        """Short alias for state adapter."""
        return self.state
