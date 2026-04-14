"""Stdio Ops - write, read, flush.

StdioWrite: write to stdout/stderr (WRITE override)
StdioRead: read line from stdin
StdioFlush: flush a stream (WRITE override)
"""

from __future__ import annotations

import sys
from typing import IO, TYPE_CHECKING, ClassVar

from nu.terms.effect import Direction
from nu.terms.op import Op


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


class StdioWrite(Op[None]):
    """Write values to a stdio stream.

    Children: [StdioRef, *values]
    Joins string-converted values with spaces, appends newline.
    """

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.WRITE}

    def __init__(self, ref: StdioRef, *values: object) -> None:
        super().__init__(ref, *values)

    async def execute(self, ctx: Context) -> None:
        """Write formatted values to the stream."""
        stream = _get_stream(ctx, self.children[0])
        parts = []
        for child in self.children[1:]:
            val = await child.execute(ctx)
            parts.append(str(val))
        stream.write(" ".join(parts) + "\n")

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self.children)
        return f"StdioWrite({args})"


class StdioRead(Op[str]):
    """Read a line from stdin.

    Children: [StdioRef]
    Returns the line read (stripped of trailing newline).
    """

    def __init__(self, ref: StdioRef | None = None) -> None:
        from .refs import STDIN

        super().__init__(ref or STDIN)

    async def execute(self, ctx: Context) -> str:
        """Read one line from the stream."""
        stream = _get_stream(ctx, self.children[0])
        line = stream.readline()
        return line.rstrip("\n")

    def __repr__(self) -> str:
        return f"StdioRead({self.children[0]!r})"


class StdioFlush(Op[None]):
    """Flush a stdio stream's buffer.

    Children: [StdioRef]
    """

    overrides: ClassVar[dict[int, Direction]] = {0: Direction.WRITE}

    def __init__(self, ref: StdioRef) -> None:
        super().__init__(ref)

    async def execute(self, ctx: Context) -> None:
        """Flush the stream."""
        stream = _get_stream(ctx, self.children[0])
        stream.flush()

    def __repr__(self) -> str:
        return f"StdioFlush({self.children[0]!r})"
