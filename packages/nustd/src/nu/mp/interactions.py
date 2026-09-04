"""``Teleport``: ship the body to an ``MpWorker`` child process for execution.

Same shape as ``nu.cluster.Teleport`` but targets ``MpWorker`` and works on
both sync and async runtimes - the parent-side pipe read/write is blocking
either way (async wraps it in ``asyncio.to_thread``).

Policy: captures the body term (slot 0), resolves an ``MpWorker`` from ctx
by tag, and calls ``worker.execute(body_term)`` on it.

``target`` is a single hashable used verbatim as the tag; omit (``UNSET``)
for the untagged singleton. ``target=None`` is a legitimate tag.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Attr, Cardinality, Policy
from nu.lang.sentinels import UNSET

from .resources import MpWorker


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.lang import Nu
    from nu.lang.runtime import Runtime


__all__ = ["Teleport"]


def _one_sync(value: object) -> Iterator:
    if value is not None:
        yield value


async def _one_async(value: object) -> AsyncIterator:
    if value is not None:
        yield value


class Teleport(Policy):
    """Runs the body in an ``MpWorker`` child process instead of in the caller.

    A policy over where, not what: the body is captured as a term and is
    never evaluated locally. On each evaluation the tagged ``MpWorker`` is
    read off the Context, the term goes down the pipe, and the child
    compiles and evaluates it against its own Context before the value comes
    back. Dropping a Teleport moves the work, it does not change it.

    Args:
        body: the Nu to run in the worker. Captured as a term, never run in
            the caller's process.

    Notes:
        - ``target`` is the tag the ``MpWorker`` was bound under, passed
          verbatim to ``ctx.get``: omit it for a bare ``Provide``, the index
          for ``ProvideList``, the key for ``ProvideDict``. ``None`` is a
          usable tag, distinct from omitting it.
        - ``carry=True`` copies the caller's ``ctx.attrs`` into a shallow
          copy of the worker's Context for that one execution, so loop
          variables bound by ``Map`` or ``Filter`` reach the body. Without
          it the body sees only what the worker's Context already holds.
        - The body resolves its refs against the worker's Context, built in
          the child by the ``MpWorker``'s ``init`` bracket or
          ``ctx_builder``. Anything bound around the Teleport in the
          caller's tree is not visible there.
        - Everything crossing the pipe is pickled, so the body term and what
          it captures must be pickleable.
        - Both runtimes work. The pipe read blocks either way; the sync path
          blocks the calling thread, the async path waits off-thread so
          sibling work keeps running.
        - A worker serves one request at a time behind a lock, so two
          Teleports at the same target serialize even under ``Parallel``.
          Parallelism comes from binding a fleet and targeting each worker.
        - A stream-rooted body evaluates to an async generator, which cannot
          be pickled back. Reduce it inside the body, with ``Collect`` or a
          fold, before teleporting.
        - An exception raised in the child is sent back and re-raised here.

    Yields:
        The value the body's root produced in the worker, None for an
        effect-only body. When the body is a stream the collapsed remote
        value is yielded as a one-item stream, and a None result yields an
        empty one.

    Example:
        Provide(MpWorker, {"name": "solo"},
            Teleport(Collect(heavy_stream)),
        )

        ProvideList(MpWorker, [{"name": "w-0"}, {"name": "w-1"}],
            Parallel(
                Teleport(shard_0, target=0),
                Teleport(shard_1, target=1),
            ),
        )
    """

    def __init__(self, body: Nu, *, target: object = UNSET, carry: bool = False) -> None:
        super().__init__(body)
        self._payload["target"] = target
        self._payload["carry"] = carry

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body_term = self._children[0]
        target = self._payload["target"]
        carry = self._payload["carry"]
        tag: tuple[object, ...] = () if target is UNSET else (target,)

        def thunk(rt: Runtime) -> object:
            worker = rt.ctx.get(MpWorker, *tag)
            attrs = dict(rt.ctx.attrs) if carry and rt.ctx.attrs else None
            result = worker.execute(body_term, attrs=attrs)
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _one_sync(result)
            return result

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body_term = self._children[0]
        target = self._payload["target"]
        carry = self._payload["carry"]
        tag: tuple[object, ...] = () if target is UNSET else (target,)

        async def athunk(rt: Runtime) -> object:
            worker = rt.ctx.get(MpWorker, *tag)
            attrs = dict(rt.ctx.attrs) if carry and rt.ctx.attrs else None
            result = await worker.aexecute(body_term, attrs=attrs)
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _one_async(result)
            return result

        return athunk
