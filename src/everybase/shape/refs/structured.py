"""Shape ref hierarchy — structured containers with named slots.

ShapeRef         = MappingBase[str, object, ...] + Ref
MutableShapeRef  = MutableMappingBase[str, object, ...] + ShapeRef
ReactiveShapeRef = ReactiveMappingBase[str, object, ...] + MutableShapeRef

A shape is a mapping (dict[str, object]) with attribute-based slot navigation.
Substrates extend these with their own storage mechanisms.

Type Parameters:
    T: Shape type (bound to ShapeBase)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.shape.collections import MappingBase, MutableMappingBase, ReactiveMappingBase

from .base import Ref


if TYPE_CHECKING:
    from everybase import Sentinel

    from ..shape import Shape as ShapeBase
    from ..shape import Slot


__all__ = [
    "MutableShapeRef",
    "ReactiveShapeRef",
    "ShapeRef",
]


# =============================================================================
# SHAPE REF — structured container with named slots
# =============================================================================


class ShapeRef[T: ShapeBase](
    Ref[dict[str, object]],
    MappingBase[str, object, object, object],
):
    """Reference to a shape — a structured container with named fields.

    A shape IS a mapping (dict[str, object]) by nature. Inherits full mapping
    ops (keys, values, items, get, extract, exists, etc.) from MappingBase.

    Attribute access is intercepted to look up slots on the shape class.
    If the name matches a slot, a child ref is created via slot.create_ref().
    Otherwise, falls back to default attribute resolution (finding methods,
    properties, etc. from base classes).

    Substrates must provide:
        __init__: set shape (and optionally key_type, value_type)
        resolve(ctx): build location identity
        fetch(ctx): extract value
        result(op): wrap morphism in typed Value
        _wrap_*: wrap operations in substrate Value types

    Slot navigation uses __getattr__ (fallback). Methods inherited from
    Ref, MappingBase, etc. resolve via normal MRO first. Only names not
    found in the class hierarchy trigger slot lookup.
    """

    def __init__(
        self,
        *,
        shape_type: type[T],
        **kwargs: object,
    ) -> None:
        """Initialize ref.

        Args:
            shape_type: Type of Shape this Ref points to
            **kwargs: Passed to super (address, parent, owner_shape, etc.)
        """
        self._shape_type = shape_type
        super().__init__(**kwargs)

    @property
    def shape_type(self) -> type[T]:
        """The Shape class type at this location."""
        return self._shape_type

    def _create_child_ref(self, key: str | Sentinel) -> Ref:
        """Create a reference to a child at the given key.

        Delegates to the shape's slot definitions.

        Args:
            key: Field name in the shape.

        Returns:
            Ref created by the slot.

        Raises:
            TypeError: If key is not a string.
            KeyError: If the shape has no slot with that name.
        """
        if not isinstance(key, str):
            raise TypeError(f"key must be str, `{type(key).__name__}` given")

        if hasattr(self._shape_type, "_slots") and key in self._shape_type._slots:
            slot: Slot = self._shape_type._slots[key]
            return slot.create_ref(owner_shape=self._shape_type, parent_ref=self)

        raise KeyError(f"{self._shape_type.__name__} has no slot '{key}'")

    def __getattr__(self, name: str) -> object:
        """Fallback attribute access — navigate to shape slots.

        Called only when normal MRO lookup fails, so inherited methods
        (execute, store, keys, etc.) resolve normally. Slot names that
        match the shape's _slots dict create child refs on the fly.
        """
        shape_type = self._shape_type

        if hasattr(shape_type, "_slots") and name in shape_type._slots:
            slot: Slot = shape_type._slots[name]
            return slot.create_ref(owner_shape=shape_type, parent_ref=self)

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
            f" (shape '{shape_type.__name__}' has no slot '{name}')"
        )


class MutableShapeRef[T: ShapeBase](
    ShapeRef[T],
    MutableMappingBase[str, object, object, object],
):
    """Shape + mapping mutations (set, delete, update) + store/length/clear."""


class ReactiveShapeRef[T: ShapeBase](
    MutableShapeRef[T],
    ReactiveMappingBase[str, object, object, object],
):
    """Shape + mapping mutations + change observation."""
