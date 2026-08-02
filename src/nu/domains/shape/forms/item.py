"""Item (leaf) shape-fabric Forms — three tiers.

Three tiers that compose into ItemRef / MutableItemRef / ReactiveItemRef:

    ItemForm          exists(), missing()
    MutableItemForm   + store(), erase()
    ReactiveItemForm  + on_change()

These are pure Form mixins — no Ref or substrate knowledge. Composed into
the shape/refs/* blueprints so the user-facing API comes from these Forms.

No generic peer — the Item trunk is shape-specific (a leaf value in the
document model has no pure-Python collection equivalent).

Notes:
- No generic type params (T, InterfaceT); Refs are unparameterised.
- No value_type / interface_cls properties; substrate concern, not Form.
- ``init()`` is not implemented: no IfDo control flow yet.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form


if TYPE_CHECKING:
    from nu.core.reactive import OnPrimitiveChange
    from nu.domains.shape.interactions import (
        Erase,
        Exists,
        Missing,
        SetCmd,
    )


__all__ = [
    "ItemForm",
    "MutableItemForm",
    "ReactiveItemForm",
]


class ItemForm(Form):
    """Slot-level read surface for a leaf value in the shape fabric.

    Provides:
        exists()  → Exists  — True if the slot is bound.
        missing() → Missing — True if the slot is unbound.
    """

    def exists(self) -> Exists:
        """Return an Exists — True if this slot is bound."""
        from nu.domains.shape.interactions import Exists

        return Exists(self)

    def missing(self) -> Missing:
        """Return a Missing — True if this slot is unbound."""
        from nu.domains.shape.interactions import Missing

        return Missing(self)


class MutableItemForm(ItemForm):
    """Slot-level write surface — read + store + erase.

    Provides (in addition to ItemForm):
        store(value) → SetCmd — write value to this slot.
        erase()      → Erase — remove this slot from the fabric.

    ``init()`` is absent: IfDo control flow is not yet available.
    """

    def set(self, value: object) -> SetCmd:
        """Return a SetCmd — write ``value`` to this slot."""
        from nu.domains.shape.interactions import SetCmd

        return SetCmd(self, value)

    def erase(self) -> Erase:
        """Return an Erase — remove this slot from the fabric."""
        from nu.domains.shape.interactions import Erase

        return Erase(self)


class ReactiveItemForm(MutableItemForm):
    """Slot-level reactive surface — read + write + change observation.

    Provides (in addition to MutableItemForm):
        on_change() → OnPrimitiveChange — subscribe to changes on this slot.
    """

    def on_change(self) -> OnPrimitiveChange:
        """Return an ``OnPrimitiveChange`` -- subscribe to changes on this leaf.

        A leaf yields a scalar, not a view, so the subscription happens on the
        *parent* view's child-change channel keyed by this leaf's address.
        ``OnPrimitiveChange`` carries only the leaf ref (self); at runtime
        it calls ``ref._afetch_parent`` and ``ref._aaddress`` to resolve the
        parent view and address, then returns
        ``parent.on_child_change(address)`` -- one uniform path across
        substrates, no per-substrate override needed.
        """
        from nu.core.reactive import OnPrimitiveChange

        return OnPrimitiveChange(self)
