"""
Model service implementation.

This module implements the model service class that uses
descriptor system for ORM-like state functionality.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from types import TracebackType
from typing import Generic, Self, TypeVar

from sonny.composer.async_composer import ServiceComposer
from sonny.state.async_state import StateProtocol
from sonny.state.types import StateKey

from .descriptors import ItemDescriptor, ModelItemDescriptor
from .types import StateContext, TransactionContext
from .values import ItemValue, ModelValue


class ModelService(ServiceComposer):
    """
    Base class for models.

    Provides ORM-like interface for state management with:
    - Type-safe field declarations
    - Nested models
    - Transaction support
    - Change notifications

    Example:
        ```python
        class UserPreferences(ModelService):
            theme: Item[str] = Item(default="light")
            language: Item[str] = Item(default="en")

        class User(ModelService):
            name: Item[str] = Item()
            preferences: ModelItem[UserPreferences] = ModelItem()
        ```
    """

    _state_: StateProtocol

    async def post_initialize(self) -> None:
        """Post-initialize hook."""
        await super().post_initialize()

        if hasattr(self, "_skip_context_init") and getattr(self, "_skip_context_init") is True:
            return

        self._init_model_context(tuple(), TransactionContext())
        self._init_model_items()

    def _init_model_context(self, prefix: StateKey, txn_context: TransactionContext) -> None:
        """Initialize context."""

        self._prefix = prefix
        self._txn_context = txn_context
        self._context = StateContext(self._state_, self._prefix, txn_context)

    def _init_model_items(self) -> None:
        """
        Init model items
        """
        for name, value in self.__class__.__dict__.items():
            if hasattr(self, name):
                continue

            if isinstance(value, ItemDescriptor):
                setattr(self, name, ItemValue[value._type](name, self._context))
            elif isinstance(value, ModelItemDescriptor):
                setattr(
                    self, name, ModelValue(name, replace(self._context), model_class=value._type)
                )

    async def begin_transaction(self) -> Self:
        """Begin new transaction."""
        txn = await self._state_.begin_transaction()
        txn_context = TransactionContext(txn)

        # FIXME: impl a robust way to create transactional handler
        # ATM, we are creating a new instance with txn context
        # which is dirty and not recommended.
        spec = self.spec.model_copy()
        spec.name = f"{self.spec.name}_txn_{str(uuid.uuid4())}"
        inst = type(self)(spec)

        # Mark as transaction service to skip effects execution.
        # This is a workaround imposed by the current design.
        setattr(inst, "_dismiss_effects", True)
        # Handle context initialization
        setattr(inst, "_skip_context_init", True)
        inst._init_model_context(self._prefix, txn_context)
        inst._init_model_items()

        return inst

    async def commit(self) -> None:
        """Commit transaction."""
        if (
            self._context.txn_context
            and self._context.txn_context.active
            and self._context.txn_context.transaction
        ):
            await self._context.txn_context.transaction.commit()

    async def rollback(self) -> None:
        """Commit transaction."""
        if (
            self._context.txn_context
            and self._context.txn_context.active
            and self._context.txn_context.transaction
        ):
            await self._context.txn_context.transaction.rollback()

    async def transaction(self) -> TransactionContextManager[Self]:
        """Get transaction context manager."""
        return TransactionContextManager(await self.begin_transaction())


ModelServiceT = TypeVar("ModelServiceT", bound=ModelService)


class TransactionContextManager(Generic[ModelServiceT]):
    """Async context manager for storage transactions."""

    def __init__(self, handler: ModelServiceT) -> None:
        """
        Initialize transaction context manager.

        Args:
            storage: Storage instance to manage transactions for
        """
        self.handler = handler

    async def __aenter__(self) -> ModelServiceT:
        """
        Start a new transaction.

        Returns:
            New transaction instance

        Raises:
            StorageError: If transaction cannot be started
        """
        await self.handler.initialize()
        return self.handler

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Commit or rollback transaction based on context exit.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if self.handler:
            if exc_type is None:
                await self.handler.commit()
            else:
                await self.handler.rollback()
            await self.handler.shutdown()
