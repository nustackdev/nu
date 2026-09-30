"""Presets over ``nustd.mp_pool``: policy the pool deliberately leaves out.

The pool owns processes and nothing else. No size, no warmth, no scheduling.
Whatever a caller wants on top is policy, and policy lives here, built on the
pool's own operations and never adding any to it.

``spares`` is the one preset so far: a shelf of workers already up and idle,
so taking one is a list pop instead of a spawn and an interpreter's worth of
imports.

- ``Spares`` - the shelf, a fabric. It launches into the ``WorkerPool`` bound
  around it and refills itself in the background.
- ``SparesRef`` - the fabric ref, EMPTY when no shelf is bound.
- ``TakeSpare`` - the interaction: one worker id, off the shelf when there is
  one, a cold ``Launch`` when there is not or no shelf is bound at all.
- ``spares(size)`` - the ``Provide`` that opens a shelf.

Why a resource and not pure Nu: a take has to test and pop the shelf with
nothing in between, or two branches taking at once are handed the same
worker. Nu has no atomic pop over a list, so the shelf is a small class whose
pop runs with no await point inside it::

    Provide(WorkerPool, {"name": "nu"},
        With(spares(2),
            body=Let("w", TakeSpare(), Dispatch(body=resident, worker=ObjectRef("w"))),
        ),
    )

A taken worker is an ordinary pool worker. The shelf forgets it, and it is
killed, waited on and reaped exactly like one that came from ``Launch``.
"""

from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING

from nu.context import FabricRef
from nu.context.fabric import Provide
from nu.engine.structure import Declared
from nu.lang import Nu, ScalarAction

from .interactions import _require_pool
from .refs import PoolRef
from .resources import WorkerPool


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Context, Runtime


__all__ = ["Spares", "SparesRef", "TakeSpare", "spares"]


class Spares:
    """Workers already up and idle, so a take does not wait for a spawn.

    Opened inside the ``Provide(WorkerPool, ...)`` it launches into, and so
    closed before it: the shelf is emptied while the pool is still there to
    empty it into.

    Args:
        size: how many idle workers to keep up. Zero keeps none, which makes
            every take a cold launch without taking the term out of the tree.

    Notes:
        - Async lifecycle only. Refilling is background tasks on the running
          loop, which a sync run does not have.
        - Every spare comes up holding the pool's own ``init``. A take never
          overrides it; a caller that needs a different bracket launches.
        - A spare that died on the shelf is reaped at take time and skipped,
          never handed out.
        - Refilling is best effort. A launch that fails in the background has
          nobody to raise at, so it is dropped, and the next take launches
          cold in front of whoever is waiting and raises there.
    """

    def __init__(self, size: int = 1) -> None:
        self.size = size
        self._pool: WorkerPool | None = None
        self._shelf: list[int] = []
        # Launches run on worker threads that outlive a cancelled await, so
        # the shelf, the closed flag and the in-flight count share one lock:
        # a finished launch either shelves before close or kills itself.
        self._lock = threading.Lock()
        self._inflight = 0
        # Held only so a refill task is not collected mid-launch.
        self._filling: set[asyncio.Task] = set()
        # Closed until a bracket opens it, so a shelf nobody opened launches
        # nothing and a late refill after teardown shelves nothing.
        self._closed = True

    # --- lifecycle -------------------------------------------------------

    async def asetup(self, ctx: Context) -> None:
        """Take the pool this shelf launches into, and start filling."""
        try:
            self._pool = ctx.get(WorkerPool)
        except LookupError:
            msg = (
                "spares needs a WorkerPool bound around it; open it inside Provide(WorkerPool, ...)"
            )
            raise RuntimeError(msg) from None
        self._closed = False
        self._fill()

    async def acleanup(self) -> None:
        """Close the shelf and kill whatever is on it.

        Deliberately with no await points, for the reason
        ``WorkerPool.acleanup`` has none: a cancellation landing here must not
        leave processes behind. A refill still launching is not waited for.
        Its thread checks the closed flag under the shelf lock once the
        launch returns and kills the worker itself, whether or not the pool
        has already been torn down around it.
        """
        with self._lock:
            self._closed = True
            shelf, self._shelf = self._shelf, []
        self._filling.clear()
        if self._pool is not None:
            for wid in reversed(shelf):
                self._pool.kill(wid)

    # --- taking ----------------------------------------------------------

    def _pop(self, pool: WorkerPool) -> int | None:
        """The shelf's first live worker, or None. No await points inside.

        Nothing yields between the test and the pop, so two branches taking
        at the same moment can never be handed the same worker.
        """
        while True:
            with self._lock:
                if not self._shelf:
                    return None
                wid = self._shelf.pop(0)
            if pool.alive(wid):
                return wid
            # A spare that died on the shelf is still the pool's to reap.
            pool.kill(wid)

    def _bound_pool(self) -> WorkerPool:
        if self._pool is None:
            msg = "spares was asked for a worker before its bracket opened"
            raise RuntimeError(msg)
        return self._pool

    async def atake(self) -> int:
        """One worker, ready now: the shelf's if it has one, a fresh launch if not."""
        pool = self._bound_pool()
        wid = self._pop(pool)
        self._fill()
        return await pool.alaunch() if wid is None else wid

    def take(self) -> int:
        """Sync ``atake``. Pops the same shelf; refills only when a loop is running."""
        pool = self._bound_pool()
        wid = self._pop(pool)
        self._fill()
        return pool.launch() if wid is None else wid

    @property
    def shelf(self) -> list[int]:
        """The ids on the shelf right now, oldest first. A snapshot."""
        with self._lock:
            return list(self._shelf)

    # --- refilling -------------------------------------------------------

    def _fill(self) -> None:
        """Top the shelf back up in the background, counting launches in flight."""
        if self._pool is None:
            return
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return
        with self._lock:
            if self._closed:
                return
            missing = self.size - len(self._shelf) - self._inflight
            self._inflight += max(missing, 0)
        for _ in range(missing):
            task = asyncio.ensure_future(asyncio.to_thread(self._one))
            self._filling.add(task)
            task.add_done_callback(self._filling.discard)

    def _one(self) -> None:
        """Launch one spare and shelve it, or kill it if the shelf closed meanwhile.

        Runs on a worker thread, start to finish. Shelving happens here and
        not back on the loop, so a cancelled await or a closed loop can never
        strand a worker that came up after the shelf was torn down.
        """
        pool = self._pool
        wid: int | None = None
        try:
            if pool is not None:
                wid = pool.launch()
        except Exception:
            wid = None
        finally:
            with self._lock:
                # Stop counting as in flight in the same step that shelves,
                # so a take never sees both the spare and its launch.
                self._inflight -= 1
                shelved = wid is not None and not self._closed
                if shelved:
                    self._shelf.append(wid)
        if wid is not None and not shelved:
            pool.kill(wid)  # type: ignore[union-attr]


