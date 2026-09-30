"""Attrs interactions: ``Exists``.

The read itself is the ``Attr`` Ref's dual role. ``Exists`` complements it: an
unbound read yields EMPTY, which a name bound to EMPTY would alias, so
existence needs an explicit query. It holds its Ref in a read slot; effect
synthesis binds it to a read on the attrs fabric.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["Exists"]


class Exists(ScalarQuery):
    """Whether the name its attrs ref names is bound in ``ctx.attrs``.

    Args:
        ref: the attrs ref whose address is resolved and looked up.

    Notes:
        - Normally written as ``ref.exists()`` rather than built by hand.
        - Exists because the dual-role read cannot answer the question: an
          unbound name yields EMPTY, and so does a name bound to EMPTY.
        - Only the address is resolved; the value is never read.

    Yields:
        True or False, never a sentinel. An address that resolves to EMPTY or
        INVALID is looked up as a key like any other, and is simply absent.

    Example:
        >>> nu.run(nu.Attr("x").exists())[0]
        False

        >>> nu.run(nu.Collect(nu.Map(nu.Iter([1]), nu.Attr("item").exists())))[0]
        [True]
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        def thunk(rt: Runtime) -> object:
            return rt.ctx.attrs.exists(ref._address(rt, rt.program.children[nid][0]))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        ref = self._children[0]

        async def athunk(rt: Runtime) -> object:
            return rt.ctx.attrs.exists(await ref._aaddress(rt, rt.program.children[nid][0]))

        return athunk
