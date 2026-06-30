"""Stdio Ops - write, read, flush."""

from __future__ import annotations

import sys
from typing import IO, TYPE_CHECKING, Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.query import ScalarQuery
from nu.terms.types import Effect, Mode


if TYPE_CHECKING:
    from .refs import StdioRef


__all__ = [
    "StdioFlush",
    "StdioRead",
    "StdioWrite",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


def _get_stream(ctx: Any, ref: Any) -> IO:  # noqa: ANN401
    from .backend import StdioBackend

    if ctx.has(StdioBackend):
        return ctx.get(StdioBackend).stream_for(ref)
    return getattr(sys, ref.name)


class StdioWrite(ScalarCommand):
    """Write values to a stdio stream."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, ref: StdioRef, *values: Any) -> None:  # noqa: ANN401
        super().__init__(ref, *values)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        stream = _get_stream(ctx, self._children[0])
        parts = [str(runtime.first(c, ctx)) for c in self._children[1:]]
        stream.write(" ".join(parts) + "\n")

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        stream = _get_stream(ctx, self._children[0])
        parts = [str(await runtime.afirst(c, ctx)) for c in self._children[1:]]
        stream.write(" ".join(parts) + "\n")


class StdioRead(ScalarQuery):
    """Read a line from stdin."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, ref: StdioRef | None = None) -> None:
        from .refs import STDIN

        super().__init__(ref or STDIN)

    def _apply(self, ctx: Any, ops: list[Any]) -> str:  # noqa: ANN401
        # ops[0] is the resolved ref value (stream handle from Ref.eval).
        # We need the ref itself to use _get_stream; pull from _children.
        stream = _get_stream(ctx, self._children[0])
        line = stream.readline()
        return line.rstrip("\n")


class StdioFlush(ScalarCommand):
    """Flush a stdio stream's buffer."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, ref: StdioRef) -> None:
        super().__init__(ref)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        stream = _get_stream(ctx, self._children[0])
        stream.flush()

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        stream = _get_stream(ctx, self._children[0])
        stream.flush()
