"""
Value accessor implementation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator, Generic, TypeVar, cast

from loomi.app.handlers.state.types import StateKey, StateValue

if TYPE_CHECKING:
    from loomi.app.handlers.state import AsyncStateCallbackFn, AsyncSubscriptionProtocol

    from .model_async import AsyncAppModel
    from .protocols import AsyncAccessorContextProtocol

__all__ = [
    "AsyncModelValue",
]

T = TypeVar("T", bound=StateValue)


class AsyncModelValue(Generic[T]):
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

    def __init__(self, model: "AsyncAppModel", name: str) -> None:
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
    def _context(self) -> "AsyncAccessorContextProtocol":
        """
        Get current context from model.

        The context can be either direct state access or transaction
        depending on whether the model is currently in a transaction.

        Returns:
            Current accessor context
        """
        return self._model.context

    async def get(self) -> T:
        """
        Get current value.

        Returns:
            Current value of type T

        Raises:
            StorageError: If get operation fails
        """
        return cast(T, await self._context.get(self._make_key()))

    async def set(self, value: T) -> None:
        """
        Set new value.

        Args:
            value: New value to set

        Raises:
            StorageError: If set operation fails
        """
        await self._context.set(self._make_key(), value)

    async def delete(self) -> None:
        """
        Delete current value.

        Raises:
            StorageError: If delete operation fails
        """
        await self._context.delete(self._make_key())

    async def exists(self) -> bool:
        """
        Check if value exists.

        Returns:
            True if value exists, False otherwise

        Raises:
            StorageError: If check fails
        """
        return await self._context.exists(self._make_key())

    async def list_keys(self) -> AsyncGenerator[StateKey, None]:
        """List all state keys under prefix."""
        async for full_key in self._context.list_keys(self._make_key()):
            # Strip app prefix from returned keys
            yield full_key[len(self._make_key()) :]

    async def subscribe(self, callback: "AsyncStateCallbackFn") -> "AsyncSubscriptionProtocol":
        """Subscribe to item changes."""
        return await self._context.subscribe(self._make_key(), callback)

    async def unsubscribe(self, subscription: "AsyncSubscriptionProtocol") -> None:
        """Unsubscribe from item changes."""
        await self._context.unsubscribe(subscription)
