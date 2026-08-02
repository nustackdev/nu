"""Strategy flows: Command-composing atoms that dispatch their children.

Nu's Strategy sub-shape - the Flows that compose mutating atoms directly, with
no Query parameters. ``Sequential`` runs its children in order (the ``>>``
composition); ``Parallel`` (``|``), ``Race`` (``&``), ``Gather`` and ``AnyN``
run them concurrently. A Strategy owns no effects and yields nothing (VOID):
the children carry the writes, and the ``flow_body_is_mutator`` law holds every
slot to a mutating child (the matrix STRATEGY row admits only work sorts).

Concurrency is the Runtime's job, not ours. The Runtime owns the Budget (its
thread pool, async semaphore, and the ``max_parallel`` gate) and exposes the
fan-in primitives keyed on child node ids: ``eval_parallel`` / ``aeval_parallel``
(join on all) and ``aeval_race`` (first to complete wins). Each falls through to
sequential when ``max_parallel == 1``, and the async variants are semaphore-
gated; per-child sync/async placement is resolved off ``Attr.ON_LOOP`` inside
the Runtime. So a Strategy thunk just hands the child nids
(``rt.program.children[nid]``) to the matching primitive - no thread pools or
``gather`` here. The Term stays immutable; all behaviour lives in the thunk.

``Parallel`` / ``Race`` / ``Gather`` / ``AnyN`` declare ``exec_order = PARALLEL``.
``Race`` and ``AnyN`` are async-only (``requires_async``): cancelling the losing
branches only works on a loop, and the Runtime provides a race primitive only
on the async path. Their sync thunks raise, but sync ``run`` refuses the
async-only subtree first (``refuse_async_only``), so the raise is a backstop.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Strategy
from nu.lang.attributes.execution import ExecOrder


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["AnyN", "Gather", "Parallel", "Race", "Sequential"]


class Sequential(Strategy):
    """Runs its children in order - the ``>>`` composition.

    Associative (``a >> (b >> c)`` regroups freely); not commutative in
    general - order is the whole point. Calls the child thunks directly: the
    sequential hot path needs no Budget, so it skips the Runtime dispatch hop.
    """

    _associative = Declared(value=True, name="associative")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            for child in children:
                child(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> None:
            for child in children:
                await child(rt)

        return athunk


class Parallel(Strategy):
    """Runs its children concurrently, joins on all - the ``|`` composition.

    Hands the child nids to the Runtime's parallel fan-in: ``eval_parallel``
    (Budget thread pool) on the sync path, ``aeval_parallel`` (semaphore-gated
    ``gather``) on the async path. Both join on every child and fall through to
    sequential under ``max_parallel == 1``. Commutative and associative.
    """

    _associative = Declared(value=True, name="associative")
    _commutative = Declared(value=True, name="commutative")
    _exec_order = Declared(value=ExecOrder.PARALLEL, name="exec_order")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            rt.eval_parallel(rt.program.children[nid])

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> None:
            await rt.aeval_parallel(rt.program.children[nid])

        return athunk


class Race(Strategy):
    """Runs its children concurrently; the first to finish wins - the ``&`` composition.

    Delegates to the Runtime's ``aeval_race``, which cancels the losing branches
    once one completes. Async-only: real cancellation needs a loop, and the
    Runtime provides a race primitive only on the async path. The sync thunk
    raises, but sync ``run`` refuses the async-only subtree first.
    """

    _associative = Declared(value=True, name="associative")
    _commutative = Declared(value=True, name="commutative")
    _requires_async = Declared(value=True, name="requires_async")
    _exec_order = Declared(value=ExecOrder.PARALLEL, name="exec_order")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "Race requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> None:
            await rt.aeval_race(rt.program.children[nid])

        return athunk


class Gather(Strategy):
    """Runs its children concurrently and joins on all.

    The yield-collecting twin of ``Parallel``: it will hand back the children's
    yields once Flow-level yield collection is wired. A Flow yields nothing
    today, so for now it dispatches exactly like ``Parallel`` - through the same
    Runtime fan-in primitives.
    """

    _associative = Declared(value=True, name="associative")
    _commutative = Declared(value=True, name="commutative")
    _exec_order = Declared(value=ExecOrder.PARALLEL, name="exec_order")

    _compile = Parallel._compile
    _acompile = Parallel._acompile


class AnyN(Strategy):
    """Runs its children concurrently; succeeds as soon as any one succeeds.

    Delegates to the Runtime's ``aeval_any``, which sets a failing branch aside
    and keeps waiting, cancels the rest on the first success, and re-raises the
    last error only if all fail. Async-only, like ``Race``.
    """

    _requires_async = Declared(value=True, name="requires_async")
    _exec_order = Declared(value=ExecOrder.PARALLEL, name="exec_order")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "AnyN requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> None:
            await rt.aeval_any(rt.program.children[nid])

        return athunk
