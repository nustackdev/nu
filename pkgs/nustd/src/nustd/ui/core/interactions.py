"""Wire interactions -- ops that flow over a Session on a Ref.

Each class's lowercased name becomes its op string in the protocol Frame
(see protocol.py). Refs decide which interactions they expose by returning
the corresponding class from their methods (e.g. ButtonRef.on_click ->
Changed, HeadingRef.set -> Write).

- Write   -- server -> client, replace a Ref's value
- Append  -- server -> client, append to a sequence-typed Ref
- Remove  -- server -> client, drop a Ref's node and everything under it
- Changed -- subscribe to client-side notifications on a Ref, all of them
             or only one event's

All four target the abstract ``Session`` from core.session -- the host
plugs in its concrete transport (nudle over ws; others in future).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import EMPTY, Command, ScalarQuery

from .protocol import Frame
from .session import Session


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.args import StrArg
    from nu.lang.runtime import Runtime

    from .base import Ref
    from .session import Subscription


__all__ = ["EVENT", "Append", "Changed", "Remove", "Write"]


#: The payload field a notify names its event in, for a Ref that sends more
#: than one kind (a tree's select, rename, move). A Ref that uses it keeps the
#: name for that and sends no field of its own under it.
EVENT = "event"


class Write(Command):
    """Send a `write` frame on a Ref -- replace the value. An EMPTY value raises."""

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nustd.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]
        value_thunk = children[1]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.fabrics.get(Session)
            ref_nid = rt.program.children[nid][0]
            # One walk: the chain carries the segments the plain path is made
            # of, plus the type and props the browser needs to create the node.
            chain = await ref._aresolve_chain(rt, ref_nid)
            path = tuple(seg for seg, _, _ in chain)
            value = await value_thunk(rt)
            if value is EMPTY:
                raise ValueError("cannot write EMPTY")
            await session.send(Frame(self, ref=path, payload=value, chain=chain))

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
            raise RuntimeError("nustd.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]
        value_thunks = children[1:]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.fabrics.get(Session)
            ref_nid = rt.program.children[nid][0]
            chain = await ref._aresolve_chain(rt, ref_nid)
            path = tuple(seg for seg, _, _ in chain)
            values = [await t(rt) for t in value_thunks]
            if any(v is EMPTY for v in values):
                raise ValueError("cannot write EMPTY")
            payload = values[0] if len(values) == 1 else values
            await session.send(Frame(self, ref=path, payload=payload, chain=chain))

        return athunk


class Remove(Command):
    """Send a `remove` frame on a Ref -- drop its node and its whole subtree.

    The plain path and no chain: a remove is addressed at a node that is
    already there, so there is nothing to bring into being on the way down.
    A path the browser does not have is a no-op there, which is what the
    first run of anything that wipes before it draws relies on.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            raise RuntimeError("nustd.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]

        async def athunk(rt: Runtime) -> None:
            session = rt.ctx.fabrics.get(Session)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            await session.send(Frame(self, ref=path))

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

    A Ref that sends several kinds of notify names each in the payload's
    ``event`` field, and ``event`` here takes only that kind: the rest never
    reach the callbacks. Left out, every notify on the Ref arrives.

    Args:
        ref: The Ref whose notifications to take.
        event: Only the notifies whose ``event`` field is this.
    """

    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, ref: Ref, event: StrArg | None = None) -> None:
        if event is None:
            super().__init__(ref)
        else:
            super().__init__(ref, event)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> Subscription:
            raise RuntimeError("nustd.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: Ref = self._children[0]
        event_thunk = children[1] if len(children) > 1 else None

        async def athunk(rt: Runtime) -> Subscription:
            session = rt.ctx.fabrics.get(Session)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            sub = session.subscribe(path)
            if event_thunk is None:
                return sub
            return _Only(sub, str(await event_thunk(rt)))

        return athunk


class _Only:
    """A subscription passing on only the notifies of one event.

    Wraps each bound callback in a check on the payload's ``event`` field.
    The check never raises: a session drops a callback that raises as a dead
    far end. Callbacks are matched by identity, never hashed, for the same
    reason the session's own subscription does it.
    """

    __slots__ = ("_bound", "_event", "_sub")

    def __init__(self, sub: Subscription, event: str) -> None:
        self._sub = sub
        self._event = event
        self._bound: list[tuple[Callable[[object], None], Callable[[object], None]]] = []

    def bind(self, cb: Callable[[object], None]) -> None:
        if any(bound is cb for bound, _ in self._bound):
            return
        event = self._event

        def only(payload: object) -> None:
            if isinstance(payload, dict) and payload.get(EVENT) == event:
                cb(payload)

        self._bound.append((cb, only))
        self._sub.bind(only)

    def unbind(self, cb: Callable[[object], None]) -> None:
        for bound, only in self._bound:
            if bound is cb:
                self._sub.unbind(only)
        self._bound = [(bound, only) for bound, only in self._bound if bound is not cb]

    def close(self) -> None:
        self._bound = []
        self._sub.close()
