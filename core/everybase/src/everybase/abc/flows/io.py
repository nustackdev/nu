"""I/O flows -- Print, Log, Debug."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from everybase import Flow

from ..utils import ensure_term


if TYPE_CHECKING:
    from everybase import Context, Executable, StrArg


__all__ = [
    "Debug",
    "Log",
    "Print",
]


class Print(Flow):
    """Print messages to stdout.

    Children layout: ``[message, *values]``

    The *message* parameter is auto-wrapped via ``ensure_term`` if a literal is
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
            message: Label or Term shown in the output prefix.
            values: Additional Terms or literals whose results are printed.
        """
        children: list[Executable] = [ensure_term(message)]
        for v in values:
            children.append(ensure_term(v))
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

    Children layout: ``[message, *values]``

    The *message* parameter is auto-wrapped via ``ensure_term`` if a literal is
    passed.  All *values* are likewise auto-wrapped so the full parameter
    list lives in the children tree.  The *level* and *logger_name* are plain
    strings used at construction time only and are not children.

    Example::

        Log("request received")
        Log("synced slot", slot_ref, ":", tx_count, "txs")
        Log("disk full", level="error", logger_name="myapp.storage")
    """

    def __init__(
        self,
        message: StrArg,
        *values: Any,
        level: str = "info",
        logger_name: str = "everybase.flows",
    ) -> None:
        """Initialize log flow.

        Args:
            message: Term or literal string to log.
            values: Additional Terms or literals whose results are logged.
            level: Logging level name -- ``"debug"``, ``"info"``,
                ``"warning"``, ``"error"``, or ``"critical"``.
            logger_name: Logger name passed to ``logging.getLogger``.
        """
        children: list[Executable] = [ensure_term(message)]
        for v in values:
            children.append(ensure_term(v))
        super().__init__(*children)
        self._level = level
        self._logger_name = logger_name
        self._path = ""

    async def execute(self, ctx: Context) -> None:
        """Evaluate message and values, then emit a log record."""
        parts: list[str] = []
        for child in self.children:
            parts.append(str(await child.execute(ctx)))
        message = " ".join(parts)
        if self._path:
            message = f"[{self._path}] {message}"
        logger = logging.getLogger(self._logger_name)
        getattr(logger, self._level)(message)


class Debug(Flow):
    """Quick debug output for development.

    Children layout: ``[*values]``

    All *values* are auto-wrapped via ``ensure_term`` if literals are passed.
    Optional *labels* pair with positional values; unlabelled values are
    printed as ``repr``.

    Example::

        Debug(x, y, labels=["x", "y"])
        # Output: [DEBUG] x=42 y='hello'

        Debug(x, y, prefix="[TRACE]")
        # Output: [TRACE] 42 'hello'
    """

    def __init__(
        self,
        *values: Any,
        labels: list[str] | None = None,
        prefix: str = "[DEBUG]",
    ) -> None:
        """Initialize debug flow.

        Args:
            values: Terms or literals whose results are printed.
            labels: Optional list of labels corresponding to each value.
                When provided, output uses ``label=repr(value)`` format.
            prefix: String prefix prepended to the output line.
        """
        super().__init__(*(ensure_term(v) for v in values))
        self._labels = labels
        self._prefix = prefix

    async def execute(self, ctx: Context) -> None:
        """Evaluate all values and print debug output."""
        parts = [self._prefix]
        for i, child in enumerate(self.children):
            val = await child.execute(ctx)
            if self._labels and i < len(self._labels):
                parts.append(f"{self._labels[i]}={val!r}")
            else:
                parts.append(repr(val))
        print(" ".join(parts))  # noqa: T201
