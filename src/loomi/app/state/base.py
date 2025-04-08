from __future__ import annotations

from loomi.app.base import App
from loomi.app.services import ServiceDescriptor

from .exceptions import StateError

__all__ = [
    "AppCommonState",
]


class AppCommonState(App):
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
