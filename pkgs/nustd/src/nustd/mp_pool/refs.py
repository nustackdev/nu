"""``PoolRef``: the fabric ref that resolves the ``WorkerPool`` bound on ctx.

A ``FabricRef`` with an optional tag, the shape ``nustd.cluster``'s
``RayServiceRef`` has: ``PoolRef()`` reads the untagged pool, ``PoolRef("gpu")``
the one a ``pool(..., tags=("gpu",))`` bound, so two pools can live in one
scope. The tag is the address, so it is payload; nothing a caller computes at
run time goes there.

It also carries this fabric's fluent surface. ``PoolRef().launch()`` and
``Launch(PoolRef())`` build the same term; the methods exist so a pool ref
reads like the thing you address rather than an argument you thread, exactly
the way the Form mixins hang ``set()`` off an item ref.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context import FabricRef
from nu.lang.null import Null
from nu.lang.sentinels import UNSET

from .resources import WorkerPool


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.core.spans.bracket import _LifecycleBracket
    from nu.lang import Nu
    from nu.lang.runtime import Runtime

    from .interactions import (
        Cancel,
        Dispatch,
        Interrupt,
        Kill,
        Launch,
        Status,
        Stop,
        Teleport,
        Wait,
        Workers,
    )


__all__ = ["PoolRef"]


class PoolRef(FabricRef):
    """The ``WorkerPool`` bound on the Context, at ``tag`` when one is given.

    Args:
        tag: the tag the pool was bound under (``pool(..., tags=(tag,))`` or
            ``Provide(WorkerPool, ..., tag=tag)``). Omit it for the untagged
            pool.

    Notes:
        - Reading it is a lookup and nothing else. No process is spawned and
          no worker is contacted; every interaction in this fabric takes this
          ref as a child and does the work itself.
        - A tagless ref never reads a tagged pool, and a tagged one never
          falls back to the untagged pool: Context resolution goes from more
          tags to fewer, and only the binding's own tag reaches it.
        - ``None`` is a usable tag, distinct from omitting the tag.
        - It is slot 0 of every mutating interaction, which is what satisfies
          the ``ref_slots`` law for the VOID ones (``Cancel``, ``Interrupt``,
          ``Kill``): a VOID mutator has to land its write through a Ref to be
          observable at all.
        - The lookup runs against whichever Context is in force where the ref
          sits, so a ``PoolRef`` inside a dispatched body reads the worker
          process's own Context, not the parent's.
        - The methods below are a convenience over the constructors, not a
          second way of building anything: each one returns the same term the
          matching ``Launch(...)`` / ``Stop(...)`` call would, with this ref
          (and so its tag) in the pool slot.

    Yields:
        The bound ``WorkerPool``. NULL when nothing is bound at that tag.

    Example:
        pool = PoolRef()
        mp_pool.pool(name="cells", body=nu.let(pool.launch(), lambda w: pool.stop(w)))
    """

    fabric = WorkerPool

    def __init__(self, tag: object = UNSET) -> None:
        super().__init__()
        self._payload["tag"] = tag

    def _tags(self) -> tuple[object, ...]:
        tag = self._payload["tag"]
        return () if tag is UNSET else (tag,)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fabric = children[0]
        tags = self._tags()

        def thunk(rt: Runtime) -> object:
            f = fabric(rt)
            if rt.ctx.fabrics.has(f, *tags):
                return rt.ctx.fabrics.get(f, *tags)
            return Null(f.__qualname__)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fabric = children[0]
        tags = self._tags()

        async def athunk(rt: Runtime) -> object:
            f = await fabric(rt)
            if rt.ctx.fabrics.has(f, *tags):
                return rt.ctx.fabrics.get(f, *tags)
            return Null(f.__qualname__)

        return athunk

    # The interactions import this module, so every import below is lazy -
    # the same shape nu's own Form mixins use for the same reason.

    def launch(self, init: _LifecycleBracket | Nu | None = None) -> Launch:
        """A ``Launch`` on this pool: hand out a worker, yield its id."""
        from .interactions import Launch

        return Launch(self, init)

    def workers(self) -> Workers:
        """A ``Workers`` stream over this pool: every live worker handed out."""
        from .interactions import Workers

        return Workers(self)

    def teleport(self, body: Nu, worker: object = None, *, carry: bool = False) -> Teleport:
        """A ``Teleport`` on this pool: run ``body`` at ``worker``, yield its value."""
        from .interactions import Teleport

        return Teleport(self, body, worker, carry=carry)

    def dispatch(self, body: Nu, worker: object = None, *, carry: bool = False) -> Dispatch:
        """A ``Dispatch`` on this pool: ship ``body`` to ``worker``, yield the job id."""
        from .interactions import Dispatch

        return Dispatch(self, body, worker, carry=carry)

    def cancel(self, worker: object = None, job: object = None) -> Cancel:
        """A ``Cancel`` on this pool: cancel dispatched ``job`` on ``worker``."""
        from .interactions import Cancel

        return Cancel(self, worker, job)

    def interrupt(self, worker: object = None) -> Interrupt:
        """An ``Interrupt`` on this pool: end every job on ``worker``, keep the worker."""
        from .interactions import Interrupt

        return Interrupt(self, worker)

    def stop(self, worker: object = None, grace: object = None) -> Stop:
        """A ``Stop`` on this pool: end ``worker`` politely within ``grace``, yield its status."""
        from .interactions import Stop

        return Stop(self, worker, grace)

    def kill(self, worker: object = None) -> Kill:
        """A ``Kill`` on this pool: SIGKILL ``worker``'s group now."""
        from .interactions import Kill

        return Kill(self, worker)

    def status(self, worker: object = None) -> Status:
        """A ``Status`` read on this pool: ``worker``'s record, alive or gone."""
        from .interactions import Status

        return Status(self, worker)

    def wait(self, worker: object = None, timeout: object = None) -> Wait:
        """A ``Wait`` on this pool: until ``worker`` exits or ``timeout``, yield its status."""
        from .interactions import Wait

        return Wait(self, worker, timeout)
