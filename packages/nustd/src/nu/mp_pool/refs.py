"""``PoolRef``: the fabric ref that resolves the ``WorkerPool`` bound on ctx.

A plain ``FabricRef`` and nothing more: the address is the fabric *type*, so
the read is the untagged binding. There is no tag child and no tag payload -
same shape ``nu.mp.MpWorkerRef`` settled on.

It also carries this fabric's fluent surface. ``PoolRef().launch()`` and
``Launch(PoolRef())`` build the same term; the methods exist so a pool ref
reads like the thing you address rather than an argument you thread, exactly
the way the Form mixins hang ``set()`` off an item ref.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context import FabricRef

from .resources import WorkerPool


if TYPE_CHECKING:
    from nu.core.spans.bracket import _LifecycleBracket
    from nu.lang import Nu

    from .interactions import Alive, Dispatch, Kill, Launch, Running, Teleport, Workers


__all__ = ["PoolRef"]


class PoolRef(FabricRef):
    """The ``WorkerPool`` bound on the Context.

    Notes:
        - Reading it is a lookup and nothing else. No process is spawned and
          no worker is contacted; every interaction in this fabric takes this
          ref as a child and does the work itself.
        - It is slot 0 of ``Dispatch`` and ``Kill``, which is what satisfies
          the ``ref_slots`` law for those two: a VOID mutator has to land its
          write through a Ref to be observable at all.
        - The lookup runs against whichever Context is in force where the ref
          sits, so a ``PoolRef`` inside a dispatched body reads the worker
          process's own Context, not the parent's.
        - The methods below are a convenience over the constructors, not a
          second way of building anything: each one returns the same term the
          matching ``Launch(...)`` / ``Kill(...)`` call would.

    Yields:
        The bound ``WorkerPool``. EMPTY when nothing is bound.

    Example:
        Provide(WorkerPool, {"name": "nu"},
            Let("w", PoolRef().launch(), PoolRef().kill(AttrRef("w"))),
        )
    """

    fabric = WorkerPool

    # The interactions import this module, so every import below is lazy -
    # the same shape nu's own Form mixins use for the same reason.

    def launch(self, init: _LifecycleBracket | Nu | None = None) -> Launch:
        """A ``Launch`` on this pool: spawn a worker, yield its id."""
        from .interactions import Launch

        return Launch(self, init)

    def dispatch(self, body: Nu, worker: object = None, *, carry: bool = False) -> Dispatch:
        """A ``Dispatch`` on this pool: ship ``body`` to ``worker``, do not wait."""
        from .interactions import Dispatch

        return Dispatch(self, body, worker, carry=carry)

    def teleport(self, body: Nu, worker: object = None, *, carry: bool = False) -> Teleport:
        """A ``Teleport`` on this pool: run ``body`` at ``worker``, yield its value."""
        from .interactions import Teleport

        return Teleport(self, body, worker, carry=carry)

    def kill(self, worker: object = None) -> Kill:
        """A ``Kill`` on this pool: end ``worker`` now and reap it."""
        from .interactions import Kill

        return Kill(self, worker)

    def alive(self, worker: object = None) -> Alive:
        """An ``Alive`` read on this pool: is ``worker`` still a live process."""
        from .interactions import Alive

        return Alive(self, worker)

    def running(self, worker: object = None) -> Running:
        """A ``Running`` read on this pool: is a dispatched body still going."""
        from .interactions import Running

        return Running(self, worker)

    def workers(self) -> Workers:
        """A ``Workers`` stream over this pool: every id it still tracks."""
        from .interactions import Workers

        return Workers(self)
