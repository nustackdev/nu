"""``AttrRef`` and the typed attrs refs.

An ``AttrRef`` names a slot in ``ctx.attrs`` by its resolved address (any child
that yields a value). Reads self-yield the value at that key (EMPTY when
unbound); a reassignment goes through the Ref so a Command never touches
``ctx.attrs`` directly - the write mechanism lives with the fabric.

Attrs hold values that never change in place. A name is declared with ``Let``
and rebound with ``.set()``, so a typed ref exists only for a Python-immutable
value, and its form contributes read-only operators. Anything else is read
through ``ObjectRef``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import Self

from nu.domains.shape.dsl import Slot
from nu.forms.collections import FrozenSet, Tuple
from nu.forms.primitives import Bool, Bytes, Float, Int, Object, Str
from nu.lang.sentinels import EMPTY

from .._refs import _ContextRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

    from .interactions import Exists, Set


__all__ = [
    "AttrRef",
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "FrozenSetRef",
    "IntRef",
    "ObjectRef",
    "StrRef",
    "TupleRef",
]


class AttrRef(_ContextRef):
    """A Ref into the ``ctx.attrs`` store, keyed by its resolved address.

    The internal base under the typed attrs refs. The sole child is the
    address, evaluated through the runtime like any other child, so a key can
    be fixed at write time or computed at run time. Reading is the dual role:
    the Ref self-yields whatever sits at that key. Reassigning never happens
    at the call site - a Command hands the Ref its own node id, the Ref
    resolves its address and touches the store, so the write mechanism stays
    with the fabric.

    Args:
        address: evaluated to the key this Ref names. ``ObjectRef("total")``
            wraps a literal key; ``ObjectRef(StrRef("k"))`` takes the key out
            of another slot.

    Notes:
        - A name is declared by ``Let`` and only reassigned through
          ``.set()``. Reassigning a name no ``Let`` declared raises, so every
          binding has a scope that ends.
        - An unbound slot and a slot holding EMPTY read the same, so reach
          for ``.exists()`` when the difference matters.
        - ``ctx.attrs`` is the short-lived axis of the Context fabric: loop
          variables, counters, accumulators, markers. Anything longer-lived
          is a typed binding, read through ``FabricRef``.
        - ``Map`` and ``Filter`` bind their per-item loop variable into this
          same store, which is why a body reads the item with an attrs ref.
        - The typed refs mix a Form in for its operator surface only.
          Nothing checks that the value at the key really has that type; an
          ``IntRef`` over an unbound slot yields EMPTY, and arithmetic on it
          collapses to INVALID like any other sentinel operand.

    Yields:
        The value at the resolved key. EMPTY when the key is unbound.

    Example:
        >>> nu.run(nu.ObjectRef("missing"))[0]
        <EMPTY>

        >>> total = nu.IntRef("total")
        >>> nu.run(nu.Let(total, 10, total + 1))[0]
        11

        >>> key = nu.StrRef("k")
        >>> nu.run(nu.Let(key, "total", nu.Let(nu.IntRef(key), 5, nu.IntRef("total"))))[0]
        5
    """

    # A shape slot of an attrs ref names the top-level attr it is called, so
    # ``Attrs.plane`` is ``StrRef("plane")``. See ``nu.domains.shape.dsl``.
    _flat_slot: ClassVar[bool] = True

    @classmethod
    def slot(cls) -> Self:
        """Declare a Shape slot naming the top-level attr of the slot's name.

        A Shape of attrs slots is how a module declares the names it uses:
        ``Attrs.plane`` is exactly ``StrRef("plane")``, so ``Let``, ``.set()``
        and ``.exists()`` take it like any attrs ref. ``plane: nu.StrRef`` as
        an annotation declares the same slot.

        Notes:
            - Attrs are flat. A Shape holding attrs slots holds nothing else,
              and never nests under another Shape.
            - One ``class Attrs(nu.Shape)`` per app is the convention; a
              module may declare its own. A module declares what it uses.

        Example:
            >>> class Attrs(nu.Shape):
            ...     total = nu.IntRef.slot()
            >>> nu.run(nu.Let(Attrs.total, 10, Attrs.total + 1))[0]
            11
        """
        return Slot(cls)  # type: ignore[return-value]

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

    def _write(self, rt: Runtime, value: object, nid: int) -> None:
        """Reassign this Ref's slot in the attrs fabric; it must be declared."""
        rt.ctx.attrs.set(self._address(rt, nid), value)

    async def _awrite(self, rt: Runtime, value: object, nid: int) -> None:
        """Async sibling of :meth:`_write`."""
        rt.ctx.attrs.set(await self._aaddress(rt, nid), value)

    def set(self, value: object) -> Set:
        """A Command reassigning this Ref's name to ``value``.

        Args:
            value: evaluated once, and its result becomes the name's value.

        Notes:
            - The name must already be declared by an enclosing ``Let``;
              reassigning an undeclared name raises at run time.
            - Rebinds the innermost declaration. When that ``Let`` exits the
              outer value comes back, so a reassignment never leaks past the
              scope that declared the name.
            - An EMPTY or INVALID ``value`` writes nothing, so the name
              keeps what it held.

        Yields:
            Nothing (VOID). The reassignment is the point.

        Example:
            >>> n = nu.IntRef("n")
            >>> _ = nu.run(nu.Let(n, 1, n.set(n + 1) >> nu.print(n)))
            2
        """
        from .interactions import Set

        return Set(self, value)

    def exists(self) -> Exists:
        """A Query yielding whether this Ref's name is declared in ``ctx.attrs``.

        Notes:
            - The plain read cannot answer this: an unbound slot yields EMPTY
              and so does a name declared without a value.
            - Only the address is resolved; the slot's value is never read.
        """
        from .interactions import Exists

        return Exists(self)


# =========================================================================
# TYPED ATTRS REFS - PRIMITIVES
# =========================================================================


class IntRef(AttrRef, Int):
    """An attrs ref with the integer interface."""


class FloatRef(AttrRef, Float):
    """An attrs ref with the float interface."""


class StrRef(AttrRef, Str):
    """An attrs ref with the string interface."""


class BoolRef(AttrRef, Bool):
    """An attrs ref with the boolean interface."""


class BytesRef(AttrRef, Bytes):
    """An attrs ref with the bytes interface."""


# =========================================================================
# TYPED ATTRS REFS - IMMUTABLE COLLECTIONS
# =========================================================================


class TupleRef(AttrRef, Tuple):
    """An attrs ref with the tuple interface."""


class FrozenSetRef(AttrRef, FrozenSet):
    """An attrs ref with the frozenset interface."""


# =========================================================================
# OBJECT REF - everything else
# =========================================================================


class ObjectRef(AttrRef, Object):
    """An attrs ref with the Object interface, the one every term has."""
