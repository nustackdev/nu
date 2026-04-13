"""I/O ops -- Print, Log, Debug."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from nu.terms import Op


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

    Children: ``[message, *values]``

    Output format: ``[Print:message] value1 value2 ...``
    """

    def __init__(self, message: StrArg = "Print", *values: Any) -> None:
        super().__init__(message, *values)

    async def execute(self, ctx: Context) -> None:
        message = await self.children[0].execute(ctx)
        parts = [f"[Print:{message}]"]
        for child in self.children[1:]:
            val = await child.execute(ctx)
            parts.append(str(val))
        print(" ".join(parts))  # noqa: T201


class Log(Op):
    """Structured logging with configurable level.

    Children: ``[level, logger_name, message, *values]``
    """

    def __init__(
        self,
        message: StrArg,
        *values: Any,
        level: StrArg = "info",
        logger_name: StrArg = "nu",
    ) -> None:
        super().__init__(level, logger_name, message, *values)
        self._path = ""

    async def execute(self, ctx: Context) -> None:
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


class Debug(Op):
    """Quick debug output for development.

    Children: ``[prefix, labels, *values]``
    """

    def __init__(
        self,
        *values: Any,
        labels: Any = None,
        prefix: StrArg = "[DEBUG]",
    ) -> None:
        super().__init__(prefix, labels, *values)

    async def execute(self, ctx: Context) -> None:
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
