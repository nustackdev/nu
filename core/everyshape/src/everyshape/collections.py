"""Collection ref hierarchy — containers in a document model.

Structural types:
    ShapeRef        structured container with named slots (attribute navigation)
    MappingRef      key-value container (child ref creation)
    SequenceRef     ordered container (item ref creation)
    ShapesListRef   sequence of homogeneous shapes
    ShapesDictRef   mapping of homogeneous shapes

Each has three capability levels:
    Base            structural identity + navigation
    Mutable         + exists/length/clear
    Reactive        + change observation

Substrates extend these with their own storage mechanisms.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, ClassVar

from everyabc import Ref, Sentinel
from everybase.capabilities.loc_collection import (
    CollectionClearableBase,
    CollectionExistableBase,
    CollectionLengthableBase,
)
from everybase.capabilities.loc_reactive import ViewObservableBase


if TYPE_CHECKING:
    from everyabc import Slot, Term
    from everyshape.shape import ShapeBase


__all__ = [
    # Base
    "MappingRef",
    # Mappings
    "MutableMappingRef",
    "MutableSequenceRef",
    # Shapes
    "MutableShapeRef",
    "MutableShapesDictRef",
    "MutableShapesListRef",
    # Reactive
    "ReactiveMappingRef",
    "ReactiveSequenceRef",
    "ReactiveShapeRef",
    "ReactiveShapesDictRef",
    "ReactiveShapesListRef",
    "SequenceRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
]


# =============================================================================
# SHAPE REF — structured container with named slots
# =============================================================================


class ShapeRef[T: ShapeBase](Ref[dict[str, object]]):
    """Reference to a shape — a structured container with named fields.

    Attribute access is intercepted to look up slots on the shape class.
    If the name matches a slot, a child ref is created via slot.create_ref().
    Otherwise, falls back to default attribute resolution (finding methods,
    properties, etc. from base classes).

    Substrates must provide:
        __init__: set _shape_type (and optionally key_type, value_type)
        resolve(ctx): build location identity
        fetch(ctx): extract value

    The _PASSTHROUGH_ATTRS class variable controls which names skip slot
    lookup entirely (for performance). Substrates can extend this set.
    """

    _PASSTHROUGH_ATTRS: ClassVar[frozenset[str]] = frozenset(
        {
            # Python internals
            "__class__",
            "__dict__",
            "__repr__",
            "__str__",
            # Ref base
            "address",
            "_address",
            "parent",
            "_parent",
            "shape",
            "_shape",
            "resolve",
            "execute",
            "fetch",
            "is_self_pure",
            "is_subtree_pure",
            "get_root_shape",
            "_type_marker",
            "_resolve_address",
            # ShapeRef specific
            "shape_type",
            "_shape_type",
            "key_type",
            "value_type",
            "_create_child_ref",
        }
    )

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

    def __getattribute__(self, name: str) -> object:
        """Navigate to nested fields via attribute access.

        1. Passthrough or private attrs → default resolution
        2. Slot match on shape → create child ref
        3. Otherwise → default resolution (finds capability methods, etc.)
        """
        passthrough = object.__getattribute__(self, "_PASSTHROUGH_ATTRS")
        if name in passthrough or name.startswith("_"):
            return object.__getattribute__(self, name)

        shape_type: type[ShapeBase] = object.__getattribute__(self, "_shape_type")

        if hasattr(shape_type, "_slots") and name in shape_type._slots:
            slot: Slot = shape_type._slots[name]
            return slot.create_ref(owner_shape=shape_type, parent_ref=self)

        # Fall back to default resolution (capability methods, etc.)
        return object.__getattribute__(self, name)


class MutableShapeRef[T: ShapeBase](
    ShapeRef[T],
    CollectionExistableBase,
    CollectionLengthableBase,
    CollectionClearableBase,
):
    """Shape with collection-level operations: exists, length, clear."""


class ReactiveShapeRef[T: ShapeBase](
    MutableShapeRef[T],
    ViewObservableBase,
):
    """Shape with collection operations + change observation."""


# =============================================================================
# MAPPING REF — key-value container
# =============================================================================


class MappingRef[K, V](Ref[dict[K, V]]):
    """Reference to a mapping container.

    Mappings hold key-value pairs where values are homogeneous.
    Child refs are created for individual entries.

    Substrates must provide:
        __init__: set key_type, value_type, key_value_type, value_value_type
        resolve(ctx): build location identity
        fetch(ctx): extract value
        _create_child_ref(key): create ref for value at key
    """

    @abstractmethod
    def _create_child_ref(self, key: K | Sentinel | Term[K | Sentinel]) -> Ref:
        """Create a reference to the value at the given key.

        Substrate-specific: creates the appropriate child ref type.
        """
        ...


class MutableMappingRef[K, V](
    MappingRef[K, V],
    CollectionExistableBase,
    CollectionLengthableBase,
    CollectionClearableBase,
):
    """Mapping with collection-level operations: exists, length, clear."""


class ReactiveMappingRef[K, V](
    MutableMappingRef[K, V],
    ViewObservableBase,
):
    """Mapping with collection operations + change observation."""


# =============================================================================
# SEQUENCE REF — ordered container
# =============================================================================


class SequenceRef[T](Ref[list[T]]):
    """Reference to a sequence container.

    Sequences hold ordered items of homogeneous type.
    Item refs are created for individual elements.

    Substrates must provide:
        __init__: set item_type, item_value_type
        resolve(ctx): build location identity
        fetch(ctx): extract value
        _create_item_ref(index): create ref for item at index
    """

    @abstractmethod
    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> Ref:
        """Create a reference to the item at the given index.

        Substrate-specific: creates the appropriate item ref type.
        """
        ...


class MutableSequenceRef[T](
    SequenceRef[T],
    CollectionExistableBase,
    CollectionLengthableBase,
    CollectionClearableBase,
):
    """Sequence with collection-level operations: exists, length, clear."""


class ReactiveSequenceRef[T](
    MutableSequenceRef[T],
    ViewObservableBase,
):
    """Sequence with collection operations + change observation."""


# =============================================================================
# SHAPES LIST REF — sequence of homogeneous shapes
# =============================================================================


class ShapesListRef[T: ShapeBase](SequenceRef[dict]):
    """Reference to a list of homogeneous shapes.

    Each item in the sequence is a shape of the same type.
    Item refs create ShapeRefs for navigation into individual shapes.

    Substrates must provide:
        __init__: set _shape_type, item_type
        _create_item_ref(index): create ShapeRef for shape at index
    """

    @property
    def shape_type(self) -> type[T]:
        """The Shape class for items in this list."""
        return self._shape_type


class MutableShapesListRef[T: ShapeBase](
    ShapesListRef[T],
    MutableSequenceRef[dict],
):
    """Shapes list with collection-level operations."""


class ReactiveShapesListRef[T: ShapeBase](
    MutableShapesListRef[T],
    ReactiveSequenceRef[dict],
):
    """Shapes list with collection operations + change observation."""


# =============================================================================
# SHAPES DICT REF — mapping of homogeneous shapes
# =============================================================================


class ShapesDictRef[K, T: ShapeBase](MappingRef[K, dict]):
    """Reference to a mapping of homogeneous shapes.

    Each value in the mapping is a shape of the same type.
    Child refs create ShapeRefs for navigation into individual shapes.

    Substrates must provide:
        __init__: set _shape_type, key_type, key_value_type
        _create_child_ref(key): create ShapeRef for shape at key
    """

    @property
    def shape_type(self) -> type[T]:
        """The Shape class for values in this dict."""
        return self._shape_type


class MutableShapesDictRef[K, T: ShapeBase](
    ShapesDictRef[K, T],
    MutableMappingRef[K, dict],
):
    """Shapes dict with collection-level operations."""


class ReactiveShapesDictRef[K, T: ShapeBase](
    MutableShapesDictRef[K, T],
    ReactiveMappingRef[K, dict],
):
    """Shapes dict with collection operations + change observation."""
