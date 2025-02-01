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

from typing import Iterator

from scriptable.app.base import AppSyncBase

from .exceptions import StateError
from .protocols import (
    StateSyncProtocol,
    SubscriptionSyncProtocol,
    TransactionContextManagerSyncProtocol,
    TransactionSyncProtocol,
)
from .types import StateKey, StateSyncCallbackFn, StateValue


class AppState(AppSyncBase):
    """
    app feature implementing state management.

    Features:
    - State adapter handling
    - State management methods
    - State subscription management
    - State transaction management
    """

    @property
    def state(self) -> StateSyncProtocol:
        """Check and return app's state service."""
        if not hasattr(self, "_state_"):
            raise StateError("No state adapter configured")
        return getattr(self, "_state_")

    @property
    def s(self) -> StateSyncProtocol:
        """Short alias for state adapter."""
        return self.state

    @property
    def state_key(self) -> StateKey:
        """Base state key for this app instance."""
        return (f"__app__{self.key}",)

    def get(self, key: StateKey) -> StateValue:
        """Get state value at key."""
        key = self.state_key + key
        return self.s.get(key)

    def set(self, key: StateKey, value: StateValue) -> None:
        """Set state value at key."""
        key = self.state_key + key
        self.s.set(key, value)

    def delete(self, key: StateKey) -> None:
        """Delete state at key."""
        key = self.state_key + key
        self.s.delete(key)

    def exists(self, key: StateKey) -> bool:
        """Check if state exists at key."""
        key = self.state_key + key
        return self.s.exists(key)

    def list(self, prefix: StateKey) -> Iterator[StateKey]:
        """List all state keys under prefix."""
        key = self.state_key + prefix
        for full_key in self.s.list_keys(key):
            # Strip app prefix from returned keys
            yield full_key[len(self.state_key) :]

    def subscribe(self, key: StateKey, callback: StateSyncCallbackFn) -> SubscriptionSyncProtocol:
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
        key = self.state_key + key
        return self.s.subscribe(key, callback)

    def unsubscribe(self, subscription: SubscriptionSyncProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        self.s.unsubscribe(subscription)

    def begin_transaction(self) -> TransactionSyncProtocol:
        """
        Begin transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        return self.s.begin_transaction()

    def transaction(self) -> TransactionContextManagerSyncProtocol:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager
        """
        return self.s.transaction()
