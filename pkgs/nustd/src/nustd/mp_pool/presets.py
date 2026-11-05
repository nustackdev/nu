"""Presets over ``nustd.mp_pool``: the bracket that stands a pool up.

``pool(...)`` is the ``Provide`` a program puts around the tree that uses the
workers. Every ``WorkerPool`` knob is a keyword here, plus ``tags`` for a pool
that is not the only one in scope, and ``body`` for the tree itself::

    POOL = mp_pool.PoolRef()
    prog = mp_pool.pool(
        name="cells",
        init=nu.Provide(dict, {}, tag=Ticks),
        spares=2,
        grace=5.0,
        body=nu.let(POOL.launch(), lambda w: POOL.stop(w)),
    )

Leaving the bracket stops every worker still up, all at once, within
``grace``. It is re-exported at package level as ``nustd.mp_pool.pool``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.fabric import Provide

from .resources import WorkerPool


if TYPE_CHECKING:
    from collections.abc import Sequence

    from nu.core.spans.bracket import _LifecycleBracket
    from nu.lang import Nu


__all__ = ["pool"]


def pool(
    *,
    init: _LifecycleBracket | None = None,
    name: str = "nu",
    grace: float = 5.0,
    spares: int = 0,
    ready_timeout: float = 30.0,
    ack_timeout: float = 10.0,
    start_method: str = "spawn",
    tags: Sequence[object] = (),
    body: Nu | None = None,
) -> Provide:
    """Stands up a ``WorkerPool`` for the body's duration and stops every worker at the end.

    Args:
        init: the bracket each worker enters once, inside its own process,
            and tears down when it stops. ``Launch`` can override it per
            worker.
        name: the pool's name; ``ps`` shows each worker as
            ``nu:{name}-{id}``.
        grace: the budget for ending a worker, and for the close: the
            ``stop`` frame, then SIGINT at 60%, SIGTERM at 80%, SIGKILL at
            95%, done by ``grace``.
        spares: warm workers kept on a shelf so ``Launch`` takes one instead
            of waiting for a spawn. Zero keeps none.
        ready_timeout: how long a launch waits for a worker's ``ready``.
        ack_timeout: how long a dispatch waits for the worker's ack.
        start_method: ``"spawn"``, the only one supported.
        tags: tags for the binding, so two pools in one scope can be told
            apart; read one back with ``PoolRef(tag)``.
        body: the tree that runs with the pool bound. Leave it out to use the
            preset inside a ``With``.

    Notes:
        - Kwargs are payload, frozen when the tree is built, like any
          ``Provide``'s.
        - Under ``nu.arun`` the close runs on the loop without blocking it;
          under ``nu.run`` it blocks the calling thread, never longer than
          ``grace`` plus a moment.

    Yields:
        A ``Provide`` bracket binding the ``WorkerPool``; transparent, it
        yields whatever ``body`` yields.

    Example:
        nu.run(mp_pool.pool(name="cells", spares=1, body=tree))
    """
    kwargs = {
        "init": init,
        "name": name,
        "grace": grace,
        "spares": spares,
        "ready_timeout": ready_timeout,
        "ack_timeout": ack_timeout,
        "start_method": start_method,
    }
    return Provide(WorkerPool, kwargs, body, tags=tuple(tags))
