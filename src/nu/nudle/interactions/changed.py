"""Changed: subscribe to browser-side notifications for a nudle Ref.

Resolves to a `Subscription` handle that ReactForever and friends drive.
No outbound frame is sent when this evaluates -- the browser pushes
`notify` frames whenever the Ref changes, and session._dispatch fires
the subscription's callbacks.

We resolve the Ref's wire path but never eval the Ref child: subscribing
must not trigger a read. React drives the returned Subscription via its
`bind` / `unbind` / `close` interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import ScalarQuery

from ..session import NudleSession, Subscription


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

    from ..refs.base import NudleRef


__all__ = ["Changed"]


class Changed(ScalarQuery):
    """Subscribe to browser-side change notifications on a nudle Ref."""

    requires_async = Declared(value=True)

    def __init__(self, ref: NudleRef) -> None:
        super().__init__(ref)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> Subscription:
            raise RuntimeError("nudle is async-only; use nu.arun")

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref: NudleRef = self.children[0]

        async def athunk(rt: Runtime) -> Subscription:
            session = rt.ctx.get(NudleSession)
            ref_nid = rt.program.children[nid][0]
            path = await ref._aresolve_address(rt, ref_nid)
            return session.subscribe(path)

        return athunk

    def __repr__(self) -> str:
        return f"Changed({self.children[0]!r})"
