"""Shape family: a nested Shape in a shape fabric, navigated by slot name.

A Shape is structurally a mapping of its slot names, so the ref wears the
mapping forms. Descent is by name, not by value: ``ref.field`` and
``ref["field"]`` resolve the slot the Shape declared, and that slot builds its
own ref under this one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import StructuredRef
from .mapping import MappingForm, MutableMappingForm, ReactiveMappingForm


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape, Slot

__all__ = [
    "MutableShapeRef",
    "ReactiveShapeRef",
    "ShapeRef",
]


class ShapeRef(MappingForm, StructuredRef):
    """Structured container Ref; slot navigation via attribute or bracket access.

    API: full MappingForm surface: exists(), missing(), extract(), keys(),
    values(), items(), len(), contains(), [key], .attr from shape MappingForm.
    """

    def __init__(
        self,
        address: object,
        *,
        shape_type: type[Shape],
        parent_ref: StructuredRef | None = None,
        owner_shape: type[Shape] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape, **kwargs)
        self._payload["shape_type"] = shape_type

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """The Shape an annotation like ``ShapeRef[Order]`` navigates."""
        (shape_type,) = args
        return {"shape_type": shape_type}

    def __getitem__(self, key: object) -> StructuredRef:
        """Navigate into shape slots via bracket access; mirror of __getattr__."""
        if isinstance(key, str):
            shape_type = self._payload["shape_type"]
            if hasattr(shape_type, "_slots") and key in shape_type._slots:
                slot: Slot = shape_type._slots[key]
                return slot.create_ref(owner_shape=shape_type, parent_ref=self)  # type: ignore[return-value]
        raise KeyError(
            f"'{type(self).__name__}' has no slot '{key}'"
            f" (shape '{self._payload['shape_type'].__name__}' has no slot '{key}')"
        )

    def __getattr__(self, name: str) -> StructuredRef:
        """Navigate into shape slots; falls through only when MRO lookup fails."""
        if name.startswith("_"):
            raise AttributeError(name)
        shape_type = self._payload["shape_type"]
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
    """
