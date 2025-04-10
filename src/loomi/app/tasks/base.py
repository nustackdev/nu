from __future__ import annotations

from loomi.app.base import App
from loomi.app.services import ServiceDescriptor

from .exceptions import ExecutionError

__all__ = [
    "AppCommonTasks",
]


class AppCommonTasks(App):
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
