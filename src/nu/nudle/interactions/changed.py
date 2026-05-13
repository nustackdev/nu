"""Changed: subscribe to browser-side notifications for a nudle Ref.

Resolves to a `Subscription` handle that ReactForever and friends drive.
No outbound frame is sent when this evaluates -- the browser pushes
`notify` frames whenever the Ref changes, and session._dispatch fires
the subscription's callbacks.

We override `aeval` directly (rather than `_aapply`) so the Ref child
is not itself eval'd: subscribing must not trigger a read.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.shapes.queries.reactive import Change
from nu.terms.types import Mode

from ..session import NudleSession


if TYPE_CHECKING:
    from ..refs.base import NudleRef


__all__ = ["Changed"]


class Changed(Change):
    """Subscribe to browser-side change notifications on a nudle Ref."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(self, ref: NudleRef) -> None:
        super().__init__(ref)

    def eval(self, ctx: Any) -> Any:
        raise RuntimeError("nudle is async-only; use aexecute")

    async def aeval(self, ctx: Any) -> Any:
        ref = self._children[0]
        session = ctx.get(NudleSession)
        path = await ref.aresolve_address(ctx)
        return session.subscribe(path)

    def __repr__(self) -> str:
        return f"Changed({self._children[0]!r})"
