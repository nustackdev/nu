"""ShapeRef hierarchy — structured container Ref with named-slot navigation.

    ShapeRef         = shape.MappingForm + _StructuredRef
    MutableShapeRef  = shape.MutableMappingForm + ShapeRef
    ReactiveShapeRef = shape.ReactiveMappingForm + MutableShapeRef

A Shape is structurally a mapping (dict[str, object]).  Using the shape-domain
``MappingForm`` (which already weaves generic MappingForm + shape CollectionForm)
gives all 3 tiers the full mapping surface (keys/values/items/extract/__getitem__,
len, contains) PLUS shape ops (exists/missing/store/erase), without a separate
ItemForm in the MRO.

Slot navigation is available two ways:
  - Attribute:  ``ref.field``   — via ``__getattr__`` (MRO fallback)
  - Bracket:    ``ref["field"]`` — via ``__getitem__`` override

Both produce a correctly-typed child Ref from the slot definition.

Form composition provides:
    base:     exists(), missing(), extract(), keys(), values(), items(),
              len(), contains(), [key], .attr
    mutable:  + store(v), erase(), set(k,v), delete(k), update(), ...
    reactive: + on_change() (generic), on_child_change(), on_children_change(),
                on_descendants_change() (shape-domain)

Notes:
- MutableShapeRef / ReactiveShapeRef are included.
- ReactiveShapeRef composes with shape.ReactiveMappingForm (shape IS a mapping).
- _wrap_* abstract methods from MappingForm raise NotImplementedError on the
  blueprint — substrate subclasses fill them in (consistent with MappingRef etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.domains.shape.forms.mapping import MappingForm, MutableMappingForm, ReactiveMappingForm

from .base import _StructuredRef


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape, Slot

__all__ = [
    "MutableShapeRef",
    "ReactiveShapeRef",
    "ShapeRef",
]


class ShapeRef(MappingForm, _StructuredRef):
    """Structured container Ref; slot navigation via attribute or bracket access.

    API: full MappingForm surface — exists(), missing(), extract(), keys(),
    values(), items(), len(), contains(), [key], .attr — from shape MappingForm.
    ``_wrap_*`` methods raise NotImplementedError on the blueprint; substrate
    subclasses override them.
    """

    def __init__(
        self,
        address: object,
        *,
        shape_type: type[Shape],
        parent_ref: _StructuredRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self._shape_type = shape_type

    @property
    def shape_type(self) -> type[Shape]:
        """The Shape class at this Ref's location."""
        return self._shape_type

    def __getstate__(self) -> dict:
        """Pickle support — return instance state."""
        return self.__dict__.copy()

    def __setstate__(self, state: dict) -> None:
        """Pickle support — restore instance state without triggering __getattr__."""
        self.__dict__.update(state)

    def __getitem__(self, key: object) -> _StructuredRef:
        """Navigate into shape slots via bracket access — mirror of __getattr__."""
        if isinstance(key, str):
            shape_type = self._shape_type
            if hasattr(shape_type, "_slots") and key in shape_type._slots:
                slot: Slot = shape_type._slots[key]
                return slot.create_ref(owner_shape=shape_type, parent_ref=self)  # type: ignore[return-value]
        raise KeyError(
            f"'{type(self).__name__}' has no slot '{key}'"
            f" (shape '{self._shape_type.__name__}' has no slot '{key}')"
        )

    def __getattr__(self, name: str) -> _StructuredRef:
        """Navigate into shape slots; falls through only when MRO lookup fails."""
        if name.startswith("_"):
            raise AttributeError(name)
        shape_type = self._shape_type
        if hasattr(shape_type, "_slots") and name in shape_type._slots:
            slot: Slot = shape_type._slots[name]
            return slot.create_ref(owner_shape=shape_type, parent_ref=self)  # type: ignore[return-value]
        raise AttributeError(
            f"'{type(self).__name__}' has no attribute '{name}'"
            f" (shape '{shape_type.__name__}' has no slot '{name}')"
        )


class MutableShapeRef(MutableMappingForm, ShapeRef):
    """Mutable structured container Ref.

    Adds: store(v), erase(), set(k,v), delete(k), update(), ... (from
    shape MutableMappingForm) on top of ShapeRef.
    """


class ReactiveShapeRef(ReactiveMappingForm, MutableShapeRef):
    """Reactive structured container Ref.

    Adds: on_change() (generic), on_child_change(), on_children_change(),
    on_descendants_change() (shape-domain, from shape.ReactiveMappingForm)
    on top of MutableShapeRef.

    shape.ReactiveMappingForm is used because a Shape IS a mapping; this provides
    the full reactive surface (generic on_change + shape tree-aware).
    """
