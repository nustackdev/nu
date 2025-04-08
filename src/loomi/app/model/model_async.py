# """
# Model implementation.

# This module implements the model service class that uses
# descriptor system for ORM-like state functionality.
# """

# from __future__ import annotations

# from contextlib import asynccontextmanager
# from contextvars import ContextVar
# from dataclasses import dataclass
# from typing import TYPE_CHECKING, AsyncContextManager, Self

# from loomi.app.base import AsyncApp

# from .accesssor_async import AsyncModelValue
# from .base import AppCommonModel
# from .descriptor import ModelDescriptor
# from .exceptions import ModelTransactionError

# if TYPE_CHECKING:
#     from .protocols import AsyncAccessorContextProtocol

# __all__ = [
#     "AsyncAppModel",
# ]


# @dataclass
# class AsyncModelContext:
#     """
#     Holds coroutine-local context for a model instance.

#     Attributes:
#         transaction: Optional active transaction for this context
#     """

#     transaction: "AsyncAccessorContextProtocol | None" = None


# class AsyncAppModel(AppCommonModel, AsyncApp):
#     @property
#     def context(self) -> "AsyncAccessorContextProtocol":
#         """
#         Get current context for operations.

#         Returns either active transaction or direct state access
#         based on whether this coroutine is in a transaction.

#         Returns:
#             Current accessor context
#         """
#         if not hasattr(self, "_context_var"):
#             self._context_var = ContextVar(f"model_context_{id(self)}", default=AsyncModelContext())

#         ctx = self._context_var.get()
#         if ctx.transaction is not None:
#             return ctx.transaction
#         return self.state

#     def _initialize_model_descriptors(self) -> None:
#         """
#         Init model items
#         """
#         for name, value in self.__class__.__dict__.items():
#             if hasattr(self, name):
#                 continue

#             if isinstance(value, ModelDescriptor):
#                 setattr(self, name, AsyncModelValue(self, name))

#     @asynccontextmanager  # type: ignore
#     async def model_transaction(self) -> AsyncContextManager[Self]:  # type: ignore
#         """
#         Start a new transaction.

#         The transaction is coroutine-local and will not affect
#         other coroutines accessing the same model instance.

#         Returns:
#             Self for method chaining

#         Raises:
#             ModelError: If transaction already active in this coroutine
#         """
#         # Get current context
#         ctx = self._context_var.get()
#         if ctx.transaction is not None:
#             raise ModelTransactionError("Transaction already active in this coroutine")

#         # Create new transaction and update context
#         transaction = await self.state.begin_transaction()
#         token = self._context_var.set(AsyncModelContext(transaction=transaction))  # type: ignore
#         # TODO: Fix type ignore. transactions do not have [un]subscribe method

#         try:
#             yield self  # type: ignore
#             await transaction.commit()
#         except Exception:
#             # Rollback on any error
#             await transaction.rollback()
#             raise
#         finally:
#             # Always restore previous context
#             self._context_var.reset(token)
