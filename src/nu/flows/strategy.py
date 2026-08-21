"""Strategy flows: Command-composing atoms that dispatch their children.

This module owns the sequential Strategy. The parallel-family Strategies
(``Parallel``, ``Race``, ``AnyN``, ``Gather``, and their forced-mode
variants) live under ``nu.flows.parallel`` and are re-exported by
``nu.flows``.

A Strategy owns no effects and yields nothing (VOID): the children carry
the writes, and the ``flow_body_is_mutator`` law holds every slot to a
mutating child (the matrix STRATEGY row admits only work sorts).
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

    Calls the child thunks directly: the sequential hot path needs no Budget,
    so it skips the Runtime dispatch hop.
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
