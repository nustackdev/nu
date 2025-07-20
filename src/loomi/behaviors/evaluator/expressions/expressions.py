from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait
from typing import TYPE_CHECKING, Awaitable, Callable, Optional

from .base import Expression
from .types import ErrorBehavior

if TYPE_CHECKING:
    from ..context import Context
    from ..evaluator import Evaluator

__all__ = [
    "Function",
    "Sequence",
    "Parallel",
]


class Function(Expression):
    """
    Executes a callable function or method.

    This is the most basic expression, allowing arbitrary async callables
    to be used within the expressions framework.

    Args:
        func: The function to execute
        error_behavior: How to handle errors that occur during execution
        on_fail: Expression to execute when an error occurs

    Examples:
        >>> async def greet(context):
        ...     print(f"Hello from path {context.path}")
        ...
        >>> expr = Function(greet)
    """

    def __init__(
        self,
        func: Callable[[Context], Awaitable[None] | None],
        /,
        *,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Expression] = None,
    ):
        """
        Initialize the Function expression.

        Args:
            func: The function to execute
            error_behavior: How to handle errors that occur during execution
            on_fail: Expression to execute when an error occurs

        Raises:
            OperationConfigError: If func is not a callable
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        self._func = func

    def evaluate(self, evaluator: "Evaluator", context: "Context") -> None:
        res = evaluator.execute(self._func, context)
        res.result()


class Sequence(Expression):
    """
    Executes expressions in sequential order.

    This expression runs each child expression in sequence, waiting for
    each to complete before executing the next.

    Args:
        expr: The first expression to execute
        *exprs: Additional expressions to execute in sequence
        error_behavior: How to handle errors that occur during execution
        on_fail: Expression to execute when an error occurs

    Examples:
        >>> expr1 = Function(func1)
        >>> expr2 = Function(func2)
        >>> expr3 = Function(func3)
        >>> sequence = Sequence(expr1, expr2, expr3)
    """

    def __init__(
        self,
        expr: Expression,
        /,
        *exprs: Expression,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Expression] = None,
    ):
        """
        Initialize the Sequence expression.

        Args:
            expr: The first expression to execute
            *exprs: Additional expressions to execute in sequence
            error_behavior: How to handle errors that occur during execution
            on_fail: Expression to execute when an error occurs

        Raises:
            OperationConfigError: If no expressions are provided
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        self.children = (expr,) + exprs

    def evaluate(self, evaluator: "Evaluator", context: "Context") -> None:
        for child in self.children:
            child.evaluate(evaluator, context)


class Parallel(Expression):
    """
    Executes expressions concurrently.

    This expression runs child expressions in parallel, with configurable
    maximum concurrency. When max_concurrency is 1, it behaves like
    a Sequence. When negative, it runs all expressions with no limit.

    Args:
        expr: The first expression to execute
        *exprs: Additional expressions to execute in parallel
        max_concurrency: Maximum number of concurrent expressions
            - 1 means sequential execution (same as Sequence)
            - >1 means limit to N concurrent expressions
            - -1 or 0 means unlimited concurrency
        error_behavior: How to handle errors that occur during execution
        on_fail: Expression to execute when an error occurs

    Examples:
        >>> expr1 = Function(func1)
        >>> expr2 = Function(func2)
        >>> expr3 = Function(func3)
        >>> parallel = Parallel(expr1, expr2, expr3, max_concurrency=2)
    """

    def __init__(
        self,
        expr: Expression,
        /,
        *exprs: Expression,
        max_concurrency: int = -1,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Expression | None = None,
    ):
        """
        Initialize the Parallel expression.

        Args:
            expr: The first expression to execute
            *exprs: Additional expressions to execute in parallel
            max_concurrency: Maximum number of concurrent expressions
                - 1 means sequential execution (same as Sequence)
                - >1 means limit to N concurrent expressions
                - -1 or 0 means unlimited concurrency
            error_behavior: How to handle errors that occur during execution
            on_fail: Expression to execute when an error occurs

        Raises:
            ValueError: If max_concurrency is invalid
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        # Validate max_concurrency
        if max_concurrency < -1:
            raise ValueError(f"Invalid max_concurrency: {max_concurrency}. Must be >= -1")

        self._max_concurrency = max_concurrency
        self.children = (expr,) + exprs

    def evaluate(self, evaluator: "Evaluator", context: "Context") -> None:
        max_workers = self._max_concurrency if self._max_concurrency > 0 else len(self.children)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(child.evaluate, evaluator, context) for child in self.children
            ]
            wait(futures)
