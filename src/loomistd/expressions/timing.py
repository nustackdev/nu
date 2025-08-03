from __future__ import annotations

import time

from loomi.app import AppBase
from loomi.evaluator import Context, Expression, ExpressionError, ExpressionValue

from .logger import logger

__all__ = [
    "Delay",
]


class Delay(Expression):
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

    def __init__(self, duration: ExpressionValue, **kwargs):
        super().__init__(**kwargs)
        self.duration = duration

    def do_evaluate(self, app: AppBase, context: "Context") -> None:
        """Sleep for the specified duration."""
        # Use snapshot for read-only access to resolve duration
        with app.state.tree.snapshot() as snapshot:
            sleep_duration = self._resolve_value(self.duration, app.state.tree, snapshot, context)

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
