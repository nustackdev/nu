"""
Base app functionality shared between async and sync app types.

The functionality here is inherited by both async and sync service base classes
to ensure consistent behavior across all service types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .logger import logger

if TYPE_CHECKING:
    from loomi.service import Service

__all__ = [
    "AppCommon",
]


class AppCommon:
    """
    Base class providing common functionality for all app types.

    This class implements the core features needed by all apps. It handles
    service management, identity management, and basic app properties.

    Class Attributes:
        _services (dict[str, Service]): Dictionary of services used by the app
        _state_service_name (str): Name of the state service

    Properties:
        key (str): Unique app instance identifier
        readable_name (str): Human-readable app identifier
    """

    _services: dict[str, "Service"]
    _state_service_name: str

    @classmethod
    def factory_name(cls) -> str:
        """
        Get the fully qualified name of the app class.

        Returns:
            str: String in format "module.ClassName"
        """
        return f"{cls.__module__}.{cls.__name__}"

    def __init__(self) -> None:
        """
        Initialize a new app instance.

        Args:
            services: Dictionary of services used by the app. If None, an empty dictionary will be created.
            state_service_name: Name of the state service.

        Notes:
            - Initializes services dictionary and state service name
            - Logs initialization details at appropriate levels
        """
        self._services = {}
        self._state_service_name = ""
        logger.debug(f"Initialized app '{self.readable_name}'")

    @property
    def key(self) -> str:
        """
        Get the unique app instance identifier.

        Returns:
            str: Unique key generated from the factory name
        """
        return self.factory_name()

    @property
    def readable_name(self) -> str:
        """
        Get a human-readable identifier for the app.

        Returns:
            str: String combining class name
        """
        return f"{self.__class__.__name__}"

    def __repr__(self) -> str:
        """
        Generate string representation of the app.

        Returns:
            str: Human-readable string showing app name and services
        """
        return f"<App '{self.readable_name}': services=({self._services})>"
