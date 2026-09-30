"""``Attr``: the tree's one read of ``ctx.attrs``.

An ``Attr`` names a key in ``ctx.attrs`` by its resolved address (any child
that yields a value) and self-yields what an interaction bound there. It only
reads: interactions write attrs in their own compile, and the tree never does.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms.primitives import Object
from nu.lang.sentinels import EMPTY

from .._refs import _ContextRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

    from .interactions import AttrExists


__all__ = ["Attr"]


class Attr(_ContextRef, Object):
    """Reads the value an interaction handed its body under a name.

    A loop binds its item, a fold its accumulator, a catch the error, a retry
    the attempt, a reaction the key that changed. ``Attr(name)`` is how the
    body reads it. The sole child is the address, evaluated through the
    runtime like any other child, so a name can be fixed at write time or
    computed at run time.

    Args:
        address: evaluated to the key this Ref names. ``Attr("item")``
            wraps a literal key; ``Attr(Attr("k"))`` takes the key out of
            another binding.

    Notes:
        - Read-only. Nothing in the tree binds or reassigns a name; state
          goes through a fabric (``nu.mem`` for local state).
        - It carries the Object form, the surface every term has. Wrap the
          read in the form it needs: ``nu.Str(nu.Attr("item")).upper()``.
        - A name nothing bound and a name bound to EMPTY read the same, so
          reach for ``.exists()`` when the difference matters.

    Yields:
        The value at the resolved key. EMPTY when the key is unbound.

    Example:
        >>> nu.run(nu.Attr("missing"))[0]
        <EMPTY>

        >>> nu.run(nu.Collect(nu.Map(nu.Iter([1, 2]), nu.Int(nu.Attr("item")) + 1)))[0]
        [2, 3]
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        address = children[0]

        def thunk(rt: Runtime) -> object:
            return rt.ctx.attrs.get(address(rt), EMPTY)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        address = children[0]

        async def athunk(rt: Runtime) -> object:
            return rt.ctx.attrs.get(await address(rt), EMPTY)

        return athunk

    def exists(self) -> AttrExists:
        """A Query yielding whether this Ref's name is bound in ``ctx.attrs``.

        Notes:
            - The plain read cannot answer this: an unbound name yields EMPTY
              and so does a name bound to EMPTY.
            - Only the address is resolved; the value is never read.
        """
        from .interactions import AttrExists

        return AttrExists(self)
