"""I/O ops -- Print, Log, Debug.

These are convenience constructors over StdioWrite.
All declare WRITE override at position 0 (StdioRef).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from nu.stdio.refs import STDERR, STDOUT
from nu.terms.effect import Direction
from nu.terms.op import Op


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import StrArg


__all__ = [
    "Debug",
    "Log",
    "Print",
]


class Print(Op):
    """Print messages to stdout.

    Children: ``[StdioRef.STDOUT, message, *values]``

    Output format: ``[Print:message] value1 value2 ...``
    """

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.WRITE}

    def __init__(self, message: StrArg = "Print", *values: Any) -> None:
        super().__init__(STDOUT, message, *values)

    async def execute(self, ctx: Context) -> None:  # noqa: D102
        from nu.stdio.ops import _get_stream

        stream = _get_stream(ctx, self.children[0])
        message = await self.children[1].execute(ctx)
        parts = [f"[Print:{message}]"]
        for child in self.children[2:]:
            val = await child.execute(ctx)
            parts.append(str(val))
        stream.write(" ".join(parts) + "\n")


class Log(Op):
    """Structured logging with configurable level.

    Children: ``[StdioRef.STDERR, level, logger_name, message, *values]``
    """

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.WRITE}

    def __init__(
        self,
        message: StrArg,
        *values: Any,
        level: StrArg = "info",
        logger_name: StrArg = "nu",
    ) -> None:
        super().__init__(STDERR, level, logger_name, message, *values)
        self._path = ""

    async def execute(self, ctx: Context) -> None:  # noqa: D102
        level = await self.children[1].execute(ctx)
        logger_name = await self.children[2].execute(ctx)
        parts: list[str] = []
        for child in self.children[3:]:
            parts.append(str(await child.execute(ctx)))
        message = " ".join(parts)
        if self._path:
            message = f"[{self._path}] {message}"
        logger = logging.getLogger(logger_name)
        getattr(logger, level)(message)


class Debug(Op):
    """Quick debug output for development.

    Children: ``[StdioRef.STDOUT, prefix, labels, *values]``
    """

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.WRITE}

    def __init__(
        self,
        *values: Any,
        labels: Any = None,
        prefix: StrArg = "[DEBUG]",
    ) -> None:
        super().__init__(STDOUT, prefix, labels, *values)

    async def execute(self, ctx: Context) -> None:  # noqa: D102
        from nu.stdio.ops import _get_stream

        stream = _get_stream(ctx, self.children[0])
        prefix = await self.children[1].execute(ctx)
        labels = await self.children[2].execute(ctx)
        parts = [str(prefix)]
        for i, child in enumerate(self.children[3:]):
            val = await child.execute(ctx)
            if labels and i < len(labels):
                parts.append(f"{labels[i]}={val!r}")
            else:
                parts.append(repr(val))
        stream.write(" ".join(parts) + "\n")
