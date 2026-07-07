"""Service existence query.

The dual-role read yields the bound service or EMPTY. That aliases a bound
EMPTY, so existence needs an explicit query. ``ServiceExistsQuery`` holds a
``ServiceRef`` in a read slot and answers whether its service type is bound
on the Context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["ServiceExistsQuery"]


class ServiceExistsQuery(ScalarQuery):
    """Yields whether the slot-0 ``ServiceRef``'s service type is bound."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        def thunk(rt: Runtime) -> object:
            return rt.ctx.has(ref._address(rt, rt.program.children[nid][0]))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        ref = self._children[0]

        async def athunk(rt: Runtime) -> object:
            return rt.ctx.has(await ref._aaddress(rt, rt.program.children[nid][0]))

        return athunk
