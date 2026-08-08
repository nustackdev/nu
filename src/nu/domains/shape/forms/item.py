"""Item (leaf) shape-fabric Forms: three tiers.

Three tiers that compose into ItemRef / MutableItemRef / ReactiveItemRef:

    ItemForm          exists(), missing()
    MutableItemForm   + set(), erase()
    ReactiveItemForm  + on_change()

Pure Form mixins, no Ref or substrate knowledge. Composed into
the shape/refs/* blueprints so the user-facing API comes from these Forms.

No generic peer: the Item trunk is shape-specific (a leaf value in the
document model has no pure-Python collection equivalent).

Notes:
- No generic type params (T, InterfaceT); Refs are unparameterised.
- No value_type / interface_cls properties; substrate concern, not Form.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form


if TYPE_CHECKING:
    from nu.domains.shape.interactions import (
        Erase,
        Exists,
        Missing,
        SetCmd,
    )
    from nu.flows.control import IfDo
    from nu.reactive import OnPrimitiveChange


__all__ = [
    "ItemForm",
    "MutableItemForm",
    "ReactiveItemForm",
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
        from nu.flows.control import IfDo

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
        from nu.reactive import OnPrimitiveChange

        return OnPrimitiveChange(self)
