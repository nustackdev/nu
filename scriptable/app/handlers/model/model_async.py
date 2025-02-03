"""
Model service implementation.

This module implements the model service class that uses
descriptor system for ORM-like state functionality.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, AsyncContextManager, Self

from scriptable.app.base import AppAsyncBase

from .accesssor import ModelValue
from .base import AppCommonModel
from .descriptor import StateDescriptor
from .exceptions import ModelTransactionError

# from sonny.composer.async_composer import ServiceComposer
# from sonny.state.async_state import StateProtocol
# from sonny.state.types import StateKey

# from .descriptors import ItemDescriptor, ModelItemDescriptor
# from .types import StateContext, TransactionContext
# from .values import ItemValue, ModelValue


# _state_: StateProtocol

# async def begin_transaction(self) -> Self:
#     """Begin new transaction."""
#     txn = await self._state_.begin_transaction()
#     txn_context = TransactionContext(txn)

#     # FIXME: impl a robust way to create transactional handler
#     # ATM, we are creating a new instance with txn context
#     # which is dirty and not recommended.
#     spec = self.spec.model_copy()
#     spec.name = f"{self.spec.name}_txn_{str(uuid.uuid4())}"
#     inst = type(self)(spec)

#     # Mark as transaction service to skip effects execution.
#     # This is a workaround imposed by the current design.
#     setattr(inst, "_dismiss_effects", True)
#     # Handle context initialization
#     setattr(inst, "_skip_context_init", True)
#     inst._init_model_context(self._prefix, txn_context)
#     inst._init_model_items()

#     return inst

# async def commit(self) -> None:
#     """Commit transaction."""
#     if (
#         self._context.txn_context
#         and self._context.txn_context.active
#         and self._context.txn_context.transaction
#     ):
#         await self._context.txn_context.transaction.commit()

# async def rollback(self) -> None:
#     """Commit transaction."""
#     if (
#         self._context.txn_context
#         and self._context.txn_context.active
#         and self._context.txn_context.transaction
#     ):
#         await self._context.txn_context.transaction.rollback()

# async def transaction(self) -> TransactionContextManager[Self]:
#     """Get transaction context manager."""
#     return TransactionContextManager(await self.begin_transaction())


if TYPE_CHECKING:
    pass

    from .protocols import AccessorContextAsyncProtocol


@dataclass
class ModelAsyncContext:
    """
    Holds coroutine-local context for a model instance.

    Attributes:
        transaction: Optional active transaction for this context
    """

    transaction: "AccessorContextAsyncProtocol | None" = None


class AppModel(AppCommonModel, AppAsyncBase):
    @property
    def context(self) -> "AccessorContextAsyncProtocol":
        """
        Get current context for operations.

        Returns either active transaction or direct state access
        based on whether this coroutine is in a transaction.

        Returns:
            Current accessor context
        """
        if not hasattr(self, "_context_var"):
            self._context_var = ContextVar(f"model_context_{id(self)}", default=ModelAsyncContext())

        ctx = self._context_var.get()
        if ctx.transaction is not None:
            return ctx.transaction
        return self.state

    def initialize_model(self) -> None:
        """
        Init model items
        """
        for name, value in self.__class__.__dict__.items():
            if hasattr(self, name):
                continue

            if isinstance(value, StateDescriptor):
                setattr(self, name, ModelValue(self, name))

    @asynccontextmanager  # type: ignore
    async def model_transaction(self) -> AsyncContextManager[Self]:  # type: ignore
        """
        Start a new transaction.

        The transaction is coroutine-local and will not affect
        other coroutines accessing the same model instance.

        Returns:
            Self for method chaining

        Raises:
            ModelError: If transaction already active in this coroutine
        """
        # Get current context
        ctx = self._context_var.get()
        if ctx.transaction is not None:
            raise ModelTransactionError("Transaction already active in this coroutine")

        # Create new transaction and update context
        transaction = await self.state.begin_transaction()
        token = self._context_var.set(ModelAsyncContext(transaction=transaction))  # type: ignore

        try:
            yield self  # type: ignore
            await transaction.commit()
        except Exception:
            # Rollback on any error
            await transaction.rollback()
            raise
        finally:
            # Always restore previous context
            self._context_var.reset(token)
