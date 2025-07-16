"""
Atomic expression execution engine.

This module provides the execution engine capabilities for atomic expressions
such as Function and (in the future) App expressions. Atomic expressions are
the fundamental building blocks that don't contain child expressions.
"""

from __future__ import annotations

from ..context import Context
from ..expressions import Function
from .base import EngineBase


class AtomEngine(EngineBase):
    """
    Engine mixin for executing atomic expressions.

    Provides implementation for executing Function expressions
    and (in the future) App expressions. These expressions represent
    the fundamental building blocks of workflows.
    """

    def exec_function(self, expression: Function, context: Context) -> None:
        """
        Execute a Function expression.

        Executes the callable function defined in the expression, providing it
        with the context. Handles both synchronous and asynchronous functions.

        Args:
            expression: The Function expression to execute
            context: The execution context

        Raises:
            Exception: Any exception raised by the function
        """
        # Get function metadata for logging
        func_name = getattr(expression._func, "__name__", "<anonymous>")
        self.logger.debug(f"Executing function {func_name}")

        # Execute the function through the task executor service
        expression._func(context)
