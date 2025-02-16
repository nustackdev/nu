from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, AsyncGenerator, Callable, Generator, Protocol, Self

if TYPE_CHECKING:
    from .handlers.state.protocols import (
        AsyncStateProtocol,
        AsyncSubscriptionProtocol,
        AsyncTransactionContextManagerProtocol,
        AsyncTransactionProtocol,
        SyncStateProtocol,
        SyncSubscriptionProtocol,
        SyncTransactionContextManagerProtocol,
        SyncTransactionProtocol,
    )
    from .handlers.state.types import (
        AsyncStateCallbackFn,
        StateKey,
        StateValue,
        SyncStateCallbackFn,
    )
    from .handlers.tasks.protocols import AsyncOperationProtocol, SyncOperationProtocol

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


class CommonAppProtocol(Protocol):
    """Base protocol for common application functionality."""

    pass


class SyncAppInitializerProtocol(Protocol):
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


class AsyncAppInitializerProtocol(Protocol):
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


class AsyncAppServicesProtocol(Protocol):
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


class SyncAppServicesProtocol(Protocol):
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


class SyncAppStateProtocol(Protocol):
    """Protocol defining synchronous service state management."""

    @property
    def state(self) -> "SyncStateProtocol":
        """Check and return app's state service."""
        ...

    @property
    def s(self) -> "SyncStateProtocol":
        """Short alias for state adapter."""
        ...

    def get(self, key: "StateKey", local: bool = ...) -> "StateValue":
        """
        Get state value at path.

        Args:
            key: State path components

        Returns:
            State value if exists, None otherwise

        Raises:
            StateError: If state access fails
        """
        ...

    def set(self, key: "StateKey", value: "StateValue", local: bool = ...) -> None:
        """
        Set state value at path.

        Args:
            key: State path components
            value: Value to store

        Raises:
            StateError: If state update fails
        """
        ...

    def delete(self, key: "StateKey", local: bool = ...) -> None:
        """
        Delete state at path.

        Args:
            key: State path components

        Raises:
            StateError: If state deletion fails
        """
        ...

    def exists(self, key: "StateKey", local: bool = ...) -> bool:
        """
        Check if state exists at path.

        Args:
            key: State path components

        Returns:
            True if key exists, False otherwise

        Raises:
            StateError: If state check fails
        """
        ...

    def list_keys(
        self,
        prefix: "StateKey",
        local: bool = ...,
    ) -> Generator["StateKey", None, None]:
        """
        List all state keys under prefix.

        Args:
            prefix: State path prefix components

        Returns:
            Generator of matching state keys

        Raises:
            StateError: If state listing fails
        """
        ...

    def subscribe(
        self,
        key: "StateKey",
        callback: "SyncStateCallbackFn",
        local: bool = ...,
    ) -> "SyncSubscriptionProtocol":
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
        ...

    def unsubscribe(self, subscription: "SyncSubscriptionProtocol") -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        ...

    def begin_transaction(self) -> "SyncTransactionProtocol":
        """
        Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        ...

    def transaction(self) -> "SyncTransactionContextManagerProtocol":
        """
        Get transaction context manager.

        Returns:
            Transaction context manager
        """
        ...

    def _initialize_state_descriptor(self) -> None:
        """Initialize state descriptor."""
        ...


class AsyncAppStateProtocol(Protocol):
    """Protocol defining asynchronous service state management."""

    @property
    def state(self) -> "AsyncStateProtocol":
        """Check and return app's state service."""
        ...

    @property
    def s(self) -> "AsyncStateProtocol":
        """Short alias for state adapter."""
        ...

    async def get(self, key: "StateKey", local: bool = ...) -> "StateValue":
        """Get state value at path."""
        ...

    async def set(self, key: "StateKey", value: "StateValue", local: bool = ...) -> None:
        """Set state value at path."""
        ...

    async def delete(self, key: "StateKey", local: bool = ...) -> None:
        """Delete state at path."""
        ...

    async def exists(self, key: "StateKey", local: bool = ...) -> bool:
        """Check if state exists at path."""
        ...

    async def list_keys(
        self,
        prefix: "StateKey",
        local: bool = ...,
    ) -> AsyncGenerator["StateKey", None]:
        """List all state keys under prefix."""
        ...

    async def subscribe(
        self,
        key: "StateKey",
        callback: "AsyncStateCallbackFn",
        local: bool = ...,
    ) -> "AsyncSubscriptionProtocol":
        """Subscribe to changes under key prefix."""
        ...

    async def unsubscribe(self, subscription: "AsyncSubscriptionProtocol") -> None:
        """Unsubscribe from changes under key prefix."""
        ...

    async def begin_transaction(self) -> "AsyncTransactionProtocol":
        """Begin transaction."""
        ...

    async def transaction(self) -> "AsyncTransactionContextManagerProtocol":
        """Get transaction context manager."""
        ...

    def _initialize_state_descriptor(self) -> None:
        """Initialize state descriptor."""
        ...


class SyncAppTasksProtocol(Protocol):
    """Protocol defining synchronous service operation capabilities."""

    def execute(self, operation: "SyncOperationProtocol") -> None:
        """Execute operation."""
        ...

    def function(
        self,
        func: Callable,
        *,
        name: str | None = None,
    ) -> "SyncOperationProtocol":
        """Create function operation."""
        ...

    def sequence(
        self,
        *operations: "SyncOperationProtocol",
        delay: float = 0,
        continue_on_error: bool = False,
    ) -> "SyncOperationProtocol":
        """Create sequential operation."""
        ...


class AsyncAppTasksProtocol(Protocol):
    """Protocol defining asynchronous service operation capabilities."""

    async def execute(self, operation: "AsyncOperationProtocol") -> None:
        """Execute operation."""
        ...

    def function(
        self,
        func: Callable,
        *,
        name: str | None = None,
    ) -> "AsyncOperationProtocol":
        """Create function operation."""
        ...

    def sequence(
        self,
        *operations: "AsyncOperationProtocol",
        delay: float = 0,
        continue_on_error: bool = False,
    ) -> "AsyncOperationProtocol":
        """Create sequential operation."""
        ...


class SyncAppModelProtocol(Protocol):
    def _initialize_model_descriptors(self) -> None:
        """Initialize model."""
        ...


class AsyncAppModelProtocol(Protocol):
    def _initialize_model_descriptors(self) -> None:
        """Initialize model."""
        ...


class AppProtocol(
    CommonAppProtocol,
    Protocol,
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
    Protocol,
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
    Protocol,
):
    """Asynchronous application protocol."""

    pass
