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
    """Runs the body on a ``RayService`` actor instead of in the caller.

    A policy over where, not what: the body is captured as a term and is
    never evaluated locally. On each evaluation the tagged ``RayService`` is
    read off the Context, the term is shipped to its actor, and the actor
    compiles and evaluates it against its own Context before the value comes
    back. Dropping a Teleport moves the work, it does not change it.

    Args:
        body: the Nu to run on the actor. Captured as a term, never run on
            the driver.

    Notes:
        - ``target`` is the tag the ``RayService`` was bound under, passed
          verbatim to ``ctx.get``: omit it for a bare ``Provide``, the index
          for ``ProvideList``, the key for ``ProvideDict``. ``None`` is a
          usable tag, distinct from omitting it.
        - ``carry=True`` copies the caller's ``ctx.attrs`` into a shallow
          copy of the actor's Context for that one execution, so loop
          variables bound by ``Map`` or ``Filter`` reach the body. Without
          it the body sees only what the actor's Context already holds.
        - The body resolves its refs against the actor's Context, built on
          the actor by the ``RayService``'s ``init`` bracket or
          ``ctx_builder``. Anything bound around the Teleport in the
          caller's tree is not visible there.
        - The body term crosses the wire through ray's serializer, so it and
          everything it captures must be picklable.
        - Async only. The sync path raises; run with ``arun``, ``afirst`` or
          ``acollect``.
        - The wait is an await on the actor's future, so Teleports to
          different services overlap under ``Parallel``. Two Teleports at
          the same service still queue on that actor.
        - A stream-rooted body evaluates to an async generator, which does
          not survive the actor boundary. Reduce it inside the body, with
          ``Collect`` or a fold, before teleporting.
        - An exception raised on the actor surfaces here when the result is
          awaited.

    Yields:
        The value the body's root produced on the actor, None for an
        effect-only body. When the body is a stream the collapsed remote
        value is yielded as a one-item stream, and a None result yields an
        empty one.

    Example:
        Provide(RayCluster, {"address": "auto"},
            ProvideList(RayService, [{"num_cpus": 4}, {"num_cpus": 4}],
                Parallel(
                    Teleport(shard_0, target=0),
                    Teleport(shard_1, target=1),
                ),
            ),
        )
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
