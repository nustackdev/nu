from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait

from loomi.expression import Context, Expression, ExpressionError, ExpressionValue
from loomistd.app import SyncApp

from .logger import logger

__all__ = [
    "Sequence",
    "Parallel",
    "Loop",
]


class Loop(Expression[SyncApp]):
    """
    Execute an expression repeatedly while a condition is true.

    This expression evaluates a condition (which can be a direct value, state path,
    or state query) and continues executing the child expression as long as the
    condition evaluates to a truthy value.

    Args:
        condition: Condition to evaluate (ExpressionValue - can be direct value,
                  state path, or state query)
        expression: Expression to execute on each iteration

    Examples:
        ```python
        # Loop with direct boolean value
        Loop(True, Print("This will loop forever"))

        # Loop with state path condition
        Loop(("config", "keep_running"), ProcessData())

        # Loop with state query condition
        Loop(Query("users").count() > 0, ProcessUsers())
        ```
    """

    def __init__(self, app, /, condition: ExpressionValue, expression: Expression, **kwargs):
        super().__init__(app, **kwargs)
        self.condition = condition
        self.expression = expression

    def do_evaluate(self, context: "Context") -> None:
        """Execute the child expression while the condition is true."""
        iteration_count = 0

        logger.info(
            f"Starting loop evaluation in {self.readable_name}",
            extra={
                "condition_type": type(self.condition).__name__,
                "child_expression_type": type(self.expression).__name__,
            },
        )

        try:
            while True:
                if self.is_cancelled(context):
                    logger.info("Loop evaluation is cancelled, skipping execution")
                    return

                # Evaluate condition using snapshot for read-only access
                with self.app.state.tree.snapshot() as snapshot:
                    condition_result = self._resolve_value(
                        self.condition, self.app.state.tree, snapshot, context
                    )

                # Check if condition is truthy
                if not condition_result:
                    logger.info(
                        "Loop condition evaluated to falsy, stopping loop",
                        extra={
                            "iteration_count": iteration_count,
                            "condition_result": condition_result,
                        },
                    )
                    break

                # Execute the child expression
                logger.debug(
                    f"Executing loop iteration {iteration_count}",
                    extra={
                        "condition_result": condition_result,
                        "child_expression_type": type(self.expression).__name__,
                    },
                )

                child_context = self._create_child_context(
                    context,
                    child_expression=self.expression,
                )
                self.expression.evaluate(child_context)
                iteration_count += 1

                logger.debug(
                    f"Completed loop iteration {iteration_count - 1}",
                    extra={"total_iterations": iteration_count},
                )

        except Exception as e:
            logger.error(
                f"Loop failed at iteration {iteration_count}",
                extra={
                    "iteration_count": iteration_count,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            raise

        logger.info(
            "Loop completed successfully",
            extra={
                "total_iterations": iteration_count,
                "expression_type": type(self.expression).__name__,
            },
        )


class Sequence(Expression[SyncApp]):
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
        app,
        expr: Expression,
        /,
        *exprs: Expression,
        **kwargs,
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

        super().__init__(app, **kwargs)

        self.children = all_exprs

    def do_evaluate(self, context: "Context") -> None:
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
                    },
                )

                try:
                    child_context = self._create_child_context(
                        context,
                        child_expression=child,
                        child_index=i,
                    )
                    child.evaluate(child_context)
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
                    "completed_count": completed_count,
                },
            )

        except Exception:
            logger.warning(
                "Sequence expression terminated early",
                extra={
                    "expression_count": len(self.children),
                    "completed_count": completed_count,
                },
            )
            raise


class Parallel(Expression[SyncApp]):
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
        app,
        expr: Expression,
        /,
        *exprs: Expression,
        max_concurrency: int = -1,
        **kwargs,
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
            **kwargs: Additional keyword arguments for error handling

        Raises:
            ValueError: If max_concurrency is invalid
        """
        super().__init__(app, **kwargs)

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

    def do_evaluate(self, context: "Context") -> None:
        """
        Evaluate all child expressions in parallel with configurable concurrency.

        Executes child expressions concurrently using a ThreadPoolExecutor,
        respecting the max_concurrency setting.

        Args:
            app: The application environment
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
                    child_context = self._create_child_context(
                        context,
                        child_expression=child,
                        child_index=i,
                    )
                    future = executor.submit(child.evaluate, child_context)
                    futures.append(future)

                logger.debug(
                    "All child expressions submitted, waiting for completion",
                    extra={
                        "futures_count": len(futures),
                        "max_workers": max_workers,
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


class If(Expression[SyncApp]):
    """
    Conditionally execute an expression if a condition is truthy.

    This expression evaluates a condition and only executes the provided expression
    if the condition evaluates to a Python truthy value (True, non-zero numbers,
    non-empty strings, non-empty collections, etc.).

    Args:
        condition: ExpressionValue to evaluate for truthiness
        expression: Expression to execute if condition is truthy

    Examples:
        ```python
        # Simple boolean condition
        If(self, True, Print(self, "This will execute"))
        If(self, False, Print(self, "This won't execute"))

        # State path condition
        If(self, Path().is_ready, ProcessTask(self))

        # Complex condition from state
        If(
            self,
            Path().user.is_authenticated,
            Sequence(
                self,
                Print(self, "User is logged in"),
                LoadUserData(self)
            )
        )

        # Number condition (0 is falsy, anything else is truthy)
        If(self, Path().error_count, SendAlert(self))

        # String condition (empty string is falsy)
        If(self, Path().username, WelcomeUser(self))
        ```
    """

    def __init__(
        self,
        app,
        condition: ExpressionValue,
        expression: Expression,
        otherwise: Expression | None = None,
        **kwargs,
    ):
        super().__init__(app, **kwargs)
        self.condition = condition
        self.expression = expression
        self.otherwise = otherwise

    def do_evaluate(self, context: "Context") -> None:
        """Evaluate condition and execute expression if truthy."""
        try:
            # Use snapshot for read-only condition evaluation
            with self.app.state.tree.snapshot() as snapshot:
                # Resolve the condition value
                condition_value = self._resolve_value(
                    self.condition, self.app.state.tree, snapshot, context
                )
                print(f"Condition value: {condition_value}")

            # Check if condition is truthy using Python's bool() conversion
            if condition_value:
                # Execute the expression
                self.expression.evaluate(
                    self._create_child_context(
                        context,
                        child_expression=self.expression,
                    )
                )
            elif self.otherwise is not None:
                # Execute the otherwise expression
                self.otherwise.evaluate(
                    self._create_child_context(
                        context,
                        child_expression=self.otherwise,
                        child_index="otherwise",
                    )
                )

        except Exception as e:
            raise ExpressionError(
                f"Failed to evaluate If condition {self.condition}: {e}",
                expression=self,
                cause=e,
            )
