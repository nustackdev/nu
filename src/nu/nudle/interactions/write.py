"""Write interaction: server -> browser, replace a Ref's value."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.types import Effect, Mode

from ..protocol import Frame
from ..session import NudleSession


if TYPE_CHECKING:
    from nu import Nu

    from ..refs.base import NudleRef


__all__ = ["Write"]


class Write(ScalarCommand):
    """Send a `write` frame on a nudle Ref."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(self, ref: NudleRef, value: Nu | Any) -> None:
        super().__init__(ref, value)

    async def arun(self, ctx: Any) -> None:
        from nu import runtime

        ref = self._children[0]
        session = ctx.get(NudleSession)
        path = await ref.aresolve_address(ctx)
        value = await runtime.afirst(self._children[1], ctx)
        await session.send(Frame(self, ref=path, payload=value))

    def run(self, ctx: Any) -> None:
        raise RuntimeError("nudle is async-only; use aexecute")

    def __repr__(self) -> str:
        return f"Write({self._children[0]!r}, {self._children[1]!r})"
