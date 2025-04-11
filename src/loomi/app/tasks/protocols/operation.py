"""
Protocols defining the interfaces for operations and related components.

This module contains the Protocol definitions that form the contract
between different parts of the operations framework.
"""

from typing import Protocol, TypeVar

__all__ = [
    "AsyncOperationProtocol",
    "ContextProtocol",
]


class ContextProtocol(Protocol):
    """
    Protocol defining the interface for a context.
    Contexts provide access to state and services during operation execution.
    """

    pass


ContextT_contra = TypeVar("ContextT_contra", bound=ContextProtocol, contravariant=True)


class AsyncOperationProtocol(Protocol[ContextT_contra]):
    """
    Protocol defining the interface for all operations.

    Operations are declarative structures that define what work should be done.
    They are executed by the execution engine and its services.
    """

    @property
    def children(self) -> tuple["AsyncOperationProtocol[ContextT_contra]", ...]:
        """
        Get all child operations of this operation.

        Returns:
            Tuple of child operations, or empty tuple if none
        """
        ...

    async def execute(self, context: "ContextT_contra") -> None:
        """
        Execute the operation within the given context.

        This method is called by the execution engine when the operation
        is to be executed as part of a workflow.

        Args:
            context: Execution context providing access to state and services
        """
        ...
