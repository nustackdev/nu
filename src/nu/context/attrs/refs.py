"""``AttrRef`` and its typed variants.

An ``AttrRef`` names a slot in ``ctx.attrs`` by its resolved address (any child
that yields a value). Reads self-yield the value at that key (EMPTY when
unbound); writes and erases go through the Ref so a Command never touches
``ctx.attrs`` directly - the write mechanism lives with the fabric.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms.collections import Dict, FrozenSet, List, Set, Tuple
from nu.forms.primitives import Any, Bool, Bytes, Float, Int, None_, Str
from nu.lang.sentinels import EMPTY

from .._refs import _ContextRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

    from .interactions import AttrExists


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

    def exists(self) -> AttrExists:
        """A Query yielding whether this Ref's address is bound in ``ctx.attrs``."""
        from .interactions import AttrExists

        return AttrExists(self)


# =========================================================================
# TYPED ATTR REFS - PRIMITIVES
# =========================================================================


class IntAttrRef(AttrRef, Int):
    """An AttrRef with the full integer interface."""


class FloatAttrRef(AttrRef, Float):
    """An AttrRef with the full float interface."""


class StrAttrRef(AttrRef, Str):
    """An AttrRef with the full string interface."""


class BoolAttrRef(AttrRef, Bool):
    """An AttrRef with the full boolean interface."""


class BytesAttrRef(AttrRef, Bytes):
    """An AttrRef with the full bytes interface."""


class AnyAttrRef(AttrRef, Any):
    """An AttrRef with the dynamic any interface."""


class NoneAttrRef(AttrRef, None_):
    """An AttrRef with the none interface."""


# =========================================================================
# TYPED ATTR REFS - COLLECTIONS
# =========================================================================


class ListAttrRef(AttrRef, List):
    """An AttrRef with the full list interface."""


class DictAttrRef(AttrRef, Dict):
    """An AttrRef with the full dict interface."""


class SetAttrRef(AttrRef, Set):
    """An AttrRef with the full set interface."""


class FrozenSetAttrRef(AttrRef, FrozenSet):
    """An AttrRef with the full frozenset interface."""


class TupleAttrRef(AttrRef, Tuple):
    """An AttrRef with the full tuple interface."""
