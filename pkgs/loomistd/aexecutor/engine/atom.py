"""
Atomic operation execution engine.

This module provides the execution engine capabilities for atomic operations
such as Function and (in the future) App operations. Atomic operations are
the fundamental building blocks that don't contain child operations.
"""

from __future__ import annotations

from loomi.interfaces.state.type_vars import StateDictT, StateT

from ..context.context import Context
from ..operations.function import Function
from .base import EngineBase


class AtomEngine(EngineBase[StateT, StateDictT]):
    """
    Engine mixin for executing atomic operations.

    Provides implementation for executing Function operations
    and (in the future) App operations. These operations represent
    the fundamental building blocks of workflows.
    """

    async def exec_function(
        self, operation: Function[StateDictT], context: Context[StateDictT]
    ) -> None:
        """
        Execute a Function operation.

        Executes the callable function defined in the operation, providing it
        with the context. Handles both synchronous and asynchronous functions.

        Args:
            operation: The Function operation to execute
            context: The execution context

        Raises:
            Exception: Any exception raised by the function
        """
        # Get function metadata for logging
        func_name = getattr(operation._func, "__name__", "<anonymous>")
        self.logger.debug(f"Executing function {func_name}")

        # Execute the function through the task executor service
        await self.execute_task(operation._func, context)