class SparesRef(FabricRef):
    """The ``Spares`` bound on the Context. EMPTY when nothing is."""

    fabric = Spares


class TakeSpare(ScalarAction):
    """One worker to run things on, off the shelf when the shelf has one.

    Stands exactly where ``Launch()`` stands and yields the same kind of id,
    so a tree with no shelf bound behaves as if it said ``Launch()``.

    Args:
        pool: the node yielding the ``WorkerPool``. Defaults to the untagged
            ``PoolRef``.
        spares: the node yielding the ``Spares``. Defaults to the untagged
            ``SparesRef``.

    Notes:
        - An action rather than a query for the reason ``Launch`` is one:
          evaluating it twice hands back two workers.
        - With no shelf bound it launches cold into the pool, so the preset
          can be dropped from a tree without touching the takes.
        - The worker it yields belongs to the pool from then on. ``Kill`` and
          ``Wait`` treat it like any other.

    Yields:
        The worker's id, an int.

    Example:
        Let("w", TakeSpare(), Dispatch(body=resident, worker=ObjectRef("w")))
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, pool: Nu | None = None, spares: Nu | None = None) -> None:
        super().__init__(
            PoolRef() if pool is None else pool,
            SparesRef() if spares is None else spares,
        )

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the sync take thunk."""

        def thunk(rt: Runtime) -> object:
            pool = children[0](rt)
            shelf = children[1](rt)
            if isinstance(shelf, Spares):
                return shelf.take()
            return _require_pool(pool).launch()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        """Build the async take thunk, falling back to a cold launch with no shelf."""

        async def athunk(rt: Runtime) -> object:
            pool = await children[0](rt)
            shelf = await children[1](rt)
            if isinstance(shelf, Spares):
                return await shelf.atake()
            return await _require_pool(pool).alaunch()

        return athunk


def spares(size: int = 1) -> Provide:
    """A shelf of ``size`` idle workers, refilled as they are taken.

    Goes inside the ``Provide(WorkerPool, ...)`` it launches into. Takes are
    ``TakeSpare()``.

    Args:
        size: how many to keep up. Zero keeps none, every take launches cold.
    """
    return Provide(Spares, {"size": size})
