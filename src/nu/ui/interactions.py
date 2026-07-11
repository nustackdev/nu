"""nudle interactions -- the ops that flow over the wire on Refs.

Each class's lowercased name becomes its op string in the protocol Frame
(see protocol.py). Refs decide which interactions they expose by returning
the corresponding class from their methods (e.g. ButtonRef.clicked ->
Changed, HeadingRef.store -> Write).

- Write   -- server -> browser, replace a Ref's value
- Append  -- server -> browser, append to a sequence-typed Ref
- Changed -- subscribe to browser-side notifications on a Ref
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command, ScalarQuery

from .protocol import Frame
from .session import NudleSession


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

    from .refs.base import NudleRef
    from .session import Subscription


__all__ = ["Append", "Changed", "Write"]


class Write(Command):
    """Send a `write` frame on a nudle Ref -- replace the value."""

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nudle is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: NudleRef = self._children[0]
        value_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.get(NudleSession)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            value = await value_thunk(rt)
            await session.send(Frame(self, ref=path, payload=value))

        return athunk


class Append(Command):
    """Send an `append` frame on a nudle Ref -- push onto a sequence.

    Multi-arg form for charts: `chart.append(x, y)` ships `[x, y]` as
    payload. Single-arg form ships the value directly.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

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


class Changed(ScalarQuery):
    """Subscribe to browser-side change notifications on a nudle Ref.

    Resolves to a `Subscription` handle that ReactForever and friends drive.
    No outbound frame is sent when this evaluates -- the browser pushes
    `notify` frames whenever the Ref changes, and session._dispatch fires
    the subscription's callbacks.

    Resolves the Ref's wire path but never evals the Ref child: subscribing
    must not trigger a read. React drives the returned Subscription via its
    `bind` / `unbind` / `close` interface.
    """

    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> Subscription:
            raise RuntimeError("nudle is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: NudleRef = self._children[0]

        async def athunk(rt: Runtime) -> Subscription:
            session = rt.ctx.get(NudleSession)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            return session.subscribe(path)

        return athunk
