"""State management protocol definitions."""

from __future__ import annotations

from abc import abstractmethod
from typing import AsyncIterator, Callable, Protocol, runtime_checkable

from .exceptions import HandlerNotImplemented
from .handlers.state.protocols import (
    SubscriptionAsyncProtocol,
    TransactionAsyncProtocol,
    TransactionContextManagerAsyncProtocol,
)
from .handlers.state.types import StateAsyncCallbackFn, StateKey, StateValue
from .handlers.tasks.protocols import OperationAsyncProtocol


class AppCommonBaseProtocol(Protocol):
    pass


@runtime_checkable
class AppStateAsyncProtocol(Protocol):
    """Protocol defining service state management."""

    @abstractmethod
    async def get(self, key: StateKey) -> StateValue:
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
    async def set(self, key: StateKey, value: StateValue) -> None:
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
    async def delete(self, key: StateKey) -> None:
        """
        Delete state at path.

        Args:
            key: State path components

        Raises:
            StateError: If state deletion fails
        """
        raise HandlerNotImplemented

    @abstractmethod
    async def exists(self, key: StateKey) -> bool:
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
    async def list(self, *prefix: str) -> AsyncIterator[StateKey]:
        """
        List all state keys under prefix.

        Args:
            *prefix: State path prefix components

        Returns:
            AsyncIterator of matching state keys

        Raises:
            StateError: If state listing fails
        """
        raise HandlerNotImplemented

    @abstractmethod
    async def subscribe(
        self, key: StateKey, callback: StateAsyncCallbackFn
    ) -> SubscriptionAsyncProtocol:
        """
        Subscribe to changes under key prefix.

        Args:
            key: Key prefix to subscribe to
            callback: Async callback function for notifications

        Returns:
            Subscription object for unsubscribing

        Raises:
            ObserverError: If subscription fails
        """
        raise HandlerNotImplemented

    @abstractmethod
    async def unsubscribe(self, subscription: SubscriptionAsyncProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        raise HandlerNotImplemented

    @abstractmethod
    async def begin_transaction(self) -> TransactionAsyncProtocol:
        """
        Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        raise HandlerNotImplemented

    @abstractmethod
    async def transaction(self) -> TransactionContextManagerAsyncProtocol:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager
        """
        raise HandlerNotImplemented


@runtime_checkable
class AppTasksAsyncProtocol(Protocol):
    """Protocol defining service operation capabilities."""

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


class AppCommonProtocol(
    AppCommonBaseProtocol,
    Protocol,
):
    """Common application protocol."""

    pass


class AppSyncProtocol(
    AppCommonProtocol,
    Protocol,
):
    """Async application protocol."""

    pass


class AppAsyncProtocol(
    AppCommonProtocol,
    AppStateAsyncProtocol,
    AppTasksAsyncProtocol,
    Protocol,
):
    """Async application protocol."""

    pass
