"""I/O flows -- Print, Log, Debug."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from nu.utils import ensure_nu

from .base import Flow


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import Nu, StrArg


__all__ = [
    "Debug",
    "Log",
    "Print",
]


class Print(Flow):
    """Print messages to stdout.

    Children layout: ``[message, *values]``

    The *message* parameter is auto-wrapped via ``ensure_nu`` if a literal is
    passed.  All *values* are likewise auto-wrapped so the full parameter
    list lives in the children tree.

    Example::

        Print("status", some_term, another_term)
        # Output: [Print:status] <value1> <value2>

        Print()
        # Output: [Print:Print]
    """

    def __init__(self, message: StrArg = "Print", *values: Any) -> None:
        """Initialize print flow.

        Args:
            message: Label or Nu shown in the output prefix.
            values: Additional Terms or literals whose results are printed.
        """
        children: list[Nu] = [ensure_nu(message)]
        for v in values:
            children.append(ensure_nu(v))
        super().__init__(*children)

    async def execute(self, ctx: Context) -> None:
        """Evaluate message and values, then print formatted output."""
        message = await self.children[0].execute(ctx)
        parts = [f"[Print:{message}]"]
        for child in self.children[1:]:
            val = await child.execute(ctx)
            parts.append(str(val))
        print(" ".join(parts))  # noqa: T201


class Log(Flow):
    """Structured logging with configurable level.

    Children layout: ``[level, logger_name, message, *values]``

    All parameters are auto-wrapped via ``ensure_nu`` so the full
    parameter list lives in the children tree.

    Example::

        Log("request received")
        Log("synced slot", slot_ref, ":", tx_count, "txs")
        Log("disk full", level="error", logger_name="myapp.storage")
    """

    def __init__(
        self,
        message: StrArg,
        *values: Any,
        level: StrArg = "info",
        logger_name: StrArg = "everybase.flows",
    ) -> None:
        """Initialize log flow.

        Args:
            message: Nu or literal string to log.
            values: Additional Terms or literals whose results are logged.
            level: Logging level name. ``"debug"``, ``"info"``,
                ``"warning"``, ``"error"``, or ``"critical"``.
            logger_name: Logger name passed to ``logging.getLogger``.
        """
        children: list[Nu] = [ensure_nu(level), ensure_nu(logger_name), ensure_nu(message)]
        for v in values:
            children.append(ensure_nu(v))
        super().__init__(*children)
        self._path = ""

    async def execute(self, ctx: Context) -> None:
        """Evaluate message and values, then emit a log record."""
        level = await self.children[0].execute(ctx)
        logger_name = await self.children[1].execute(ctx)
        parts: list[str] = []
        for child in self.children[2:]:
            parts.append(str(await child.execute(ctx)))
        message = " ".join(parts)
        if self._path:
            message = f"[{self._path}] {message}"
        logger = logging.getLogger(logger_name)
        getattr(logger, level)(message)


class Debug(Flow):
    """Quick debug output for development.

    Children layout: ``[prefix, labels, *values]``

    All parameters are auto-wrapped via ``ensure_nu``.
    *labels* resolves to a list of strings (or None); unlabelled values
    are printed as ``repr``.

    Example::

        Debug(x, y, labels=["x", "y"])
        # Output: [DEBUG] x=42 y='hello'

        Debug(x, y, prefix="[TRACE]")
        # Output: [TRACE] 42 'hello'
    """

    def __init__(
        self,
        *values: Any,
        labels: Any = None,
        prefix: StrArg = "[DEBUG]",
    ) -> None:
        """Initialize debug flow.

        Args:
            values: Terms or literals whose results are printed.
            labels: List of label strings (or Nu resolving to one).
                When provided, output uses ``label=repr(value)`` format.
            prefix: String prefix prepended to the output line.
        """
        children: list[Nu] = [ensure_nu(prefix), ensure_nu(labels)]
        for v in values:
            children.append(ensure_nu(v))
        super().__init__(*children)

    async def execute(self, ctx: Context) -> None:
        """Evaluate all values and print debug output."""
        prefix = await self.children[0].execute(ctx)
        labels = await self.children[1].execute(ctx)
        parts = [str(prefix)]
        for i, child in enumerate(self.children[2:]):
            val = await child.execute(ctx)
            if labels and i < len(labels):
                parts.append(f"{labels[i]}={val!r}")
            else:
                parts.append(repr(val))
        print(" ".join(parts))  # noqa: T201
