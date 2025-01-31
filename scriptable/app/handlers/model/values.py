"""
Implementation of value objects.

This module provides the actual implementations for leaf values (items)
and branch values (nested models) in the state.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, AsyncIterator, Generic, Type, TypeVar, cast

from sonny.state.async_state.protocols import SubscriptionProtocol
from sonny.state.types import StateAsyncCallbackFn, StateKey, StateValue

from .descriptors import ItemDescriptor, ModelItemDescriptor
from .types import StateContext

if TYPE_CHECKING:
    from .service import ModelService

StateValueT = TypeVar("StateValueT", bound=StateValue)
ModelServiceT = TypeVar("ModelServiceT", bound="ModelService")


class ItemValue(Generic[StateValueT]):
    """
    Implementation for leaf values.

    Provides typed access to individual values with proper
    transaction handling and state forwarding.
    """

    def __init__(self, name: str, context: StateContext) -> None:
        self._name: str = name
        self._context: StateContext = context

    def key(self) -> StateKey:
        """Get item key."""
        return self._context.prefix + (self._name,)

    async def get(self) -> StateValueT:
        """Get item value."""
        if self._context.txn_context and self._context.txn_context.transaction:
            value = await self._context.txn_context.transaction.get(self.key())
        else:
            value = await self._context.state.get(self.key())
        return cast(StateValueT, value)

    async def set(self, value: StateValueT) -> None:
        """Set item value."""
        if self._context.txn_context and self._context.txn_context.transaction:
            await self._context.txn_context.transaction.set(self.key(), value)
        else:
            await self._context.state.set(self.key(), value)

    async def delete(self) -> None:
        """Delete item value."""
        if self._context.txn_context and self._context.txn_context.transaction:
            await self._context.txn_context.transaction.delete(self.key())
        else:
            await self._context.state.delete(self.key())

    async def exists(self) -> bool:
        """Check if item exists."""
        if self._context.txn_context and self._context.txn_context.transaction:
            return await self._context.txn_context.transaction.exists(self.key())
        return await self._context.state.exists(self.key())

    async def list_keys(self) -> AsyncIterator[StateKey]:
        """List keys with prefix."""
        if self._context.txn_context and self._context.txn_context.transaction:
            async for key in self._context.txn_context.transaction.list_keys(self.key()):  # type: ignore
                yield key
        else:
            async for key in self._context.state.list_keys(self.key()):  # type: ignore
                yield key

    async def subscribe(self, callback: StateAsyncCallbackFn) -> SubscriptionProtocol:
        """Subscribe to item changes."""
        return await self._context.state.subscribe(self.key(), callback)

    async def unsubscribe(self, subscription: SubscriptionProtocol) -> None:
        """Unsubscribe from item changes."""
        await self._context.state.unsubscribe(subscription)


class ModelValue(Generic[ModelServiceT]):
    """
    Implementation for nested model values.

    Manages nested model instances with proper context propagation.
    """

    def __init__(self, name: str, context: StateContext, model_class: Type[ModelServiceT]) -> None:
        self._name = name
        self._context = context
        self._model_class = model_class
        self._init_items()

    def key(self) -> StateKey:
        """Get item key."""
        return self._context.prefix + (self._name,)

    def _init_items(self) -> None:
        """
        Init model items
        """
        context = self._context
        context.prefix = self._context.prefix + (self._name,)

        for name, value in self._model_class.__dict__.items():
            if hasattr(self, name):
                continue

            if isinstance(value, ItemDescriptor):
                setattr(self, name, ItemValue[value._type](name, context))
            elif isinstance(value, ModelItemDescriptor):
                setattr(self, name, ModelValue(name, replace(context), model_class=value._type))
