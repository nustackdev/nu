"""Strategy concretes - Sequential, Parallel, Race, Gather, AnyN.

`Sequential` is the `>>` operator's target; `Parallel` is `|`; `Race`
is `&`. `Gather` runs concurrently and (eventually) collects yields.
`AnyN` runs children concurrently and succeeds if any one succeeds.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar
from typing import Literal as TLiteral

from nu.terms.flow import Strategy
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.terms import Nu


__all__ = [
    "AnyN",
    "Gather",
    "Parallel",
    "Race",
    "Sequential",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})
_ASYNC_ONLY = frozenset({Mode.ASYNC})


def _has_async_only(nu: Any) -> bool:  # noqa: ANN401
    """True if any node in the subtree has `support = {ASYNC}` exclusively.

    Async-only descendants must run on the event loop. Subtrees without
    any async-only node can run on a worker thread.
    """
    support = getattr(type(nu), "support", None)
    if support is not None and support == _ASYNC_ONLY:
        return True
    for child in getattr(nu, "_children", ()):
        if _has_async_only(child):
            return True
    return False


class Sequential(Strategy):
    """`a >> b` - run children in order."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    associative: ClassVar[bool] = True
    commutative: ClassVar[bool | TLiteral["if-independent"]] = "if-independent"

    # Inherits sequential `_run_children` from Strategy.


class Parallel(Strategy):
    """`a | b` - run children concurrently."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    associative: ClassVar[bool] = True
    commutative: ClassVar[bool] = True

    def _run_children(self, ctx: Any) -> None:  # noqa: ANN401
        from concurrent.futures import ThreadPoolExecutor, as_completed

        from nu.terms.dispatch import ExecState, atom_dispatch

        with ThreadPoolExecutor(max_workers=max(1, len(self._children))) as pool:
            futures = [
                pool.submit(atom_dispatch(c, ExecState.NO_LOOP), ctx) for c in self._children
            ]
            for f in as_completed(futures):
                f.result()

    async def _arun_children(self, ctx: Any) -> None:  # noqa: ANN401
        import asyncio

        from nu.terms.dispatch import ExecState, atom_dispatch

        loop = asyncio.get_running_loop()
        awaitables: list[Any] = []
        for c in self._children:
            if _has_async_only(c):
                awaitables.append(atom_dispatch(c, ExecState.LOOP)(ctx))
            else:
                sync_method = atom_dispatch(c, ExecState.NO_LOOP)
                awaitables.append(loop.run_in_executor(None, sync_method, ctx))
        await asyncio.gather(*awaitables)


class Race(Strategy):
    """`a & b` - run children concurrently; first to complete wins."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    associative: ClassVar[bool] = True
    commutative: ClassVar[bool] = True

    def _run_children(self, ctx: Any) -> None:  # noqa: ANN401
        from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

        from nu.terms.dispatch import ExecState, atom_dispatch

        with ThreadPoolExecutor(max_workers=max(1, len(self._children))) as pool:
            futures = [
                pool.submit(atom_dispatch(c, ExecState.NO_LOOP), ctx) for c in self._children
            ]
            done, _pending = wait(futures, return_when=FIRST_COMPLETED)
            for f in done:
                f.result()
                break

    async def _arun_children(self, ctx: Any) -> None:  # noqa: ANN401
        import asyncio

        from nu.terms.dispatch import ExecState, atom_dispatch

        loop = asyncio.get_running_loop()
        tasks: list[asyncio.Future] = []
        for c in self._children:
            if _has_async_only(c):
                tasks.append(asyncio.ensure_future(atom_dispatch(c, ExecState.LOOP)(ctx)))
            else:
                sync_method = atom_dispatch(c, ExecState.NO_LOOP)
                tasks.append(loop.run_in_executor(None, sync_method, ctx))
        try:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for t in pending:
                t.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            for t in done:
                await t
                break
        except BaseException:
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise


class Gather(Strategy):
    """Run children concurrently and collect their yields.

    For Command children, `run/arun` returns None; this kind is most
    interesting once stream collection is wired. For now it behaves
    like Parallel.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH
    associative: ClassVar[bool] = True
    commutative: ClassVar[bool] = True

    _run_children = Parallel._run_children
    _arun_children = Parallel._arun_children


class AnyN(Strategy):
    """Run children concurrently; succeed if any one succeeds.

    Children: ``[*children]`` -- all body slots (Strategy semantics).
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(self, *children: Nu) -> None:
        super().__init__(*children)

    async def _arun_children(self, ctx: Any) -> None:  # noqa: ANN401
        import asyncio

        from nu import runtime

        if not self._children:
            return
        tasks = {asyncio.create_task(runtime.aexecute(child, ctx)) for child in self._children}
        last_error: BaseException | None = None
        try:
            while tasks:
                done, tasks = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in done:
                    exc = task.exception()
                    if exc is None:
                        for t in tasks:
                            t.cancel()
                        if tasks:
                            await asyncio.gather(*tasks, return_exceptions=True)
                        return
                    last_error = exc
            if last_error is not None:
                raise last_error
        except BaseException:
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            raise
