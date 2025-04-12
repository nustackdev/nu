from typing import TYPE_CHECKING, Awaitable, Callable, Literal, Protocol, TypeVar

from .operation import AsyncOperationProtocol, ContextProtocol

if TYPE_CHECKING:
    from loomi.app import AsyncApp

error_behaviors = Literal["fail", "continue"]
ContextT_contra = TypeVar("ContextT_contra", bound=ContextProtocol, contravariant=True)


class AppOperationProtocol(AsyncOperationProtocol[ContextT_contra], Protocol):
    """
    Executes a Loomi app as an operation.

    This operation adapts a Loomi app to the operations framework,
    allowing apps to be composed within workflows.

    Args:
        app: The app to execute
        state_path: Optional path to mount the app's state
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

    Examples:
        >>> from loomi.app import App as LApp
        >>> my_app = LApp()
        >>> op = App(my_app, state_path=("apps", "my_app"))
    """

    def __init__(
        self,
        app: "AsyncApp",
        /,
        *,
        state_path: tuple[str, ...] | str | None = None,
        error_behavior: error_behaviors = "fail",
        on_fail: AsyncOperationProtocol[ContextT_contra] | None = None,
    ):
        """
        Initialize the Function operation.

        Args:
            func: The function to execute
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

        Raises:
            OperationConfigError: If func is not a callable
        """


class FunctionOperationProtocol(AsyncOperationProtocol[ContextT_contra], Protocol):
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
        func: Callable[[ContextT_contra], Awaitable[None]],
        /,
        *,
        error_behavior: error_behaviors = "fail",
        on_fail: AsyncOperationProtocol[ContextT_contra] | None = None,
    ):
        """
        Initialize the Function operation.

        Args:
            func: The function to execute
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

        Raises:
            OperationConfigError: If func is not a callable
        """


class SequenceOperationProtocol(AsyncOperationProtocol[ContextT_contra], Protocol):
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
        op: AsyncOperationProtocol[ContextT_contra],
        /,
        *ops: AsyncOperationProtocol[ContextT_contra],
        error_behavior: error_behaviors = "fail",
        on_fail: AsyncOperationProtocol[ContextT_contra] | None = None,
    ):
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
