"""
Value accessor implementation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Generic, TypeVar, cast

from scriptable.app.handlers.state.types import StateKey, StateValue

if TYPE_CHECKING:
    from scriptable.app.handlers.state import SyncStateCallbackFn, SyncSubscriptionProtocol

    from .model_sync import SyncAppModel
    from .protocols import SyncAccessorContextProtocol

__all__ = [
    "SyncModelValue",
]

T = TypeVar("T", bound=StateValue)


class SyncModelValue(Generic[T]):
    """
    Value accessor that works with model's current context.

    Provides unified interface for accessing values through either
    direct state access or transaction context.

    Type Parameters:
        T: Type of the value being accessed

    Attributes:
        _model: Reference to parent model instance
        _name: Name of this value in the model
    """

    def __init__(self, model: "SyncAppModel", name: str) -> None:
        """
        Initialize value accessor.

        Args:
            model: Parent model instance
            name: Name of this value in model
        """
        self._model = model
        self._name = name

    def _make_key(self) -> StateKey:
        """
        Convert accessor name to state key.

        Returns:
            Tuple containing name as state key
        """
        return (self._name,)

    @property
    def _context(self) -> "SyncAccessorContextProtocol":
        """
        Get current context from model.

        The context can be either direct state access or transaction
        depending on whether the model is currently in a transaction.

        Returns:
            Current accessor context
        """
        return self._model.context

    def get(self) -> T:
        """
        Get current value.

        Returns:
            Current value of type T

        Raises:
            StorageError: If get operation fails
        """
        return cast(T, self._context.get(self._make_key()))

    def set(self, value: T) -> None:
        """
        Set new value.

        Args:
            value: New value to set

        Raises:
            StorageError: If set operation fails
        """
        self._context.set(self._make_key(), value)

    def delete(self) -> None:
        """
        Delete current value.

        Raises:
            StorageError: If delete operation fails
        """
        self._context.delete(self._make_key())

    def exists(self) -> bool:
        """
        Check if value exists.

        Returns:
            True if value exists, False otherwise

        Raises:
            StorageError: If check fails
        """
        return self._context.exists(self._make_key())

    def list_keys(self) -> Generator[StateKey, None, None]:
        """List all state keys under prefix."""
        for full_key in self._context.list_keys(self._make_key()):
            # Strip app prefix from returned keys
            yield full_key[len(self._make_key()) :]

    def subscribe(self, callback: "SyncStateCallbackFn") -> "SyncSubscriptionProtocol":
        """Subscribe to item changes."""
        return self._context.subscribe(self._make_key(), callback)

    def unsubscribe(self, subscription: "SyncSubscriptionProtocol") -> None:
        """Unsubscribe from item changes."""
        self._context.unsubscribe(subscription)
