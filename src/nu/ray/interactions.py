"""``Teleport``: ship the body to a ``RayService`` for remote execution.

Teleport is a Policy - it decides *where* the body runs, the same family as
Retry / Timeout, and never runs the body locally. It captures the body term
(slot 0), resolves a ``RayService`` from ctx by tag, and calls
``service.aexecute(body_term)`` on the remote actor.

Transparent: removing Teleport doesn't change what is computed, only where it
runs. Cardinality is preserved - a stream body is collapsed to the single
remote result and yielded once.

Async-only: the body ships via ray, which requires the async runtime.

``target`` is a single hashable used verbatim as the tag; omitting it (or
passing ``UNSET``) resolves the untagged singleton. Everything matches the
shape ``Provide`` / ``ProvideList`` / ``ProvideDict`` used to bind (int
index for ``ProvideList``, dict key for ``ProvideDict``, no tag for a bare
``Provide``). ``target=None`` is a legitimate tag - the sentinel makes the
"no tag given" branch unambiguous.

Usage::

    # Untagged singleton
    Teleport(body)

    # ProvideList index
    Teleport(body, target=0)

    # ProvideDict tuple key (matches feed_run's ("ledger", i) shape)
    Teleport(body, target=("ledger", 0))

    # ProvideDict string key
    Teleport(body, target="ledger-main")

    # Carry parent's attrs to worker
    Teleport(body, target=("indexer", 3), carry=True)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Attr, Cardinality, Policy
from nu.lang.sentinels import UNSET

from .resources import RayService


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from nu.lang import Nu
    from nu.lang.runtime import Runtime


__all__ = ["Teleport"]


async def _one(value: object) -> AsyncIterator:
    """Yield a collapsed remote result once (stream body -> one-item stream)."""
    if value is not None:
        yield value


class Teleport(Policy):
    """Ship the body to a ``RayService`` for remote execution.

    Args:
        body: The Nu to execute remotely. Captured as a term, not run locally.
        target: The tag identifying the ``RayService`` on ctx. A single value
            (str, int, tuple) becomes a one-element tag; pass a tuple
            explicitly to preserve tuple keys, matching whatever ``ctx.bind``
            used. Accepts an already-wrapped tuple too.
        carry: If True, copy the parent's ``ctx.attrs`` to the remote actor's
            Context before executing there.
    """

    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, body: Nu, *, target: object = UNSET, carry: bool = False) -> None:
        super().__init__(body)
        self._payload["target"] = target
        self._payload["carry"] = carry

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            msg = "Teleport requires the async runtime; use arun / afirst / acollect"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body_term = self._children[0]
        target = self._payload["target"]
        carry = self._payload["carry"]
        tag: tuple[object, ...] = () if target is UNSET else (target,)

        async def athunk(rt: Runtime) -> object:
            service = rt.ctx.get(RayService, *tag)
            attrs = dict(rt.ctx.attrs) if carry and rt.ctx.attrs else None
            result = await service.aexecute(body_term, attrs=attrs)
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _one(result)
            return result

        return athunk
