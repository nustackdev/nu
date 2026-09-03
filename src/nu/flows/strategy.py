"""Strategy flows: Command-composing atoms that dispatch their children.

This module owns the sequential Strategy. The parallel-family Strategies
(``Parallel``, ``Race``, ``AnyN``, ``Gather``, and their forced-mode
variants) live under ``nu.flows.parallel`` and are re-exported by
``nu.flows``.

A Strategy owns no effects itself; the children carry the writes, and the
``flow_body_is_mutator`` law holds every slot to a mutating child.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Strategy


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["Sequential"]


class Sequential(Strategy):
    """Runs its children in order - the ``>>`` composition.

    Args:
        *children: the mutating children to run in order.

    Notes:
        - Calls the child thunks directly rather than going through
          ``Runtime.eval`` / ``Runtime.aeval``, so the sequential hot path
          needs no Budget and skips the dispatch hop per child.

    Yields:
        Nothing (VOID). The writes are the children's.

    Example:
        >>> nu.run(nu.Sequential(nu.SetCmd(nu.AttrRef("a"), 1), nu.SetCmd(nu.AttrRef("b"), 2)))[1].attrs
        Attributes(a=1, b=2)
    """

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
