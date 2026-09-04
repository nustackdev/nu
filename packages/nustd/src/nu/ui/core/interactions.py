"""Wire interactions -- ops that flow over a Session on a Ref.

Each class's lowercased name becomes its op string in the protocol Frame
(see protocol.py). Refs decide which interactions they expose by returning
the corresponding class from their methods (e.g. ButtonRef.clicked ->
Changed, HeadingRef.set -> Write).

- Write   -- server -> client, replace a Ref's value
- Append  -- server -> client, append to a sequence-typed Ref
- Changed -- subscribe to client-side notifications on a Ref

All three target the abstract ``Session`` from core.session -- the host
plugs in its concrete transport (nudle over ws; others in future).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Command, ScalarQuery

from .protocol import Frame
from .session import Session


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

    from .base import Ref
    from .session import Subscription


__all__ = ["Append", "Changed", "Write"]


class Write(Command):
    """Send a `write` frame on a Ref -- replace the value."""

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nu.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]
        value_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.get(Session)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            value = await value_thunk(rt)
            await session.send(Frame(self, ref=path, payload=value))

        return athunk


class Append(Command):
    """Send an `append` frame on a Ref -- push onto a sequence.

    Multi-arg form for charts: `chart.append(x, y)` ships `[x, y]` as
    payload. Single-arg form ships the value directly.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nu.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]
        value_thunks = children[1:]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.get(Session)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            values = [await t(rt) for t in value_thunks]
            payload = values[0] if len(values) == 1 else values
            await session.send(Frame(self, ref=path, payload=payload))

        return athunk


class Changed(ScalarQuery):
    """Subscribe to client-side change notifications on a Ref.

    Resolves to a `Subscription` handle that ReactForever and friends drive.
    No outbound frame is sent when this evaluates -- the client pushes
    `notify` frames whenever the Ref changes, and the session dispatches
    them to the subscription's callbacks.

    Resolves the Ref's wire path but never evals the Ref child: subscribing
    must not trigger a read. Consumers drive the returned Subscription via
    its `bind` / `unbind` / `close` interface.
    """

    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> Subscription:
            raise RuntimeError("nu.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]

        async def athunk(rt: Runtime) -> Subscription:
            session = rt.ctx.get(Session)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            return session.subscribe(path)

        return athunk
