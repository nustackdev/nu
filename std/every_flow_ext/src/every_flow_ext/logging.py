"""Logging and debug flows."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from everyabc import Flow, Term


if TYPE_CHECKING:
    from everyabc import Context


__all__ = [
    "Debug",
    "Log",
]

logger = logging.getLogger("every_flow_ext")


class Log(Flow):
    """Leaf flow that logs a message with optional Term values.

    Example::

        Log("User count: {}", [user_count_ref])
        Log("Starting process", level="debug")
    """

    __slots__ = ("_level", "_message", "_values")

    def __init__(
        self,
        message: str,
        values: list[Any] | None = None,
        *,
        level: str = "info",
    ) -> None:
        """Initialize log flow.

        Args:
            message: Format string for the log message.
            values: Optional list of Terms or literals to format into message.
            level: Log level name (debug, info, warning, error, critical).
        """
        super().__init__()
        self._message = message
        self._values = values or []
        self._level = level

    def execute(self, ctx: Context) -> None:
        """Log the message with resolved values."""
        resolved = [v.execute(ctx) if isinstance(v, Term) else v for v in self._values]
        formatted = self._message.format(*resolved) if resolved else self._message
        log_level = getattr(logging, self._level.upper(), logging.INFO)
        logger.log(log_level, formatted)


class Debug(Flow):
    """Leaf flow that prints debug output with labels.

    Example::

        Debug(x_ref, y_ref, labels=["x", "y"])
        # prints: [DEBUG] x=42 y=17
    """

    __slots__ = ("_labels", "_prefix", "_values")

    def __init__(
        self,
        *values: Any,
        labels: list[str] | None = None,
        prefix: str = "[DEBUG]",
    ) -> None:
        """Initialize debug flow.

        Args:
            *values: Terms or literals to display.
            labels: Optional labels for each value.
            prefix: Output prefix string.
        """
        super().__init__()
        self._values = values
        self._labels = labels
        self._prefix = prefix

    def execute(self, ctx: Context) -> None:
        """Print debug output."""
        parts = [self._prefix]
        for i, v in enumerate(self._values):
            resolved = v.execute(ctx) if isinstance(v, Term) else v
            label = self._labels[i] if self._labels and i < len(self._labels) else f"v{i}"
            parts.append(f"{label}={resolved!r}")
        print(" ".join(parts))  # noqa: T201
