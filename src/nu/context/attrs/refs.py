"""``AttrRef`` and its typed variants.

An ``AttrRef`` names a slot in ``ctx.attrs`` by its resolved address (any child
that yields a value). Reads self-yield the value at that key (EMPTY when
unbound); writes and erases go through the Ref so a Command never touches
``ctx.attrs`` directly - the write mechanism lives with the fabric.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms.collections import DictForm, FrozenSetForm, ListForm, SetForm, TupleForm
from nu.forms.primitives import AnyForm, BoolForm, BytesForm, FloatForm, IntForm, NoneForm, StrForm
from nu.lang.sentinels import EMPTY

from .._refs import _ContextRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

    from .interactions import AttrExistsQuery


__all__ = [
    "AnyAttrRef",
    "AttrRef",
    "BoolAttrRef",
    "BytesAttrRef",
    "DictAttrRef",
    "FloatAttrRef",
    "FrozenSetAttrRef",
    "IntAttrRef",
    "ListAttrRef",
    "NoneAttrRef",
    "SetAttrRef",
    "StrAttrRef",
    "TupleAttrRef",
]


class AttrRef(_ContextRef):
    """A Ref into the ``ctx.attrs`` store, keyed by its resolved address.

    The address child resolves to a key. Reads yield the value at that key
    (EMPTY when unbound) through the dual role; writes and erases resolve the
    address and go through the Ref. The address can be anything that yields a
    value - ``AttrRef("total")`` (a literal key) or ``AttrRef(AttrRef("k"))``
    (a key read from another slot).
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        address = children[0]

        def thunk(rt: Runtime) -> object:
            return rt.ctx.attrs.get(address(rt), EMPTY)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        address = children[0]

        async def athunk(rt: Runtime) -> object:
            return rt.ctx.attrs.get(await address(rt), EMPTY)

        return athunk

    def _write(self, rt: Runtime, value: object, nid: int) -> None:
        """Write ``value`` to this Ref's slot in the attrs fabric."""
        rt.ctx.attrs[self._address(rt, nid)] = value

    async def _awrite(self, rt: Runtime, value: object, nid: int) -> None:
        """Async sibling of :meth:`_write`."""
        rt.ctx.attrs[await self._aaddress(rt, nid)] = value

    def _erase(self, rt: Runtime, nid: int) -> None:
        """Remove this Ref's slot from the attrs fabric, if present."""
        address = self._address(rt, nid)
        if address in rt.ctx.attrs:
            del rt.ctx.attrs[address]

    async def _aerase(self, rt: Runtime, nid: int) -> None:
        """Async sibling of :meth:`_erase`."""
        address = await self._aaddress(rt, nid)
        if address in rt.ctx.attrs:
            del rt.ctx.attrs[address]

    def exists(self) -> AttrExistsQuery:
        """A Query yielding whether this Ref's address is bound in ``ctx.attrs``."""
        from .interactions import AttrExistsQuery

        return AttrExistsQuery(self)


# =========================================================================
# TYPED ATTR REFS - PRIMITIVES
# =========================================================================


class IntAttrRef(AttrRef, IntForm):
    """An AttrRef with the full integer interface."""


class FloatAttrRef(AttrRef, FloatForm):
    """An AttrRef with the full float interface."""


class StrAttrRef(AttrRef, StrForm):
    """An AttrRef with the full string interface."""


class BoolAttrRef(AttrRef, BoolForm):
    """An AttrRef with the full boolean interface."""


class BytesAttrRef(AttrRef, BytesForm):
    """An AttrRef with the full bytes interface."""


class AnyAttrRef(AttrRef, AnyForm):
    """An AttrRef with the dynamic any interface."""


class NoneAttrRef(AttrRef, NoneForm):
    """An AttrRef with the none interface."""


# =========================================================================
# TYPED ATTR REFS - COLLECTIONS
# =========================================================================


class ListAttrRef(AttrRef, ListForm):
    """An AttrRef with the full list interface."""


class DictAttrRef(AttrRef, DictForm):
    """An AttrRef with the full dict interface."""


class SetAttrRef(AttrRef, SetForm):
    """An AttrRef with the full set interface."""


class FrozenSetAttrRef(AttrRef, FrozenSetForm):
    """An AttrRef with the full frozenset interface."""


class TupleAttrRef(AttrRef, TupleForm):
    """An AttrRef with the full tuple interface."""
