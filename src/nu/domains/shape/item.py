"""Leaf family: a single value in a shape fabric, with no descent below it.

Forms give the slot-level surface (read, write, observe the one value); refs
bind that surface to an address. A fabric's leaves mix a value form in beside
these, so the ref itself is an operand of the value it names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form

from .base import StructuredRef


if TYPE_CHECKING:
    from nu.core.flows.control import IfDo
    from nu.core.reactive import OnPrimitiveChange
    from nu.domains.shape.interactions import (
        Erase,
        Exists,
        Missing,
        SetCmd,
    )


__all__ = [
    "ItemForm",
    "ItemRef",
    "MutableItemForm",
    "MutableItemRef",
    "ReactiveItemForm",
    "ReactiveItemRef",
]


class ItemForm(Form):
    """Slot-level read surface for a leaf value. Ops: ``exists()``, ``missing()``."""

    def exists(self) -> Exists:
        """Build an ``Exists`` query."""
        from nu.domains.shape.interactions import Exists

        return Exists(self)

    def missing(self) -> Missing:
        """Build a ``Missing`` query."""
        from nu.domains.shape.interactions import Missing

        return Missing(self)


class MutableItemForm(ItemForm):
    """Slot-level write surface. Adds ``set(value)`` and ``erase()``."""

    def set(self, value: object) -> SetCmd:
        """Build a ``SetCmd``."""
        from nu.domains.shape.interactions import SetCmd

        return SetCmd(self, value)

    def erase(self) -> Erase:
        """Build an ``Erase``."""
        from nu.domains.shape.interactions import Erase

        return Erase(self)

    def init(self, value: object) -> IfDo:
        """Set ``value`` iff the leaf is currently missing."""
        from nu.core.flows.control import IfDo

        return IfDo(self.missing(), self.set(value))


class ReactiveItemForm(MutableItemForm):
    """Slot-level reactive surface. Adds ``on_change()``."""

    def on_change(self) -> OnPrimitiveChange:
        """Subscribe to changes on this leaf.

        A leaf yields a scalar, not a view, so the subscription happens on the
        *parent* view's child-change channel keyed by this leaf's address.
        ``OnPrimitiveChange`` carries only the leaf ref (self); at runtime
        it calls ``ref._afetch_parent`` and ``ref._aaddress`` to resolve the
        parent view and address, then returns
        ``parent.on_child_change(address)``: one uniform path across
        substrates, no per-substrate override needed.
        """
        from nu.core.reactive import OnPrimitiveChange

        return OnPrimitiveChange(self)


class ItemRef(ItemForm, StructuredRef):
    """Leaf Ref: single typed value, no child descent.

    API: exists(), missing() (from ItemForm).
    """


class MutableItemRef(MutableItemForm, ItemRef):
    """Mutable leaf Ref: single typed value with write/erase.

    API: exists(), missing(), set(v), erase() (from MutableItemForm).
    """


class ReactiveItemRef(ReactiveItemForm, MutableItemRef):
    """Reactive leaf Ref: single typed value with observation.

    API: exists(), missing(), set(v), erase(), on_change() (from ReactiveItemForm).
    """
