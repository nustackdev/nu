"""nustd.mp_pool - the pool of worker processes, as one fabric.

``nustd.mp`` is the fabric of ONE process: its whole lifecycle is the
``With`` / ``Provide`` bracket and it stays purely declarative.
``nustd.mp_pool`` is the sibling where **the pool itself is the fabric**. One
``Provide`` at the top of a tree owns N worker processes, and because the
fabric spans many processes it legitimately owns interactions over them -
launch a worker, run a tree on worker id X, interrupt, stop or kill it, read
its status. Those are statements about the fabric's contents, not
imperative escapes.

- ``pool(...)`` - the preset that stands a pool up: every knob keyword-only
  (``name``, ``init``, ``grace``, ``spares``, ``ready_timeout``,
  ``ack_timeout``), plus ``tags`` and ``body``.
- ``WorkerPool`` - the resource. Owns ``{id -> process}``, keeps ``spares``
  warm, and on close stops every worker at once under one budget,
  ``grace``. No size, no scheduling, no acquire/release: that is policy and
  belongs to callers. Its sync and async Python methods are public too.
- ``PoolRef(tag=)`` - the fabric ref. Reading it is a lookup and nothing
  else. It also carries the fluent form of every interaction below.
- the worker toolkit, policy-free, each verb sync and async:
  ``Launch`` / ``Workers``; ``Teleport`` / ``Dispatch`` / ``Cancel``;
  ``Interrupt`` / ``Stop`` / ``Kill``; ``Status`` / ``Wait``.
- ``WorkerStatus`` - what ``Status``, ``Stop`` and ``Wait`` yield: state,
  pid, pgid, name, started_at, jobs, and once gone exitcode and cause.
- errors named after the state: ``WorkerGone`` (with ``cause`` and
  ``exitcode``), ``PoolClosed``, ``Interrupted``, ``UnknownWorker``.

The guarantees: nothing outlives the pool or the host (workers lead their own
process group and watch the parent), Ctrl+C in a terminal reaches only the
host, the event loop never blocks, every pending request gets an answer, and
every worker has a pid and a status, readable after it is gone.

Everything is Nu. Every worker id, job id and the ``init`` override is a
**child**, never payload, so a target can come from a ``Ref``, a mem slot or
any query. Here ``nu.let`` holds the launched worker's id for the body::

    POOL = PoolRef()
    prog = pool(
        name="cells",
        init=nu.Provide(dict, {}, tag=Ticks),
        spares=2,
        body=nu.let(POOL.launch(), lambda w: nu.Sequential(
            POOL.dispatch(ticker, w),
            nu.Print(nu.STDOUT, POOL.teleport(Ticks.n, w)),
            nu.Print(nu.STDOUT, POOL.status(w)),
            POOL.stop(w),
        )),
    )

The one exception to "no payload" is a ``Dispatch`` body, which has to be
payload because a Flow does not compose in an Interaction's slots. The
consequence is worth knowing before you rely on it: a body in payload is not
part of the tree, so no walker, rewrite, analysis or render reaches it, and
the caller has to apply whatever passes it needs (``nustd.kv.auto_flow_atomic``
among them) to the body itself before building the ``Dispatch``.

``Dispatch`` vs ``Teleport`` is the crux. ``Dispatch`` returns as soon as the
child acknowledges receipt and yields a job id, so it is the verb for
resident, never-terminating trees - a ``ReactEvery`` body using it never
blocks. ``Teleport`` is request/reply, for work that finishes.

Worker ids are monotonic ints and are never reused, so a stale id is
detectably gone rather than silently a different worker. Only the
``"spawn"`` start method is supported - the child gets a clean interpreter.
The ``init`` bracket and every body go through cloudpickle (``nu.lang.wire``),
so closures and classes defined inside a function travel too.
"""

from __future__ import annotations

from . import presets
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
from .presets import pool
from .refs import PoolRef
from .resources import (
    Interrupted,
    PoolClosed,
    UnknownWorker,
    WorkerGone,
    WorkerPool,
    WorkerStatus,
)


__all__ = [
    "Cancel",
    "Dispatch",
    "Interrupt",
    "Interrupted",
    "Kill",
    "Launch",
    "PoolClosed",
    "PoolRef",
    "Status",
    "Stop",
    "Teleport",
    "UnknownWorker",
    "Wait",
    "WorkerGone",
    "WorkerPool",
    "WorkerStatus",
    "Workers",
    "pool",
    "presets",
]
