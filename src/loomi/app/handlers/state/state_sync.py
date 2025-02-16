from __future__ import annotations

from typing import Generator

from loomi.app.base import SyncApp

from .base import AppCommonState
from .config import DEFALT_APP_STATE_SCOPE
from .exceptions import StateError
from .protocols import (
    SyncStateProtocol,
    SyncSubscriptionProtocol,
    SyncTransactionContextManagerProtocol,
    SyncTransactionProtocol,
)
from .types import StateKey, StateValue, SyncStateCallbackFn

__all__ = [
    "SyncAppState",
]


class SyncAppState(AppCommonState, SyncApp):
    """
    App feature implementing state management.

    Features:
    - State adapter handling
    - State management methods
    - State subscription management
    - State transaction management
    """

    @property
    def state(self) -> SyncStateProtocol:
        """Check and return app's state service."""
        if not self._state_service_name or len(self._state_service_name) == 0:
            raise StateError("No state adapter configured")
        return getattr(self, self._state_service_name)

    @property
    def s(self) -> SyncStateProtocol:
        """Short alias for state adapter."""
        return self.state

    def get(
        self,
        key: StateKey,
        local=DEFALT_APP_STATE_SCOPE,
    ) -> StateValue:
        """Get state value at key."""
        if local:
            key = self._local_state_key + key
        return self.s.get(key)

    def set(
        self,
        key: StateKey,
        value: StateValue,
        local=DEFALT_APP_STATE_SCOPE,
    ) -> None:
        """Set state value at key."""
        if local:
            key = self._local_state_key + key
        self.s.set(key, value)

    def delete(
        self,
        key: StateKey,
        local=DEFALT_APP_STATE_SCOPE,
    ) -> None:
        """Delete state at key."""
        if local:
            key = self._local_state_key + key
        self.s.delete(key)

    def exists(
        self,
        key: StateKey,
        local=DEFALT_APP_STATE_SCOPE,
    ) -> bool:
        """Check if state exists at key."""
        if local:
            key = self._local_state_key + key
        return self.s.exists(key)

    def list_keys(
        self,
        prefix: StateKey,
        local=DEFALT_APP_STATE_SCOPE,
    ) -> Generator[StateKey, None, None]:
        """List all state keys under prefix."""
        if local:
            key = self._local_state_key + prefix

        for full_key in self.s.list_keys(key):
            # Strip app prefix from returned keys
            yield full_key[len(self._local_state_key) :]

    def subscribe(
        self,
        key: StateKey,
        callback: SyncStateCallbackFn,
        local=DEFALT_APP_STATE_SCOPE,
    ) -> SyncSubscriptionProtocol:
        """
        Subscribe to changes under key prefix.

        Args:
            key: Key prefix to subscribe to
            callback: Sync callback function for notifications

        Returns:
            Subscription object for unsubscribing

        Raises:
            ObserverError: If subscription fails
        """
        if local:
            key = self._local_state_key + key
        return self.s.subscribe(key, callback)

    def unsubscribe(self, subscription: SyncSubscriptionProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        self.s.unsubscribe(subscription)

    def begin_transaction(self) -> SyncTransactionProtocol:
        """
        Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        return self.s.begin_transaction()

    def transaction(self) -> SyncTransactionContextManagerProtocol:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager
        """
        return self.s.transaction()
