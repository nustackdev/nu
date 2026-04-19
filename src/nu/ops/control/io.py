"""I/O ops -- Print, Log, Debug.

Commands that write to stdio. All declare `writes = 0` (StdioRef position).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from nu.eval import first
from nu.stdio.refs import STDERR, STDOUT
from nu.terms.op import Command


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import Arg, StrArg


__all__ = [
    "Debug",
    "Log",
    "Print",
]


class Print(Command):
    """Print messages to stdout.

    Children: [StdioRef.STDOUT, message, *values]
    Output: `[Print:message] value1 value2 ...`
    """

    writes = 0  # StdioRef at child 0 is a WRITE target

    def __init__(self, message: Arg = "Print", *values: Any) -> None:
        super().__init__(STDOUT, message, *values)

    async def run(self, ctx: Context) -> None:
        from nu.stdio.ops import _get_stream

        stream = _get_stream(ctx, self.children[0])
        message = await first(self.children[1], ctx)
        parts = [f"[Print:{message}]"]
        for child in self.children[2:]:
            parts.append(str(await first(child, ctx)))
        stream.write(" ".join(parts) + "\n")


class Log(Command):
    """Structured logging with configurable level.

    Children: [StdioRef.STDERR, level, logger_name, message, *values]
    """

    writes = 0

    def __init__(
        self,
        message: StrArg,
        *values: Any,
        level: StrArg = "info",
        logger_name: StrArg = "nu",
    ) -> None:
        super().__init__(STDERR, level, logger_name, message, *values)
        self._path = ""

    async def run(self, ctx: Context) -> None:
        level = await first(self.children[1], ctx)
        logger_name = await first(self.children[2], ctx)
        parts = [str(await first(c, ctx)) for c in self.children[3:]]
        message = " ".join(parts)
        if self._path:
            message = f"[{self._path}] {message}"
        getattr(logging.getLogger(logger_name), level)(message)


class Debug(Command):
    """Quick debug output for development.

    Children: [StdioRef.STDOUT, prefix, labels, *values]
    """

    writes = 0

    def __init__(
        self,
        *values: Any,
        labels: Any = None,
        prefix: StrArg = "[DEBUG]",
    ) -> None:
        super().__init__(STDOUT, prefix, labels, *values)

    async def run(self, ctx: Context) -> None:
        from nu.stdio.ops import _get_stream

        stream = _get_stream(ctx, self.children[0])
        prefix = await first(self.children[1], ctx)
        labels = await first(self.children[2], ctx)
        parts = [str(prefix)]
        for i, child in enumerate(self.children[3:]):
            val = await first(child, ctx)
            if labels and i < len(labels):
                parts.append(f"{labels[i]}={val!r}")
            else:
                parts.append(repr(val))
        stream.write(" ".join(parts) + "\n")
