from __future__ import annotations

from typing import AsyncGenerator

from loomi.app.base import AsyncApp

from .base import AppCommonState
from .config import DEFALT_APP_STATE_SCOPE
from .exceptions import StateError
from .protocols import (
    AsyncStateProtocol,
    AsyncSubscriptionProtocol,
    AsyncTransactionContextManagerProtocol,
    AsyncTransactionProtocol,
)
from .types import AsyncStateCallbackFn, StateKey, StateValue

__all__ = [
    "AsyncAppState",
]


class AsyncAppState(AppCommonState, AsyncApp):
    """
    App feature implementing state management.

    Features:
    - State adapter handling
    - State management methods
    - State subscription management
    - State transaction management

    Example:
        class DataApp(AsyncApp):
            ...

            def exec_data_process(self, key: str) -> Any:
                await self.set(("status",), "processing")
                result = self.process_data(key)
                await self.set(("status,), "done")
    """

    @property
    def state(self) -> AsyncStateProtocol:
        """Check and return app's state service."""
        if not self._state_service_name or len(self._state_service_name) == 0:
            raise StateError("No state adapter configured")
        return getattr(self, self._state_service_name)

    @property
    def s(self) -> AsyncStateProtocol:
        """Short alias for state adapter."""
        return self.state

    async def get(
        self,
        key: StateKey,
        local: bool = DEFALT_APP_STATE_SCOPE,
    ) -> StateValue:
        """Get state value at key."""
        if local:
            key = self._local_state_key + key
        return await self.s.get(key)

    async def set(
        self,
        key: StateKey,
        value: StateValue,
        local: bool = DEFALT_APP_STATE_SCOPE,
    ) -> None:
        """Set state value at key."""
        if local:
            key = self._local_state_key + key
        await self.s.set(key, value)

    async def delete(
        self,
        key: StateKey,
        local: bool = DEFALT_APP_STATE_SCOPE,
    ) -> None:
        """Delete state at key."""
        if local:
            key = self._local_state_key + key
        await self.s.delete(key)

    async def exists(
        self,
        key: StateKey,
        local: bool = DEFALT_APP_STATE_SCOPE,
    ) -> bool:
        """Check if state exists at key."""
        if local:
            key = self._local_state_key + key
        return await self.s.exists(key)

    async def list_keys(
        self,
        prefix: StateKey,
        local: bool = DEFALT_APP_STATE_SCOPE,
    ) -> AsyncGenerator[StateKey, None]:
        """List all state keys under prefix."""
        if local:
            key = self._local_state_key + prefix

        async for full_key in self.s.list_keys(key):
            # Strip app prefix from returned keys
            yield full_key[len(self._local_state_key) :]

    async def subscribe(
        self,
        key: StateKey,
        callback: AsyncStateCallbackFn,
        local: bool = DEFALT_APP_STATE_SCOPE,
    ) -> AsyncSubscriptionProtocol:
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
        if local:
            key = self._local_state_key + key
        return await self.s.subscribe(key, callback)

    async def unsubscribe(
        self,
        subscription: AsyncSubscriptionProtocol,
        local: bool = DEFALT_APP_STATE_SCOPE,
    ) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        await self.s.unsubscribe(subscription)

    async def begin_transaction(self) -> AsyncTransactionProtocol:
        """
        Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        return await self.s.begin_transaction()

    async def transaction(self) -> AsyncTransactionContextManagerProtocol:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager
        """
        return await self.s.transaction()
