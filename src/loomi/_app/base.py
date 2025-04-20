"""
Base app functionality shared between async and sync app types.

The functionality here is inherited by both async and sync service base classes
to ensure consistent behavior across all service types.
"""

from __future__ import annotations

from abc import ABC
from types import TracebackType
from typing import TYPE_CHECKING, Generic, Self

from .logger import logger
from .types import ExecutorT, StateT, SyncExecutorT, SyncStateT

if TYPE_CHECKING:
    from loomi._service import Service

__all____ = [
    "AppABC",
    "SyncAppABC",
    "AsyncAppABC",
]


class AppABC(ABC, Generic[StateT, ExecutorT]):
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
    _exec_engine_service_name: str

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
        """
        self._services = {}
        self._app_deps = {}
        self._state_service_name = ""
        self._exec_engine_service_name = ""
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


class SyncAppABC(AppABC[SyncStateT, SyncExecutorT]):
    """
    Base class for synchronous app functionality.
    """

    """
    Synchronous app initializer protocol.

    This protocol defines the interface for app initialization.
    """

    def initialize(self) -> None:
        """
        Initialize app and its dependencies synchronously.
        """
        ...

    def shutdown(self) -> None:
        """
        Shutdown app and cleanup dependencies synchronously.
        """
        ...

    def __enter__(self) -> Self:
        """
        Enter context, initializing app.

        Returns:
            Self for context usage
        """
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context, shutting down app."""
        ...

    """

    This protocol defines the interface for services initialization.
    """

    def initialize_services(self) -> None:
        """
        Initialize app service dependencies synchronously.
        """
        ...

    def shutdown_services(self) -> None:
        """
        Shutdown app service dependencies synchronously.
        """
        ...

    def _initialize_service_descriptors(self) -> None:
        """Initialize service descriptors."""
        ...

    """Protocol defining synchronous service state management."""

    @property
    def state(self) -> SyncStateT:
        """Check and return app's state service."""
        ...

    @property
    def s(self) -> SyncStateT:
        """Short alias for state adapter."""
        ...

    def _initialize_state_descriptor(self) -> None:
        """Initialize state descriptor."""
        ...

    """Protocol defining synchronous service operation capabilities."""

    def _initialize_engine_descriptor(self) -> None:
        """Initialize engine descriptor."""
        ...

    """Defining synchronous app composition capabilities."""

    def _initialize_app_composition_descriptors(self) -> None:
        """Initialize app composition descriptors."""
        ...

    def initialize_apps(self) -> None:
        """Initialize apps."""
        ...

    def shutdown_apps(self) -> None:
        """Shutdown app and cleanup."""
        ...


class AsyncAppABC(AppABC[StateT, ExecutorT]):
    """AsyncStateProtocol for asynchronous app functionality."""

    """
    Async app initializer protocol.

    This protocol defines the interface for apps initialization.
    """

    async def initialize(self) -> None:
        """
        Initialize app and its dependencies asynchronously.
        """
        ...

    async def shutdown(self) -> None:
        """
        Shutdown app and cleanup dependencies asynchronously.
        """
        ...

    async def __aenter__(self) -> Self:
        """
        Enter async context, initializing app.

        Returns:
            Self for context usage
        """
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context, shutting down app."""
        ...

    """
    Async app services handler protocol.

    This protocol defines the interface for services initialization.
    """

    async def initialize_services(self) -> None:
        """
        Initialize app service dependencies asynchronously.
        """
        ...

    async def shutdown_services(self) -> None:
        """
        Shutdown app service dependencies asynchronously.
        """
        ...

    def _initialize_service_descriptors(self) -> None:
        """Initialize service descriptors."""
        ...

    """Protocol defining asynchronous service state management."""

    @property
    def state(self) -> StateT:
        """Check and return app's state service."""
        ...

    @property
    def s(self) -> StateT:
        """Short alias for state adapter."""
        ...

    def _initialize_state_descriptor(self) -> None:
        """Initialize state descriptor."""
        ...

    """Protocol defining asynchronous service operation capabilities."""

    @property
    def engine(self) -> ExecutorT:
        """Check and return app's state service."""
        ...

    @property
    def e(self) -> ExecutorT:
        """Short alias for state adapter."""
        ...

    def _initialize_engine_descriptor(self) -> None:
        """Initialize engine descriptor."""
        ...

    """Defining asynchronous app composition capabilities."""

    def _initialize_app_composition_descriptors(self) -> None:
        """Initialize app composition descriptors."""
        ...

    async def initialize_apps(self) -> None:
        """Initialize apps."""
        ...

    async def shutdown_apps(self) -> None:
        """Shutdown app and cleanup."""
        ...
