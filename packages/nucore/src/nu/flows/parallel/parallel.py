"""Parallel: join-on-all fan-in, smart + forced variants.

- ``Parallel`` - smart. Sync uses the thread pool; async places each child
  per ``Attr.ON_LOOP`` (with per-child ``(child, "threaded"|"async")``
  overrides taking precedence over the smart choice).
- ``ParallelThreaded`` - every child forced onto a worker thread under
  async. Rejects subtrees holding an async-only atom (compile-time law).
- ``ParallelAsync`` - every child forced onto the loop under async; the
  whole subtree becomes async-only, so sync ``run`` refuses it up front.
  Rejects subtrees holding a sync-only atom.
- ``Gather`` - alias for ``Parallel``; kept for the yield-collecting name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang.attributes.execution import ExecOrder
from nu.lang.kinds import Strategy

from . import _scheduling
from ._base import _ParallelBase


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["Gather", "Parallel", "ParallelAsync", "ParallelThreaded"]


class Parallel(_ParallelBase, Strategy):
    """Runs its children concurrently and joins once every one has finished.

    Each item is either a child or a ``(child, "threaded"|"async")`` pair
    that pins that one child's placement. Sync ``run`` fans every child out
    to the Budget's thread pool (or evaluates in order when
    ``max_parallel == 1``). Async ``arun`` places each child on a worker
    thread or on the loop; an unpinned child follows the smart choice folded
    from its subtree (``Attr.ON_LOOP``), a pinned child follows its own
    ``"threaded"``/``"async"`` tag regardless of that fold. A smart
    ``Parallel`` cannot host a Dyn child, since the smart fold needs every
    child's async affinity visible at compile time; ``ParallelThreaded`` /
    ``ParallelAsync`` force a mode instead of folding one.

    Args:
        *items: children to run concurrently, each either a Nu instance or
            a ``(child, "threaded"|"async")`` pair pinning its placement.

    Notes:
        - This is the ``|`` composition: ``a | b`` builds ``Parallel(a, b)``.
        - A child that raises propagates once its slot is awaited; the other
          children keep running and are not cancelled.
        - Nothing here bounds how long a hung child is waited on - concurrent
          does not mean supervised.

    Example:
        >>> nu.run(nu.Parallel(nu.SetCmd(nu.AttrRef("a"), 1), nu.SetCmd(nu.AttrRef("b"), 2)))[1].attrs["a"]
        1
    """

    _exec_order = Declared(value=ExecOrder.PARALLEL, name="exec_order")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        per_child = self._payload.get("parallel_modes")
        force = self._FORCE_MODE

        def thunk(rt: Runtime) -> None:
            _scheduling.eval_parallel(
                rt, rt.program.children[nid], per_child=per_child, force=force
            )

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        per_child = self._payload.get("parallel_modes")
        force = self._FORCE_MODE

        async def athunk(rt: Runtime) -> None:
            await _scheduling.aeval_parallel(
                rt, rt.program.children[nid], per_child=per_child, force=force
            )

        return athunk


class ParallelThreaded(Parallel):
    """Parallel with every child forced onto a worker thread under async.

    The sync path is unchanged from ``Parallel`` (Budget's thread pool).
    Under async, the smart fold and any per-child ``(child, "async")`` tags
    are both overridden: every child lands on a worker thread.

    Args:
        *items: children to run concurrently. A per-child mode tag can still
            be passed for API symmetry with ``Parallel`` but has no effect,
            since ``_FORCE_MODE`` always wins.

    Notes:
        - Rejected at compile time when a child's subtree folds an
          async-only atom, since a forced thread cannot host one - the
          ``parallel_threaded_no_async_only_child`` law.

    Yields:
        VOID, inherited from ``Parallel``.
    """

    _FORCE_MODE = "threaded"


class ParallelAsync(Parallel):
    """Parallel with every child forced onto the loop under async.

    Declaring ``requires_async`` makes the whole subtree async-only, so a
    sync ``run`` over it raises up front rather than reaching the thunk
    below. Under ``arun``, the smart fold and any per-child
    ``(child, "threaded")`` tags are both overridden: every child runs on
    the loop.

    Args:
        *items: children to run concurrently. A per-child mode tag can still
            be passed for API symmetry with ``Parallel`` but has no effect,
            since ``_FORCE_MODE`` always wins.

    Notes:
        - Rejected at compile time when a child's subtree folds a
          sync-only atom, since the forced loop path cannot host one - the
          ``parallel_async_no_sync_only_child`` law.

    Yields:
        VOID, inherited from ``Parallel``.
    """

    _FORCE_MODE = "async"
    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "ParallelAsync requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk


class Gather(Parallel):
    """Alias of ``Parallel``, named for reading naturally at a yield site.

    Args:
        *items: children to run concurrently, each either a Nu instance or
            a ``(child, "threaded"|"async")`` pair pinning its placement.

    Notes:
        - Identical to ``Parallel`` in every mechanical respect - same
          placement rules, same laws, same compiled thunks. The separate
          name exists so code that collects results reads ``Gather`` rather
          than ``Parallel``.

    Example:
        >>> nu.run(nu.Gather(nu.SetCmd(nu.AttrRef("a"), 1), nu.SetCmd(nu.AttrRef("b"), 2)))[1].attrs["b"]
        2
    """
