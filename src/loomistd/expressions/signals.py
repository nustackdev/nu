"""
GracefulInterruption Expression

Provides graceful interruption handling for system signals (SIGINT, SIGTERM).
Wraps a child expression and cancels it when signals are received.
"""

from __future__ import annotations

import signal
import threading
from typing import Any

from loomi.expression import Context, Expression

from .logger import logger

__all__ = [
    "GracefulInterruption",
]


class GracefulInterruption(Expression):
    """
    Expression that provides graceful interruption handling for its child expression.

    Sets up signal handlers for SIGINT (Ctrl+C) and SIGTERM, and cancels the child
    expression when these signals are received.

    Example:
        ```python
        # Wrap main application logic with graceful interruption
        main_app = MainApplication(app)

        graceful_app = GracefulInterruption(
            app,
            expression=main_app
        )

        # When Ctrl+C is pressed, main_app will be cancelled gracefully
        graceful_app.evaluate()
        ```
    """

    def __init__(self, app, expression: Expression, **kwargs):
        """
        Initialize the graceful interruption wrapper.

        Args:
            expression: The expression to wrap and protect
            **kwargs: Additional arguments passed to Expression.__init__
        """
        super().__init__(app, **kwargs)
        self.expression = expression
        self._original_handlers: dict[int, Any] = {}
        self._child_context: Context | None = None
        self._signal_received = threading.Event()

    def do_evaluate(self, context: Context) -> None:
        """
        Execute the child expression with graceful interruption support.

        Args:
            context: The execution context
        """
        # Set up signal handlers
        self._setup_signal_handlers()

        try:
            logger.info(
                f"Starting graceful execution of {self.expression.readable_name}",
                extra={"child_type": type(self.expression).__name__},
            )

            self._child_context = self._create_child_context(
                context,
                child_expression=self.expression,
            )
            # Execute the child expression
            self.expression.evaluate(self._child_context)

            logger.info(
                "Graceful execution completed successfully",
                extra={"child_type": type(self.expression).__name__},
            )

        except Exception as e:
            if self._signal_received.is_set():
                logger.info(
                    f"Graceful execution interrupted by signal: {e}",
                    extra={"child_type": type(self.expression).__name__},
                )
            else:
                logger.error(
                    f"Graceful execution failed: {e}",
                    extra={"child_type": type(self.expression).__name__},
                )
            raise

        finally:
            # Restore original signal handlers
            self._restore_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful interruption."""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")

            # Mark that signal was received
            self._signal_received.set()

            # Cancel the child expression
            if self._child_context is not None:
                self.expression.cancel(self._child_context, f"Signal {signum} received")

        # Store original handlers and set new ones
        for sig in [signal.SIGINT, signal.SIGTERM]:
            try:
                self._original_handlers[sig] = signal.signal(sig, signal_handler)
                logger.info(f"Registered graceful interruption handler for signal {sig}")
            except (ValueError, OSError) as e:
                logger.warning(f"Could not register handler for signal {sig}: {e}")

    def _restore_signal_handlers(self) -> None:
        """Restore original signal handlers."""
        for sig, original_handler in self._original_handlers.items():
            try:
                signal.signal(sig, original_handler)
                logger.info(f"Restored original handler for signal {sig}")
            except (ValueError, OSError) as e:
                logger.warning(f"Could not restore handler for signal {sig}: {e}")

        self._original_handlers.clear()
