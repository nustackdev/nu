"""nu.mp_pool - the pool of worker processes, as one fabric.

``nu.mp`` is the fabric of ONE process: its whole lifecycle is the
``With`` / ``Provide`` bracket and it stays purely declarative.
``nu.mp_pool`` is the sibling where **the pool itself is the fabric**. One
``Provide`` at the top of a tree owns N worker processes, and because the
fabric now spans many processes it legitimately owns interactions over them -
launch a worker, kill a worker, run a tree on worker id X. Those are
statements about the fabric's contents, not imperative escapes.

- ``WorkerPool`` - the resource. Owns ``{id -> process}``. Bracket close kills
  every worker, newest first. No size, no warmth, no scheduling, no
  acquire/release: that is policy and belongs to callers.
- ``PoolRef`` - the fabric ref. Reading it is a lookup and nothing else. It
  also carries the fluent form of every interaction below.
- ``Launch`` / ``Dispatch`` / ``Teleport`` / ``Kill`` / ``Alive`` /
  ``Running`` / ``Workers`` - the interactions.

Everything is Nu. Every worker id and the ``init`` override is a **child**,
never payload, so a target can come from a ``Ref``, an ``AttrRef`` or any
query::

    Provide(WorkerPool, {"init": With(Provide(Store, {...})), "name": "nu"},
        Sequential(
            SetCmd(AttrRef("w"), Launch()),
            Dispatch(body=resident_tree, worker=AttrRef("w")),
            SetCmd(AttrRef("n"), Teleport(body=Add(1, 2), worker=AttrRef("w"))),
            Kill(worker=AttrRef("w")),
        ),
    )

The interactions are also reachable off the ref, which is the same term by a
shorter road::

    pool = PoolRef()
    Sequential(
        SetCmd(AttrRef("w"), pool.launch()),
        pool.dispatch(resident_tree, AttrRef("w")),
        pool.kill(AttrRef("w")),
    )

The one exception to "no payload" is a ``Dispatch`` body, which has to be
payload because a Command cannot hold a Flow in a child slot. The consequence
is worth knowing before you rely on it: a body in payload is not part of the
tree, so no walker, rewrite, analysis or render reaches it, and the caller has
to apply whatever passes it needs (``nu.kv.auto_flow_atomic`` among them) to
the body itself before building the ``Dispatch``.

``Dispatch`` vs ``Teleport`` is the crux. ``Dispatch`` returns as soon as the
child acknowledges receipt, so it is the verb for resident, never-terminating
trees - a ``ReactForever`` body using it never blocks. ``Teleport`` is
request/reply, for work that finishes.

Worker ids are monotonic ints and are never reused, so a stale id is
detectably dead rather than silently a different worker.

The default ``start_method`` is ``"spawn"`` - the child gets a clean
interpreter, so the ``init`` bracket and any dispatched body must be
pickleable (top-level in a module, no closures).
"""

from __future__ import annotations

from .interactions import Alive, Dispatch, Kill, Launch, Running, Teleport, Workers
from .refs import PoolRef
from .resources import UnknownWorker, WorkerGone, WorkerPool


__all__ = [
    "Alive",
    "Dispatch",
    "Kill",
    "Launch",
    "PoolRef",
    "Running",
    "Teleport",
    "UnknownWorker",
    "WorkerGone",
    "WorkerPool",
    "Workers",
]
