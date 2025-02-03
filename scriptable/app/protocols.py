"""State and task management protocol definitions."""

from __future__ import annotations

from abc import abstractmethod
from types import TracebackType
from typing import AsyncIterator, Callable, Iterator, Protocol, Self, runtime_checkable

from .exceptions import HandlerNotImplemented
from .handlers.state.protocols import (
    StateAsyncProtocol,
    StateSyncProtocol,
    SubscriptionAsyncProtocol,
    SubscriptionSyncProtocol,
    TransactionAsyncProtocol,
    TransactionContextManagerAsyncProtocol,
    TransactionContextManagerSyncProtocol,
    TransactionSyncProtocol,
)
from .handlers.state.types import StateAsyncCallbackFn, StateKey, StateSyncCallbackFn, StateValue
from .handlers.tasks.protocols import OperationAsyncProtocol, OperationSyncProtocol


class AppCommonBaseProtocol(Protocol):
    """Base protocol for common application functionality."""

    pass


@runtime_checkable
class AppInitializerSyncProtocol(Protocol):
    """
    Synchronous app initializer protocol.

    This protocol defines the interface for app initialization.
    """

    def initialize(self) -> None:
        """
        Initialize app and its dependencies synchronously.
        """
        raise HandlerNotImplemented

    def shutdown(self) -> None:
        """
        Shutdown app and cleanup dependencies synchronously.
        """
        raise HandlerNotImplemented

    def __enter__(self) -> Self:
        """
        Enter context, initializing app.

        Returns:
            Self for context usage
        """
        raise HandlerNotImplemented

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context, shutting down app."""
        raise HandlerNotImplemented


@runtime_checkable
class AppInitializerAsyncProtocol(Protocol):
    """
    Async app initializer protocol.

    This protocol defines the interface for apps initialization.
    """

    async def initialize(self) -> None:
        """
        Initialize app and its dependencies asynchronously.
        """
        raise HandlerNotImplemented

    async def shutdown(self) -> None:
        """
        Shutdown app and cleanup dependencies asynchronously.
        """
        raise HandlerNotImplemented

    async def __aenter__(self) -> Self:
        """
        Enter async context, initializing app.

        Returns:
            Self for context usage
        """
        raise HandlerNotImplemented

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context, shutting down app."""
        raise HandlerNotImplemented


@runtime_checkable
class AppServicesAsyncProtocol(Protocol):
    """
    Async app services handler protocol.

    This protocol defines the interface for services initialization.
    """

    async def initialize_services(self) -> None:
        """
        Initialize app service dependencies asynchronously.
        """
        raise HandlerNotImplemented

    async def shutdown_services(self) -> None:
        """
        Shutdown app service dependencies asynchronously.
        """
        raise HandlerNotImplemented


@runtime_checkable
class AppServicesSyncProtocol(Protocol):
    """
    Sync app services handler protocol.

    This protocol defines the interface for services initialization.
    """

    def initialize_services(self) -> None:
        """
        Initialize app service dependencies synchronously.
        """
        raise HandlerNotImplemented

    def shutdown_services(self) -> None:
        """
        Shutdown app service dependencies synchronously.
        """
        raise HandlerNotImplemented


