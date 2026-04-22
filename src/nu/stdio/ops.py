"""Stdio Ops - write, read, flush.

StdioWrite: write to stdout/stderr (Command, writes=0)
StdioRead:  read line from stdin (Query)
StdioFlush: flush a stream (Command, writes=0)
"""

from __future__ import annotations

import sys
from typing import IO, TYPE_CHECKING

from nu.terms import Command, Query


if TYPE_CHECKING:
    from nu.context import Context

    from .refs import StdioRef


__all__ = [
    "StdioFlush",
    "StdioRead",
    "StdioWrite",
]


def _get_stream(ctx: Context, ref: object) -> IO:
    """Get stream for ref, with fallback to sys streams."""
    from .backend import StdioBackend

    if ctx.has(StdioBackend):
        return ctx.get(StdioBackend).stream_for(ref)
    return getattr(sys, ref.name)


class StdioWrite(Command):
    """Write values to a stdio stream.

    Children: [StdioRef, *values]
    Joins string-converted values with spaces, appends newline.
    """

    writes = 0

    def __init__(self, ref: StdioRef, *values: object) -> None:
        super().__init__(ref, *values)

    async def arun(self, ctx: Context) -> None:
        stream = _get_stream(ctx, self.children[0])
        parts = []
        for child in self.children[1:]:
            parts.append(str(await child.afirst(ctx)))
        stream.write(" ".join(parts) + "\n")

    def run(self, ctx: Context) -> None:
        stream = _get_stream(ctx, self.children[0])
        parts = [str(c.first(ctx)) for c in self.children[1:]]
        stream.write(" ".join(parts) + "\n")

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self.children)
        return f"StdioWrite({args})"


class StdioRead(Query[str]):
    """Read a line from stdin.

    Children: [StdioRef]
    Returns the line read (stripped of trailing newline).
    """

    def __init__(self, ref: StdioRef | None = None) -> None:
        from .refs import STDIN

        super().__init__(ref or STDIN)

    async def arun(self, ctx: Context) -> str:
        stream = _get_stream(ctx, self.children[0])
        line = stream.readline()
        return line.rstrip("\n")

    def run(self, ctx: Context) -> str:
        stream = _get_stream(ctx, self.children[0])
        line = stream.readline()
        return line.rstrip("\n")

    def __repr__(self) -> str:
        return f"StdioRead({self.children[0]!r})"


class StdioFlush(Command):
    """Flush a stdio stream's buffer.

    Children: [StdioRef]
    """

    writes = 0

    def __init__(self, ref: StdioRef) -> None:
        super().__init__(ref)

    async def arun(self, ctx: Context) -> None:
        stream = _get_stream(ctx, self.children[0])
        stream.flush()

    def run(self, ctx: Context) -> None:
        stream = _get_stream(ctx, self.children[0])
        stream.flush()

    def __repr__(self) -> str:
        return f"StdioFlush({self.children[0]!r})"
