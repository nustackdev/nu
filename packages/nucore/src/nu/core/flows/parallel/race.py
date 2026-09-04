"""Race: first-to-complete fan-in over the async loop.

Async-only: real cancellation of the losers needs a loop. The sync thunk
raises as a backstop, but sync ``run`` refuses the async-only subtree first.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang.attributes.execution import ExecOrder
from nu.lang.kinds import Strategy

from . import _scheduling


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["Race"]


class Race(Strategy):
    """Runs its children concurrently; first to finish wins - the ``&`` composition.

    Args:
        *children: the mutating children to race.

    Notes:
        - The losers are cancelled once the first child completes.
        - Async-only: ``_compile`` raises ``RuntimeError``, and sync ``run``
          refuses the subtree up front via ``requires_async``.

    Yields:
        Nothing (VOID). The writes are whichever child wins.

    Example:
        >>> import asyncio
        >>> fast = nu.SetCmd(nu.AttrRef("winner"), "fast")
        >>> slow = nu.DelayedDo(1, nu.SetCmd(nu.AttrRef("winner"), "slow"))
        >>> asyncio.run(nu.arun(nu.Race(fast, slow)))[1].attrs
        Attributes(winner='fast')
    """

    _requires_async = Declared(value=True, name="requires_async")
    _exec_order = Declared(value=ExecOrder.PARALLEL, name="exec_order")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "Race requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> None:
            await _scheduling.aeval_race(rt, rt.program.children[nid])

        return athunk