@runtime_checkable
class AppStateSyncProtocol(Protocol):
    """Protocol defining synchronous service state management."""

    @property
    def state(self) -> StateSyncProtocol:
        """Check and return app's state service."""
        raise HandlerNotImplemented

    @property
    def s(self) -> StateSyncProtocol:
        """Short alias for state adapter."""
        raise HandlerNotImplemented

    @abstractmethod
    def get(self, key: StateKey) -> StateValue:
        """
        Get state value at path.

        Args:
            key: State path components

        Returns:
            State value if exists, None otherwise

        Raises:
            StateError: If state access fails
        """
        raise HandlerNotImplemented

    @abstractmethod
    def set(self, key: StateKey, value: StateValue) -> None:
        """
        Set state value at path.

        Args:
            key: State path components
            value: Value to store

        Raises:
            StateError: If state update fails
        """
        raise HandlerNotImplemented

    @abstractmethod
    def delete(self, key: StateKey) -> None:
        """
        Delete state at path.

        Args:
            key: State path components

        Raises:
            StateError: If state deletion fails
        """
        raise HandlerNotImplemented

    @abstractmethod
    def exists(self, key: StateKey) -> bool:
        """
        Check if state exists at path.

        Args:
            key: State path components

        Returns:
            True if state exists, False otherwise

        Raises:
            StateError: If state check fails
        """
        raise HandlerNotImplemented

    @abstractmethod
    def list(self, *prefix: str) -> Iterator[StateKey]:
        """
        List all state keys under prefix.

        Args:
            *prefix: State path prefix components

        Returns:
            Iterator of matching state keys

        Raises:
            StateError: If state listing fails
        """
        raise HandlerNotImplemented

    @abstractmethod
    def subscribe(self, key: StateKey, callback: StateSyncCallbackFn) -> SubscriptionSyncProtocol:
        """
        Subscribe to changes under key prefix.

        Args:
            key: Key prefix to subscribe to
            callback: Callback function for notifications

        Returns:
            Subscription object for unsubscribing

        Raises:
            ObserverError: If subscription fails
        """
        raise HandlerNotImplemented

    @abstractmethod
    def unsubscribe(self, subscription: SubscriptionSyncProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        raise HandlerNotImplemented

    @abstractmethod
    def begin_transaction(self) -> TransactionSyncProtocol:
        """
        Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        raise HandlerNotImplemented

    @abstractmethod
    def transaction(self) -> TransactionContextManagerSyncProtocol:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager
        """
        raise HandlerNotImplemented


@runtime_checkable
class AppStateAsyncProtocol(Protocol):
    """Protocol defining asynchronous service state management."""

    @property
    def state(self) -> StateAsyncProtocol:
        """Check and return app's state service."""
        raise HandlerNotImplemented

    @property
    def s(self) -> StateAsyncProtocol:
        """Short alias for state adapter."""
        raise HandlerNotImplemented

    @abstractmethod
    async def get(self, key: StateKey) -> StateValue:
        """Get state value at path."""
        raise HandlerNotImplemented

    @abstractmethod
    async def set(self, key: StateKey, value: StateValue) -> None:
        """Set state value at path."""
        raise HandlerNotImplemented

    @abstractmethod
    async def delete(self, key: StateKey) -> None:
        """Delete state at path."""
        raise HandlerNotImplemented

    @abstractmethod
    async def exists(self, key: StateKey) -> bool:
        """Check if state exists at path."""
        raise HandlerNotImplemented

    @abstractmethod
    async def list(self, *prefix: str) -> AsyncIterator[StateKey]:
        """List all state keys under prefix."""
        raise HandlerNotImplemented

    @abstractmethod
    async def subscribe(
        self, key: StateKey, callback: StateAsyncCallbackFn
    ) -> SubscriptionAsyncProtocol:
        """Subscribe to changes under key prefix."""
        raise HandlerNotImplemented

    @abstractmethod
    async def unsubscribe(self, subscription: SubscriptionAsyncProtocol) -> None:
        """Unsubscribe from changes under key prefix."""
        raise HandlerNotImplemented

    @abstractmethod
    async def begin_transaction(self) -> TransactionAsyncProtocol:
        """Begin transaction."""
        raise HandlerNotImplemented

    @abstractmethod
    async def transaction(self) -> TransactionContextManagerAsyncProtocol:
        """Get transaction context manager."""
        raise HandlerNotImplemented


@runtime_checkable
class AppTasksSyncProtocol(Protocol):
    """Protocol defining synchronous service operation capabilities."""

    def execute(self, operation: OperationSyncProtocol) -> None:
        """Execute operation."""
        raise HandlerNotImplemented

    def function(
        self,
        func: Callable,
        *,
        name: str | None = None,
    ) -> OperationSyncProtocol:
        """Create function operation."""
        raise HandlerNotImplemented

    def sequence(
        self,
        *operations: OperationSyncProtocol,
        delay: float = 0,
        continue_on_error: bool = False,
    ) -> OperationSyncProtocol:
        """Create sequential operation."""
        raise HandlerNotImplemented


@runtime_checkable
class AppTasksAsyncProtocol(Protocol):
    """Protocol defining asynchronous service operation capabilities."""

    async def execute(self, operation: OperationAsyncProtocol) -> None:
        """Execute operation."""
        raise HandlerNotImplemented

    def function(
        self,
        func: Callable,
        *,
        name: str | None = None,
    ) -> OperationAsyncProtocol:
        """Create function operation."""
        raise HandlerNotImplemented

    def sequence(
        self,
        *operations: OperationAsyncProtocol,
        delay: float = 0,
        continue_on_error: bool = False,
    ) -> OperationAsyncProtocol:
        """Create sequential operation."""
        raise HandlerNotImplemented


@runtime_checkable
class AppModelAsyncProtocol(Protocol):
    def initialize_model(self) -> None:
        """Initialize model."""
        raise HandlerNotImplemented


@runtime_checkable
class AppModelSyncProtocol(Protocol):
    def initialize_model(self) -> None:
        """Initialize model."""
        raise HandlerNotImplemented


class AppCommonProtocol(
    AppCommonBaseProtocol,
    Protocol,
):
    """Common application protocol."""

    pass


class AppSyncProtocol(
    AppCommonProtocol,
    AppInitializerSyncProtocol,
    AppServicesSyncProtocol,
    AppStateSyncProtocol,
    AppTasksSyncProtocol,
    AppModelSyncProtocol,
    Protocol,
):
    """Synchronous application protocol."""

    pass


class AppAsyncProtocol(
    AppCommonProtocol,
    AppInitializerAsyncProtocol,
    AppServicesAsyncProtocol,
    AppStateAsyncProtocol,
    AppTasksAsyncProtocol,
    AppModelAsyncProtocol,
    Protocol,
):
    """Asynchronous application protocol."""

    pass
