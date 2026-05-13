"""nudle commands.

Each command resolves the NudleSession bound on Context, resolves the Ref's
wire path, evaluates the payload, and ships a frame. Async-only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.types import Effect, Mode

from .session import NudleSession


if TYPE_CHECKING:
    from nu import Nu

    from .refs import NudleRef


__all__ = [
    "NudleAppendCmd",
    "NudleWriteCmd",
]


_ASYNC = frozenset({Mode.ASYNC})


class NudleWriteCmd(ScalarCommand):
    """Send `write` on a nudle Ref. Payload is one Nu, evaluated."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _ASYNC

    def __init__(self, ref: NudleRef, value: Nu | Any) -> None:
        super().__init__(ref, value)

    async def arun(self, ctx: Any) -> None:
        from nu import runtime

        ref = self._children[0]
        session = ctx.get(NudleSession)
        path = await ref.aresolve_address(ctx)
        value = await runtime.afirst(self._children[1], ctx)
        await session.awrite(path, value)

    def run(self, ctx: Any) -> None:
        raise RuntimeError("nudle is async-only; use aexecute")

    def __repr__(self) -> str:
        return f"NudleWriteCmd({self._children[0]!r}, {self._children[1]!r})"


class NudleAppendCmd(ScalarCommand):
    """Send `append` on a nudle Ref. Payload is one Nu (or a list of them).

    A single child -> payload is its value. Multiple children -> payload is
    a list of resolved values, in order. LineChart uses the multi-child form
    so `chart.append(x, y)` lands as `[x, y]` on the wire.
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _ASYNC

    def __init__(self, ref: NudleRef, *values: Nu | Any) -> None:
        super().__init__(ref, *values)

    async def arun(self, ctx: Any) -> None:
        from nu import runtime

        ref = self._children[0]
        session = ctx.get(NudleSession)
        path = await ref.aresolve_address(ctx)
        values = [await runtime.afirst(c, ctx) for c in self._children[1:]]
        payload = values[0] if len(values) == 1 else values
        await session.aappend(path, payload)

    def run(self, ctx: Any) -> None:
        raise RuntimeError("nudle is async-only; use aexecute")

    def __repr__(self) -> str:
        parts = ", ".join(repr(c) for c in self._children[1:])
        return f"NudleAppendCmd({self._children[0]!r}, {parts})"
