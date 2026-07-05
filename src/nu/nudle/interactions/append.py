"""Append interaction: server -> browser, append to a sequence-typed Ref.

Multi-arg form for charts: `chart.append(x, y)` ships `[x, y]` as payload.
Single-arg form ships the value directly.
"""

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


__all__ = ["Append"]


class Append(Command):
    """Send an `append` frame on a nudle Ref."""

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, ref: NudleRef, *values: Nu | Any) -> None:
        super().__init__(ref, *values)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nudle is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: NudleRef = self._children[0]
        value_thunks = children[1:]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.get(NudleSession)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            values = [await t(rt) for t in value_thunks]
            payload = values[0] if len(values) == 1 else values
            await session.send(Frame(self, ref=path, payload=payload))

        return athunk

    def __repr__(self) -> str:
        parts = ", ".join(repr(c) for c in self._children[1:])
        return f"Append({self._children[0]!r}, {parts})"
