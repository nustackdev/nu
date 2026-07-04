"""Write interaction: server -> browser, replace a Ref's value."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nu.engine.structure import Declared
from nu.lang import Command

from ..protocol import Frame
from ..session import NudleSession


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu import Nu
    from nu.lang.runtime import Runtime

    from ..refs.base import NudleRef


__all__ = ["Write"]


class Write(Command):
    """Send a `write` frame on a nudle Ref."""

    mutates = Declared(value=frozenset({0}))
    requires_async = Declared(value=True)

    def __init__(self, ref: NudleRef, value: Nu | Any) -> None:
        super().__init__(ref, value)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nudle is async-only; use nu.arun")

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: NudleRef = self.children[0]
        value_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.get(NudleSession)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            value = await value_thunk(rt)
            await session.send(Frame(self, ref=path, payload=value))

        return athunk

    def __repr__(self) -> str:
        return f"Write({self.children[0]!r}, {self.children[1]!r})"
