"""Append interaction: server -> browser, append to a sequence-typed Ref.

Multi-arg form for charts: `chart.append(x, y)` ships `[x, y]` as payload.
Single-arg form ships the value directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.types import Effect, Mode

from ..protocol import Frame
from ..session import NudleSession


if TYPE_CHECKING:
    from nu import Nu

    from ..refs.base import NudleRef


__all__ = ["Append"]


class Append(ScalarCommand):
    """Send an `append` frame on a nudle Ref."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(self, ref: NudleRef, *values: Nu | Any) -> None:
        super().__init__(ref, *values)

    async def arun(self, ctx: Any) -> None:
        from nu import runtime

        ref = self._children[0]
        session = ctx.get(NudleSession)
        path = await ref.aresolve_address(ctx)
        values = [await runtime.afirst(c, ctx) for c in self._children[1:]]
        payload = values[0] if len(values) == 1 else values
        await session.send(Frame(self, ref=path, payload=payload))

    def run(self, ctx: Any) -> None:
        raise RuntimeError("nudle is async-only; use aexecute")

    def __repr__(self) -> str:
        parts = ", ".join(repr(c) for c in self._children[1:])
        return f"Append({self._children[0]!r}, {parts})"
