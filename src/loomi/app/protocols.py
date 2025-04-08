from __future__ import annotations

from abc import ABC
from types import TracebackType
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from .state import AsyncStateProtocol, SyncStateProtocol

__all__ = [
    "CommonAppProtocol",
    "SyncAppInitializerProtocol",
    "AsyncAppInitializerProtocol",
    "AsyncAppServicesProtocol",
    "SyncAppServicesProtocol",
    "AsyncAppStateProtocol",
    "SyncAppStateProtocol",
    "AsyncAppTasksProtocol",
    "SyncAppTasksProtocol",
    "AsyncAppModelProtocol",
    "SyncAppModelProtocol",
    "AppProtocol",
    "SyncAppProtocol",
    "AsyncAppProtocol",
]


class CommonAppProtocol(ABC):
    """Base protocol for common application functionality."""

    pass


class SyncAppInitializerProtocol(ABC):
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


class AsyncAppInitializerProtocol(ABC):
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


class AsyncAppServicesProtocol(ABC):
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


class SyncAppServicesProtocol(ABC):
    """
    Sync app services handler protocol.

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


class SyncAppStateProtocol(ABC):
    """Protocol defining synchronous service state management."""

    @property
    def state(self) -> "SyncStateProtocol":
        """Check and return app's state service."""
        ...

    @property
    def s(self) -> "SyncStateProtocol":
        """Short alias for state adapter."""
        ...

    def _initialize_state_descriptor(self) -> None:
        """Initialize state descriptor."""
        ...


class AsyncAppStateProtocol(ABC):
    """Protocol defining asynchronous service state management."""

    @property
    def state(self) -> "AsyncStateProtocol":
        """Check and return app's state service."""
        ...

    @property
    def s(self) -> "AsyncStateProtocol":
        """Short alias for state adapter."""
        ...

    def _initialize_state_descriptor(self) -> None:
        """Initialize state descriptor."""
        ...


class SyncAppTasksProtocol(ABC):
    """Protocol defining synchronous service operation capabilities."""

    ...


class AsyncAppTasksProtocol(ABC):
    """Protocol defining asynchronous service operation capabilities."""

    ...


class SyncAppModelProtocol(ABC):
    def _initialize_model_descriptors(self) -> None:
        """Initialize model."""
        ...


class AsyncAppModelProtocol(ABC):
    def _initialize_model_descriptors(self) -> None:
        """Initialize model."""
        ...


class SyncAppCompositionProtocol(ABC):
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


class AsyncAppCompositionProtocol(ABC):
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


class AppProtocol(
    CommonAppProtocol,
):
    """Common application protocol."""

    pass


class SyncAppProtocol(
    AppProtocol,
    SyncAppInitializerProtocol,
    SyncAppServicesProtocol,
    SyncAppStateProtocol,
    SyncAppTasksProtocol,
    SyncAppModelProtocol,
    SyncAppCompositionProtocol,
):
    """Synchronous application protocol."""

    pass


class AsyncAppProtocol(
    AppProtocol,
    AsyncAppInitializerProtocol,
    AsyncAppServicesProtocol,
    AsyncAppStateProtocol,
    AsyncAppTasksProtocol,
    AsyncAppModelProtocol,
    AsyncAppCompositionProtocol,
):
    """Asynchronous application protocol."""

    pass
