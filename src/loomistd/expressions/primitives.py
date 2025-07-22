from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait
from typing import TYPE_CHECKING, Awaitable, Callable, Optional

from loomi.behaviors.evaluator.expressions import ErrorBehavior, Expression, ExpressionError

from .logger import logger

if TYPE_CHECKING:
    from loomi.behaviors.evaluator import Evaluator
    from loomi.behaviors.evaluator.context import Context

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
            ExpressionError: If func is not a callable
        """
        # Validate that func is callable
        if not callable(func):
            error_msg = f"func must be callable, got {type(func).__name__}"
            logger.error(
                "Invalid function provided to Function expression",
                extra={
                    "func_type": type(func).__name__,
                    "func_repr": repr(func),
                },
            )
            raise ExpressionError(error_msg)

        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        self._func = func

    def do_evaluate(self, evaluator: "Evaluator", context: "Context") -> None:
        """
        Evaluate the Function expression by executing the wrapped function.

        Args:
            evaluator: The evaluator environment
            context: The execution context
        """
        function_name = getattr(self._func, "__name__", "anonymous")

        try:
            # Execute the function using the evaluator's fleet
            future = evaluator.execute(self._func, context)

            # Wait for completion and get result
            result = future.result()

            logger.info(
                "Function expression completed successfully",
                extra={
                    "function_name": function_name,
                    "expression_id": id(self),
                    "result_type": type(result).__name__ if result is not None else "None",
                },
            )

        except Exception as e:
            logger.error(
                "Function expression execution failed",
                extra={
                    "function_name": function_name,
                    "expression_id": id(self),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            # Re-raise the exception to be handled by the evaluator
            raise


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
            ExpressionError: If any provided expression is not an Expression instance
        """
        # Validate all expressions
        all_exprs = (expr,) + exprs
        for i, expression in enumerate(all_exprs):
            if not isinstance(expression, Expression):
                error_msg = f"All arguments must be Expression instances, got {type(expression).__name__} at position {i}"
                logger.error(
                    "Invalid expression provided to Sequence",
                    extra={
                        "position": i,
                        "expression_type": type(expression).__name__,
                        "total_expressions": len(all_exprs),
                    },
                )
                raise ExpressionError(error_msg)

        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        self.children = all_exprs

    def do_evaluate(self, evaluator: "Evaluator", context: "Context") -> None:
        """
        Evaluate all child expressions in sequential order.

        Each expression is evaluated one after another, waiting for completion
        before proceeding to the next.

        Args:
            evaluator: The evaluator environment
            context: The execution context
        """
        completed_count = 0

        try:
            for i, child in enumerate(self.children):
                logger.debug(
                    "Evaluating child expression in sequence",
                    extra={
                        "child_index": i,
                        "child_type": type(child).__name__,
                        "child_id": id(child),
                        "sequence_id": id(self),
                    },
                )

                try:
                    child.evaluate(evaluator, context)
                    completed_count += 1

                    logger.debug(
                        "Child expression completed successfully",
                        extra={
                            "child_index": i,
                            "child_type": type(child).__name__,
                            "completed_count": completed_count,
                            "total_count": len(self.children),
                        },
                    )

                except Exception as e:
                    logger.error(
                        "Child expression failed in sequence",
                        extra={
                            "child_index": i,
                            "child_type": type(child).__name__,
                            "completed_count": completed_count,
                            "total_count": len(self.children),
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                        },
                        exc_info=True,
                    )
                    # Re-raise to let the evaluator handle error behavior
                    raise

            logger.info(
                "Sequence expression completed successfully",
                extra={
                    "expression_count": len(self.children),
                    "expression_id": id(self),
                    "completed_count": completed_count,
                },
            )

        except Exception:
            logger.warning(
                "Sequence expression terminated early",
                extra={
                    "expression_count": len(self.children),
                    "expression_id": id(self),
                    "completed_count": completed_count,
                },
            )
            raise


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
            error_msg = f"Invalid max_concurrency: {max_concurrency}. Must be >= -1"
            logger.error(
                "Invalid max_concurrency for Parallel expression",
                extra={
                    "max_concurrency": max_concurrency,
                    "valid_range": ">= -1",
                },
            )
            raise ValueError(error_msg)

        # Validate all expressions
        all_exprs = (expr,) + exprs
        for i, expression in enumerate(all_exprs):
            if not isinstance(expression, Expression):
                error_msg = f"All arguments must be Expression instances, got {type(expression).__name__} at position {i}"
                logger.error(
                    "Invalid expression provided to Parallel",
                    extra={
                        "position": i,
                        "expression_type": type(expression).__name__,
                        "total_expressions": len(all_exprs),
                    },
                )
                raise ExpressionError(error_msg)

        self._max_concurrency = max_concurrency
        self.children = all_exprs

    def do_evaluate(self, evaluator: "Evaluator", context: "Context") -> None:
        """
        Evaluate all child expressions in parallel with configurable concurrency.

        Executes child expressions concurrently using a ThreadPoolExecutor,
        respecting the max_concurrency setting.

        Args:
            evaluator: The evaluator environment
            context: The execution context
        """
        # Calculate effective max workers
        max_workers = self._max_concurrency if self._max_concurrency > 0 else len(self.children)

        logger.info(
            "Starting Parallel expression evaluation",
            extra={
                "expression_count": len(self.children),
                "max_concurrency": self._max_concurrency,
                "effective_max_workers": max_workers,
                "expression_id": id(self),
                "expression_types": [type(e).__name__ for e in self.children],
            },
        )

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all child expressions for parallel execution
                futures = []
                for i, child in enumerate(self.children):
                    logger.debug(
                        "Submitting child expression for parallel execution",
                        extra={
                            "child_index": i,
                            "child_type": type(child).__name__,
                            "child_id": id(child),
                            "parallel_id": id(self),
                        },
                    )
                    future = executor.submit(child.evaluate, evaluator, context)
                    futures.append(future)

                logger.debug(
                    "All child expressions submitted, waiting for completion",
                    extra={
                        "futures_count": len(futures),
                        "max_workers": max_workers,
                        "parallel_id": id(self),
                    },
                )

                # Wait for all futures to complete
                wait(futures)

                # Check for exceptions in completed futures
                exceptions = []
                for i, future in enumerate(futures):
                    try:
                        future.result()  # This will raise if the future had an exception
                        logger.debug(
                            "Child expression completed successfully",
                            extra={
                                "child_index": i,
                                "child_type": type(self.children[i]).__name__,
                                "parallel_id": id(self),
                            },
                        )
                    except Exception as e:
                        logger.error(
                            "Child expression failed in parallel execution",
                            extra={
                                "child_index": i,
                                "child_type": type(self.children[i]).__name__,
                                "error_type": type(e).__name__,
                                "error_message": str(e),
                                "parallel_id": id(self),
                            },
                            exc_info=True,
                        )
                        exceptions.append((i, e))

                # If any exceptions occurred, raise the first one
                if exceptions:
                    first_exception_index, first_exception = exceptions[0]
                    logger.error(
                        "Parallel expression failed due to child expression errors",
                        extra={
                            "failed_count": len(exceptions),
                            "total_count": len(self.children),
                            "first_failure_index": first_exception_index,
                            "parallel_id": id(self),
                        },
                    )
                    raise first_exception

                logger.info(
                    "Parallel expression completed successfully",
                    extra={
                        "expression_count": len(self.children),
                        "max_workers": max_workers,
                        "expression_id": id(self),
                    },
                )

        except Exception as e:
            logger.error(
                "Parallel expression execution failed",
                extra={
                    "expression_count": len(self.children),
                    "max_workers": max_workers,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "expression_id": id(self),
                },
                exc_info=True,
            )
            raise
