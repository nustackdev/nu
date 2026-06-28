"""Item (leaf) shape-fabric Forms — three tiers.

Three tiers that compose into ItemRef / MutableItemRef / ReactiveItemRef:

    ItemForm          exists(), missing()
    MutableItemForm   + store(), erase()
    ReactiveItemForm  + on_change()

These are pure Form mixins — no Ref or substrate knowledge. Composed into
the shape/refs/* blueprints so the user-facing API comes from these Forms.

No generic peer — the Item trunk is shape-specific (a leaf value in the
document model has no pure-Python collection equivalent).

v1 reference: ``src/nu/shapes/forms/abc/item.py``.

Deviations from v1:
- No generic type params (T, InterfaceT) — v2 Refs are unparameterised.
- No value_type / interface_cls properties — substrate concern, not Form.
- ``init()`` is not implemented — v2 has no IfDo control flow yet.
"""

from __future__ import annotations

from nu2.lang import Form


__all__ = [
    "ItemForm",
    "MutableItemForm",
    "ReactiveItemForm",
]


class ItemForm(Form):
    """Slot-level read surface for a leaf value in the shape fabric.

    Provides:
        exists()  → ExistsQuery  — True if the slot is bound.
        missing() → MissingQuery — True if the slot is unbound.
    """

    def exists(self) -> object:
        """Return an ExistsQuery — True if this slot is bound."""
        from nu2.domains.shape.interactions import ExistsQuery

        return ExistsQuery(self)

    def missing(self) -> object:
        """Return a MissingQuery — True if this slot is unbound."""
        from nu2.domains.shape.interactions import MissingQuery

        return MissingQuery(self)


class MutableItemForm(ItemForm):
    """Slot-level write surface — read + store + erase.

    Provides (in addition to ItemForm):
        store(value) → StoreCommand — write value to this slot.
        erase()      → EraseCommand — remove this slot from the fabric.

    ``init()`` is absent in v2: IfDo control flow is not yet available.
    """

    def store(self, value: object) -> object:
        """Return a StoreCommand — write ``value`` to this slot."""
        from nu2.domains.shape.interactions import StoreCommand

        return StoreCommand(self, value)

    def erase(self) -> object:
        """Return an EraseCommand — remove this slot from the fabric."""
        from nu2.domains.shape.interactions import EraseCommand

        return EraseCommand(self)


class ReactiveItemForm(MutableItemForm):
    """Slot-level reactive surface — read + write + change observation.

    Provides (in addition to MutableItemForm):
        on_change() → OnChangeQuery — subscribe to changes on this slot.
    """

    def on_change(self) -> object:
        """Return an OnChildChangeQuery — subscribe to changes at this slot's address within the parent.

        v1 mechanic: ``OnChildChange(self.parent, self._raw_address)`` — subscribes
        on the PARENT's child-change channel for this item's address, not on self.
        v2: ``OnChildChangeQuery(self.parent_ref, self.children[0])`` — same logic,
        v2 Ref contract (``parent_ref`` + ``children[0]`` as the address Nu node).
        ``parent_ref`` and ``children[0]`` resolve via ``_StructuredRef`` in the
        composition chain.

        Note: OnChildChangeQuery is shape-domain (lives in
        ``nu2.domains.shape.interactions``, not ``nu2.forms.reactive``).
        """
        from nu2.domains.shape.interactions import OnChildChangeQuery

        return OnChildChangeQuery(self.parent_ref, self.children[0])  # type: ignore[attr-defined]
