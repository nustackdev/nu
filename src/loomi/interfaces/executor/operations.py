from __future__ import annotations

from typing import Awaitable, Callable, Protocol, runtime_checkable

from .type_vars import ContextT_co, OperationT
from .types import ErrorBehavior


@runtime_checkable
class OperationProtocol(Protocol[OperationT, ContextT_co]):
    @property
    def parent(self) -> OperationT | None: ...

    @parent.setter
    def parent(self, parent: OperationT | None) -> None: ...

    @property
    def children(self) -> tuple[OperationT, ...]: ...

    @children.setter
    def children(self, children: tuple[OperationT, ...]) -> None: ...


@runtime_checkable
class FunctionOperationProtocol(OperationProtocol[OperationT, ContextT_co], Protocol):
    """
    Executes a callable function or method.

    This is the most basic operation, allowing arbitrary async callables
    to be used within the operations framework.

    Args:
        func: The function to execute
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

    Examples:
        >>> async def greet(context):
        ...     print(f"Hello from path {context.path}")
        ...
        >>> op = Function(greet)
    """

    def __init__(
        self,
        func: Callable[["ContextT_co"], Awaitable[None]] | Callable[["ContextT_co"], None],
        /,
        *,
        error_behavior: ErrorBehavior = "fail",
        on_fail: OperationT | None = None,
    ) -> None:
        """
        Initialize the Function operation.

        Args:
            func: The function to execute
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

        Raises:
            OperationConfigError: If func is not a callable
        """


@runtime_checkable
class SequenceOperationProtocol(OperationProtocol[OperationT, ContextT_co], Protocol):
    """
    Executes operations in sequential order.

    This operation runs each child operation in sequence, waiting for
    each to complete before executing the next.

    Args:
        *ops: The operations to execute in sequence
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

    Examples:
        >>> op1 = Function(func1)
        >>> op2 = Function(func2)
        >>> op3 = Function(func3)
        >>> sequence = Sequence(op1, op2, op3)
    """

    def __init__(
        self,
        op: OperationT,
        /,
        *ops: OperationT,
        error_behavior: ErrorBehavior = "fail",
        on_fail: OperationT | None = None,
    ) -> None:
        """
        Initialize the Sequence operation.

        Args:
            op: The first operation to execute
            *ops: Additional operations to execute in sequence
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

        Raises:
            OperationConfigError: If no operations are provided
        """
