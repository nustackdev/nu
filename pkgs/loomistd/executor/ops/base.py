"""
Base class for all operations.

This module provides the Operation class, which all operations
should inherit from to ensure consistent behavior.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Awaitable, Callable, final

from loomi.app.tasks.protocols import AsyncOperationProtocol

from ..context import Context
from ..errors import wrap_error
from ..logger import log_operation_end, log_operation_error, log_operation_start
from ..types import error_behaviors
from .metadata import OperationMetadata


class Operation(ABC):
    """
    Base class for all operations.

    Implements common functionality for operations, including error handling,
    logging, and tracing. All operations should inherit from this class.

    Args:
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs
    """

    def __init__(
        self,
        *,
        error_behavior: error_behaviors = "fail",
        on_fail: Operation | None = None,
    ):
        """
        Initialize the operation.

        Args:
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs
        """
        if error_behavior not in ("fail", "continue"):
            raise ValueError(f"Invalid error_behavior: {error_behavior}")

        self._error_behavior = error_behavior
        self._on_fail = on_fail

    @property
    def metadata(self) -> OperationMetadata:
        """
        Get the operation's metadata.

        The metadata includes the operation's name, description, and any
        custom properties. By default, the name is the class name and
        the description is the class docstring.

        Returns:
            The operation metadata
        """
        return OperationMetadata(
            name=self.__class__.__name__,
            description=self.__doc__ or "",
            custom_properties={},
        )

    @property
    def children(self) -> tuple[Operation, ...]:
        """
        Get all child operations of this operation.

        By default, this includes only the on_fail operation if set.
        Subclasses should override this to include their own children.

        Returns:
            Tuple of child operations
        """
        if self._on_fail:
            return (self._on_fail,)
        return tuple()

    @final
    async def execute_task(
        self,
        func: Callable[[Context], Awaitable[None]],
        context: Context,
        timeout: float | None = None,
    ) -> None:
        """
        Execute a Python function as a managed task through the executor service.

        This helper method allows operations to delegate function execution to the
        task executor, ensuring proper task management, tracking, and lifecycle.

        Args:
            context: The execution context
            func: The async function to execute
            timeout: Optional timeout for the task execution

        Raises:
            RuntimeError: If no executor is available in the context
        """
        # Ensure executor is available
        if context.executor is None:
            raise RuntimeError(
                f"Operation {self.metadata.name} requires a task executor in the context"
            )

        # Execute the function through the task executor
        await context.executor.execute(func=func, context=context, timeout=timeout, wait=True)

    @final
    async def execute(self, context: Context) -> None:
        """
        Execute the operation within the given context.

        This method handles the execution lifecycle, including logging,
        tracing, and error handling. Subclasses should implement the
        _execute method to define their specific behavior.

        Args:
            context: Execution context providing access to state and services
        """
        log_operation_start(self.metadata.name, context.get_structural_path_str())

        # Record tracing event if tracing service is available
        if context.tracing:
            context.tracing.record_event(self, context, "start")

        try:
            # Execute the operation
            await self._execute(context)

            # Log and trace successful completion
            log_operation_end(self.metadata.name, context.get_structural_path_str())
            if context.tracing:
                context.tracing.record_event(self, context, "end")

        except Exception as e:
            # Log and trace error
            log_operation_error(self.metadata.name, e, context.get_structural_path_str())
            if context.tracing:
                context.tracing.record_event(
                    self, context, "error", {"error": str(e), "error_type": type(e).__name__}
                )

            # Execute on_fail operation if set
            if self._on_fail:
                fail_context = context.with_structural_path("on_fail")
                try:
                    await self._on_fail.execute(fail_context)
                except Exception as fail_e:
                    # Log and trace error in on_fail operation
                    log_operation_error(
                        f"{self.metadata.name}.on_fail",
                        fail_e,
                        fail_context.get_structural_path_str(),
                    )
                    if context.tracing:
                        context.tracing.record_event(
                            self._on_fail,
                            fail_context,
                            "error",
                            {"error": str(fail_e), "error_type": type(fail_e).__name__},
                        )

            # Handle error based on error_behavior
            if self._error_behavior == "fail":
                # Wrap and re-raise error
                wrapped = wrap_error(e, self, context)
                raise wrapped

    @abstractmethod
    async def _execute(self, context: Context) -> None:
        """
        Implementation of operation execution.

        This method should be implemented by subclasses to define the
        specific behavior of the operation.

        Args:
            context: Execution context providing access to state and services
        """
        pass


if TYPE_CHECKING:
    _: type[AsyncOperationProtocol] = Operation
