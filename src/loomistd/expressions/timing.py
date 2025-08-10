from __future__ import annotations

import threading
import time

from loomi.expression import Context, Expression, ExpressionError, ExpressionValue, create_component
from loomistd.app import SyncApp

from .logger import logger

__all__ = [
    "Delay",
]


class Delay(Expression[SyncApp]):
    """
    Pause execution for a specified duration.

    This expression pauses execution using time.sleep() for the specified
    number of seconds. The duration can be a direct value or resolved from state.

    Args:
        duration: Duration to sleep in seconds (can be direct value or state path)

    Examples:
        ```python
        # Sleep for 1 second
        Delay(1.0)

        # Sleep for duration from state
        Delay(("config", "polling_interval"))

        # Use in sequences for timed operations
        Sequence(
            Print("Starting process..."),
            Delay(2.0),
            Print("Process started after delay")
        )
        ```
    """

    def __init__(self, app, duration: ExpressionValue, **kwargs):
        super().__init__(app, **kwargs)
        self.duration = duration

    def do_evaluate(self, context: "Context") -> None:
        """Sleep for the specified duration."""
        # Use snapshot for read-only access to resolve duration
        with self.app.state.tree.snapshot() as snapshot:
            sleep_duration = self._resolve_value(
                self.duration, self.app.state.tree, snapshot, context
            )

        # Validate duration type
        if not isinstance(sleep_duration, (int, float)):
            raise ExpressionError(
                f"Sleep duration must be a number (got {type(sleep_duration).__name__}: {sleep_duration})",
                expression=self,
            )

        # Validate duration value
        if sleep_duration < 0:
            raise ExpressionError(
                f"Sleep duration must be non-negative (got {sleep_duration})",
                expression=self,
            )

        logger.info(
            f"Starting delay for {sleep_duration} seconds",
            extra={
                "duration": sleep_duration,
                "duration_type": type(sleep_duration).__name__,
            },
        )

        start_time = time.perf_counter()

        try:
            time.sleep(sleep_duration)
            actual_duration = time.perf_counter() - start_time

            logger.info(
                "Delay completed",
                extra={
                    "requested_duration": sleep_duration,
                    "actual_duration": actual_duration,
                    "duration_diff": actual_duration - sleep_duration,
                },
            )

        except Exception as e:
            actual_duration = time.perf_counter() - start_time
            logger.error(
                f"Delay interrupted after {actual_duration:.3f} seconds",
                extra={
                    "requested_duration": sleep_duration,
                    "actual_duration": actual_duration,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            raise


class Timeout(Expression[SyncApp]):
    """
    Expression that executes a child expression with a timeout.

    If the child expression doesn't complete within the specified time,
    it will be cancelled via the cancellation token mechanism.

    Example:
        ```python
        # Execute an expression with a 30-second timeout
        long_task = SomeSlowExpression(app)

        timed_task = Timeout(
            app,
            child_expression=long_task,
            timeout_seconds=30.0,
        )

        timed_task.evaluate()  # Will cancel long_task if it takes > 30 seconds
        ```
    """

    def __init__(
        self,
        app: SyncApp,
        *,
        expression: Expression,
        timeout_seconds: float,
        on_timeout: Expression | None = None,
        **kwargs,
    ):
        """
        Initialize the timeout wrapper.

        Args:
            expression: The expression to execute with timeout
            timeout_seconds: Maximum execution time in seconds
            on_timeout: Optional callback to execute when timeout occurs
            **kwargs: Additional arguments passed to Expression.__init__
        """
        super().__init__(app, **kwargs)
        self.expression = expression
        self.timeout_seconds = timeout_seconds
        self.on_timeout = on_timeout

    def do_evaluate(self, context: Context) -> None:
        """
        Execute the child expression with timeout enforcement.

        Args:
            context: The execution context
        """
        # Create a child context with its own cancellation token
        child_context = context.create_child_context(create_component(self.expression))
        # Track completion
        completed = threading.Event()
        exception_holder: list[Exception | None] = [None]  # Mutable container for exception

        def execute_child():
            """Execute the child expression in a separate thread."""
            try:
                self.expression.evaluate(child_context)
                completed.set()
            except Exception as e:
                exception_holder[0] = e
                completed.set()

        # Start the child expression in a separate thread
        child_thread = threading.Thread(target=execute_child, daemon=True)
        child_thread.start()

        try:
            # Wait for completion or timeout
            if completed.wait(timeout=self.timeout_seconds):
                # Child completed (successfully or with error)
                if exception_holder[0] is not None:
                    # Child failed, re-raise the exception
                    raise exception_holder[0]
                else:
                    logger.info(
                        f"Child expression {self.expression.readable_name} completed within timeout",
                        extra={"timeout_seconds": self.timeout_seconds},
                    )
            else:
                # Timeout occurred
                logger.warning(
                    f"Child expression {self.expression.readable_name} timed out",
                    extra={"timeout_seconds": self.timeout_seconds},
                )

                # Cancel the child expression
                self.expression.cancel(child_context, "timeout")

                # Execute timeout callback if provided
                if self.on_timeout:
                    try:
                        self.on_timeout.evaluate(context)
                    except Exception as callback_error:
                        logger.error(f"Timeout callback failed: {callback_error}", exc_info=True)

        finally:
            # Ensure child thread cleanup
            if child_thread.is_alive():
                self.expression.cancel(child_context, "timeout")
                # Give the thread a moment to respond to cancellation
                child_thread.join(timeout=1.0)
