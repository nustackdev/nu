"""
app base class providing dependency injection, lifecycle management,
and component-based architecture.

This module implements the core app functionality with:
- Dependency injection and lifecycle (from Memory)
- Component-based composition
- State and operation platforms
- Extension points
"""

from __future__ import annotations

from typing import AsyncIterator

from scriptable.app.base import AppAsyncBase

from .exceptions import StateError
from .protocols import (
    StateAsyncProtocol,
    SubscriptionAsyncProtocol,
    TransactionAsyncProtocol,
    TransactionContextManagerAsyncProtocol,
)
from .types import StateAsyncCallbackFn, StateKey, StateValue


class AppState(AppAsyncBase):
    """
    app feature implementing state management.

    Features:
    - State adapter handling
    - State management methods
    - State subscription management
    - State transaction management

    Example:
        class Dataapp(
            app(
                as_state(RedisStorage),
                as_platform(AsyncPlatform)
            )
        ):
            ...

            def exec_data_process(self, key: str) -> Any:
                self.state_set(("status",), "processing")
                result = self.process_data(key)
                self.state_set(("status,), "done")
    """

    @property
    def state(self) -> StateAsyncProtocol:
        """Check and return app's state service."""
        if not hasattr(self, "_state_"):
            raise StateError("No state adapter configured")
        return getattr(self, "_state_")

    @property
    def s(self) -> StateAsyncProtocol:
        """Short alias for state adapter."""
        return self.state

    @property
    def state_key(self) -> StateKey:
        """Base state key for this app instance."""
        return (f"__app__{self.key}",)

    async def get(self, key: StateKey) -> StateValue:
        """Get state value at key."""
        key = self.state_key + key
        return await self.s.get(key)

    async def set(self, key: StateKey, value: StateValue) -> None:
        """Set state value at key."""
        key = self.state_key + key
        await self.s.set(key, value)

    async def delete(self, key: StateKey) -> None:
        """Delete state at key."""
        key = self.state_key + key
        await self.s.delete(key)

    async def exists(self, key: StateKey) -> bool:
        """Check if state exists at key."""
        key = self.state_key + key
        return await self.s.exists(key)

    async def list(self, prefix: StateKey) -> AsyncIterator[StateKey]:
        """List all state keys under prefix."""
        key = self.state_key + prefix
        async for full_key in await self.s.list_keys(key):
            # Strip app prefix from returned keys
            yield full_key[len(self.state_key) :]

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
        key = self.state_key + key
        return await self.s.subscribe(key, callback)

    async def unsubscribe(self, subscription: SubscriptionAsyncProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        await self.s.unsubscribe(subscription)

    async def begin_transaction(self) -> TransactionAsyncProtocol:
        """
        Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        return await self.s.begin_transaction()

    async def transaction(self) -> TransactionContextManagerAsyncProtocol:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager
        """
        return await self.s.transaction()
