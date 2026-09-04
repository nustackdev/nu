"""Fabric existence query.

The dual-role read of a ``FabricRef`` yields the bound fabric or ``EMPTY``.
That aliases a bound ``EMPTY``, so existence needs an explicit query.
``FabricExists`` holds a ``FabricRef`` in a read slot and answers
whether its fabric type is bound on the Context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["FabricExists"]


class FabricExists(ScalarQuery):
    """Whether the fabric type of its ``FabricRef`` is bound on the Context.

    Args:
        ref: the ``FabricRef`` whose address is resolved and looked up.

    Notes:
        - Normally written as ``FabricRef(...).exists()`` rather than built by
          hand.
        - Exists because the dual-role read cannot answer the question: an
          unbound type yields EMPTY, and so does a type bound to EMPTY.
        - Answering goes through Context resolution, so a lazily bound
          factory is materialized by the check itself.

    Yields:
        True or False, never a sentinel.

    Example:
        >>> class Counter:
        ...     pass
        >>> nu.run(nu.FabricRef(Counter).exists())[0]
        False
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        def thunk(rt: Runtime) -> object:
            return rt.ctx.has(ref._address(rt, rt.program.children[nid][0]))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        async def athunk(rt: Runtime) -> object:
            return rt.ctx.has(await ref._aaddress(rt, rt.program.children[nid][0]))

        return athunk
