"""Input/Output flows.

This module provides flows for I/O operations:
- Print: Print messages to stdout
- Log: Structured logging with levels
- Debug: Quick debug output
"""

from __future__ import annotations

import logging
from typing import Any

import attrs

from every import Flow, Runtime, Term


__all__ = [
    "Debug",
    "Log",
    "Print",
]


@attrs.define
class Print[RuntimeT: Runtime](Flow[RuntimeT]):
    """Print a message or term result to stdout.

    Supports format string interpolation with Term values.
    """

    message: str = attrs.field(default="Print")
    values: object = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute print."""
        if self.values is not None:
            if not isinstance(self.values, list):
                values = [self.values]
            else:
                values = self.values

            with runtime.storage.context() as ctx:
                results = [
                    runtime.terms.execute_term(v, ctx=ctx) if isinstance(v, Term) else v
                    for v in values
                ]
            print(self.message.format(*results))  # noqa: T201
        else:
            print(self.message)  # noqa: T201


@attrs.define
class _Log[RuntimeT: Runtime](Flow[RuntimeT]):
    """Log a message with structured data.

    Logs to the everybase.flows logger at the specified level.
    Supports format string interpolation with Term values.

    Flow Building Pattern:
        Log provides structured logging that integrates with Python's
        logging system. Use it for production-grade observability.

        Log levels:
        - debug: Detailed diagnostic info
        - info: General operational info
        - warning: Warning conditions
        - error: Error conditions
        - critical: Critical conditions
    """

    level: str = attrs.field(default="info")
    message: str = attrs.field(default="")
    values: object | None = attrs.field(default=None)
    extra: dict[str, Term | Any] | None = attrs.field(default=None)
    logger_name: str = attrs.field(default="everybase.flows")

    async def run(self, runtime: RuntimeT) -> None:
        """Execute log."""
        # Resolve message values
        if self.values is not None:
            if not isinstance(self.values, list):
                values = [self.values]
            else:
                values = self.values

            with runtime.storage.context() as ctx:
                resolved_values = [
                    runtime.terms.execute_term(v, ctx=ctx) if isinstance(v, Term) else v
                    for v in values
                ]
            formatted_message = self.message.format(*resolved_values)
        else:
            formatted_message = self.message

        # Resolve extra data
        extra_data: dict[str, Any] = {}
        if self.extra:
            with runtime.storage.context() as ctx:
                for key, value in self.extra.items():
                    if isinstance(value, Term):
                        extra_data[key] = runtime.terms.execute_term(value, ctx=ctx)
                    else:
                        extra_data[key] = value

        # Add path info
        extra_data["flow_path"] = str(runtime.path)

        # Get log level
        log_level = getattr(logging, self.level.upper(), logging.INFO)

        # Log the message
        flow_logger = logging.getLogger(self.logger_name)
        flow_logger.log(log_level, formatted_message)


@attrs.define
class _Debug[RuntimeT: Runtime](Flow[RuntimeT]):
    """Quick debug output for development.

    Prints values with labels for quick debugging during development.
    Uses print() for immediate visibility (bypasses logging config).

    Flow Building Pattern:
        Debug is for quick development iteration. For production,
        use Log instead. Debug will show:
        - The flow path
        - Each value with its label or index
    """

    values: list[Term | Any] = attrs.field(factory=list)
    labels: list[str] | None = attrs.field(default=None)
    prefix: str = attrs.field(default="[DEBUG]")

    async def run(self, runtime: RuntimeT) -> None:
        """Execute debug output."""
        parts = [f"{self.prefix} path={runtime.path}"]

        with runtime.storage.context() as ctx:
            for i, value in enumerate(self.values):
                if isinstance(value, Term):
                    resolved = runtime.terms.execute_term(value, ctx=ctx)
                else:
                    resolved = value

                if self.labels and i < len(self.labels):
                    label = self.labels[i]
                else:
                    label = f"v{i}"

                parts.append(f"{label}={resolved!r}")

        print(" ".join(parts))  # noqa: T201


# =============================================================================
# Wrapper Functions
# =============================================================================


def Log(  # noqa: N802
    message: str,
    level: str = "info",
    values: object | None = None,
    extra: dict[str, Term | Any] | None = None,
    logger_name: str = "everybase.flows",
) -> _Log:
    """Log a message with structured data.

    Logs to everybase.flows logger at the specified level.

    Args:
        message: Log message (supports {} format placeholders)
        level: Log level (debug, info, warning, error, critical)
        values: Optional values for format placeholders
        extra: Optional extra data to include in log record

    Returns:
        Log flow

    Example:
        >>> Log("Processing item {}", values=[item_id.get()])
        >>> Log("User action", level="info", extra={"user_id": user.get()})
    """
    return _Log(
        level=level,
        message=message,
        values=values,
        extra=extra,
        logger_name=logger_name,
    )


def Debug(  # noqa: N802
    *values: Term | Any, labels: list[str] | None = None, prefix: str = "[DEBUG]"
) -> _Debug:
    """Quick debug output for development.

    Prints values with labels for quick debugging.

    Args:
        *values: Values to debug (Terms will be resolved)
        labels: Optional labels for each value
        prefix: Prefix for debug output (default: "[DEBUG]")

    Returns:
        Debug flow

    Example:
        >>> Debug(count.get(), status.get(), labels=["count", "status"])
        >>> Debug(x.get(), y.get())  # Uses v0, v1 as labels
    """
    return _Debug(values=list(values), labels=labels, prefix=prefix)
