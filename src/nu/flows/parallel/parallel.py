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
    """Runs its children concurrently, joins on all - the ``|`` composition.

    Smart placement by default: sync path uses the Budget's thread pool;
    async path places each child per ``Attr.ON_LOOP``. Per-child mode can be
    forced by passing ``(child, "threaded")`` or ``(child, "async")``.
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

    Sync path is unchanged (thread pool). Rejects subtrees holding an
    async-only atom via the ``parallel_threaded_no_async_only_child`` law.
    """

    _FORCE_MODE = "threaded"


class ParallelAsync(Parallel):
    """Parallel with every child forced onto the loop.

    Declaring ``requires_async`` makes the whole subtree async-only, so sync
    ``run`` refuses it up front. Rejects subtrees holding a sync-only atom.
    """

    _FORCE_MODE = "async"
    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "ParallelAsync requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk


class Gather(Parallel):
    """Yield-collecting sibling of ``Parallel``; dispatches the same way."""
