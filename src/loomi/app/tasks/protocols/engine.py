from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

from .operation import AsyncOperationProtocol, ContextProtocol

if TYPE_CHECKING:
    from loomi.app.state import AsyncStateProtocol

    from .operations import AppOperationProtocol, FunctionOperationProtocol


__all__ = [
    "AsyncEngineProtocol",
]

OperationT_contra = TypeVar("OperationT_contra", bound=AsyncOperationProtocol, contravariant=True)
ContextT = TypeVar("ContextT", bound=ContextProtocol)


class AsyncEngineProtocol(Protocol[OperationT_contra, ContextT]):
    """
    Protocol defining the interface for the execution engine.

    The execution engine is responsible for executing operations and
    providing them with context and services.
    """

    state: "AsyncStateProtocol"

    async def execute(
        self,
        operation: OperationT_contra,
        parent_context: ContextT | None = None,
    ) -> None:
        """
        Execute an operation.

        Creates a new context if no parent context is provided, or derives
        a child context from the parent if one is provided.

        Args:
            operation: The operation to execute
            path: Optional execution path, defaults to ["_"]
            parent_context: Optional parent context to derive from
        """
        ...

    Function: type[FunctionOperationProtocol[ContextT]]
    App: type[AppOperationProtocol[ContextT]]
