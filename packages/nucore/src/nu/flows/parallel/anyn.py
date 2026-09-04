"""AnyN: first-to-succeed fan-in over the async loop.

A child that raises is set aside; the wait continues. If every child fails,
the last error is re-raised. Async-only, like ``Race``.
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

__all__ = ["AnyN"]


class AnyN(Strategy):
    """Runs its children concurrently; succeeds as soon as any one does.

    Args:
        *children: the mutating children to run.

    Notes:
        - A child that raises is set aside rather than failing the whole
          node; the wait continues for the rest. If every child fails, the
          last error is re-raised.
        - Async-only: ``_compile`` raises ``RuntimeError``, and sync ``run``
          refuses the subtree up front via ``requires_async``.

    Yields:
        Nothing (VOID). The writes are the first child to succeed.

    Example:
        >>> import asyncio
        >>> fail = nu.raise_(ValueError, "nope")
        >>> ok = nu.DelayedDo(0.05, nu.SetCmd(nu.AttrRef("winner"), "ok"))
        >>> asyncio.run(nu.arun(nu.AnyN(fail, ok)))[1].attrs
        Attributes(winner='ok')
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
            await _scheduling.aeval_any(rt, rt.program.children[nid])

        return athunk
