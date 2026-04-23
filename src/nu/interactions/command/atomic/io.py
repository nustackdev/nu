"""I/O ops -- Print, Log, Debug.

Commands that write to stdio. All declare `writes = 0` (StdioRef position).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from nu.stdio.refs import STDERR, STDOUT
from nu.terms import Atomic, Mode


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import Arg, StrArg


__all__ = [
    "Debug",
    "Log",
    "Print",
]


class Print(Atomic):
    """Print messages to stdout.

    Children: [StdioRef.STDOUT, message, *values]
    Output: `[Print:message] value1 value2 ...`
    """

    writes = 0  # StdioRef at child 0 is a WRITE target
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(self, *values: Arg) -> None:
        super().__init__(STDOUT, *values)

    def run(self, ctx: Context) -> None:
        from nu.stdio.ops import _get_stream

        stream = _get_stream(ctx, self.children[0])
        parts = [str(c.collect(ctx)) for c in self.children[1:]]
        stream.write(" ".join(parts) + "\n")


class Log(Atomic):
    """Structured logging with configurable level.

    Children: [StdioRef.STDERR, level, logger_name, message, *values]
    """

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        message: StrArg,
        *values: Any,
        level: StrArg = "info",
        logger_name: StrArg = "nu",
    ) -> None:
        super().__init__(STDERR, level, logger_name, message, *values)
        self._path = ""

    def run(self, ctx: Context) -> None:
        level = self.children[1].first(ctx)
        logger_name = self.children[2].first(ctx)
        parts = [str(c.collect(ctx)) for c in self.children[3:]]
        message = " ".join(parts)
        if self._path:
            message = f"[{self._path}] {message}"
        getattr(logging.getLogger(logger_name), level)(message)


class Debug(Atomic):
    """Quick debug output for development.

    Children: [StdioRef.STDOUT, prefix, labels, *values]
    """

    writes = 0
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *values: Any,
        labels: Any = None,
        prefix: StrArg = "[DEBUG]",
    ) -> None:
        super().__init__(STDOUT, prefix, labels, *values)

    def run(self, ctx: Context) -> None:
        from nu.stdio.ops import _get_stream

        stream = _get_stream(ctx, self.children[0])
        prefix = self.children[1].first(ctx)
        labels = self.children[2].first(ctx)
        parts = [str(prefix)]
        for i, child in enumerate(self.children[3:]):
            val = child.collect(ctx)
            if labels and i < len(labels):
                parts.append(f"{labels[i]}={val!r}")
            else:
                parts.append(repr(val))
        stream.write(" ".join(parts) + "\n")
