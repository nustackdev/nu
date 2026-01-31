"""Dict substrate collection refs — containers in nested dicts.

These combine everyshape document model bases (navigation, capabilities)
with RefBase (plain dict navigation). No reactivity.

Structural types:
    ShapeRef        structured container with named slots
    MappingRef      key-value container (child ref creation)
    SequenceRef     ordered container (item ref creation)
    ShapesListRef   sequence of homogeneous shapes
    ShapesDictRef   mapping of homogeneous shapes
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from every_dict.items import ItemRef
from every_dict.ref import RefBase
from everybase import ensure_term
from everyshape import ShapeBase
from everyshape.collections import (
    MutableMappingRef,
    MutableSequenceRef,
    MutableShapeRef,
    MutableShapesDictRef,
    MutableShapesListRef,
)
from everyshape.collections import ShapeRef as _BaseShapeRef


if TYPE_CHECKING:
    from everyabc import Sentinel, Term


__all__ = [
    "MappingRef",
    "SequenceRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
]


# =============================================================================
# SHAPE REF
# =============================================================================


class ShapeRef[T: ShapeBase](
    MutableShapeRef[T],
    RefBase[dict[str, object]],
):
    """Dict shape reference — structured container backed by nested dict."""

    _PASSTHROUGH_ATTRS: ClassVar[frozenset[str]] = _BaseShapeRef._PASSTHROUGH_ATTRS

    def __init__(
        self,
        address: str | int | Term,
        shape_type: type[T],
        parent: RefBase | None = None,
        shape: type[ShapeBase] | None = None,
    ) -> None:
        """Initialize shape reference."""
        super().__init__(address, parent, shape)
        self._shape_type = shape_type
        self.key_type: type = str
        self.value_type: type = object


# =============================================================================
# MAPPING REF
# =============================================================================


class MappingRef[K, V](
    MutableMappingRef[K, V],
    RefBase[dict[K, V]],
):
    """Dict mapping reference — key-value container backed by nested dict."""

    def __init__(
        self,
        address: str | int | Term,
        value_type: type[V],
        key_type: type[K],
        key_value_type: type,
        value_value_type: type,
        parent: RefBase | None = None,
        shape: type[ShapeBase] | None = None,
    ) -> None:
        """Initialize mapping reference."""
        super().__init__(address, parent, shape)
        self.value_type = value_type
        self.key_type = key_type
        self.key_value_type = key_value_type
        self.value_value_type = value_value_type

    def _create_child_ref(self, key: K | Sentinel | Term[K | Sentinel]) -> ItemRef[V, ...]:
        """Create a reference to the value at the given key."""
        return ItemRef(
            address=ensure_term(key),
            value_type=self.value_type,
            value_value_type=self.value_value_type,
            parent=self,
            shape=self._shape,
        )


# =============================================================================
# SEQUENCE REF
# =============================================================================


class SequenceRef[T](
    MutableSequenceRef[T],
    RefBase[list[T]],
):
    """Dict sequence reference — ordered container backed by nested list."""

    def __init__(
        self,
        address: str | int | Term,
        item_type: type[T],
        item_value_type: type,
        parent: RefBase | None = None,
        shape: type[ShapeBase] | None = None,
    ) -> None:
        """Initialize sequence reference."""
        super().__init__(address, parent, shape)
        self.item_type = item_type
        self.item_value_type = item_value_type

    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> ItemRef[T, ...]:
        """Create a reference to the item at the given index."""
        return ItemRef(
            address=ensure_term(index),
            value_type=self.item_type,
            value_value_type=self.item_value_type,
            parent=self,
            shape=self._shape,
        )


# =============================================================================
# SHAPES LIST REF
# =============================================================================


class ShapesListRef[T: ShapeBase](
    MutableShapesListRef[T],
    RefBase[list[dict]],
):
    """Dict shapes list reference — sequence of homogeneous shapes."""

    def __init__(
        self,
        address: str | int | Term,
        shape_type: type[T],
        parent: RefBase | None = None,
        shape: type[ShapeBase] | None = None,
    ) -> None:
        """Initialize shapes list reference."""
        super().__init__(address, parent, shape)
        self._shape_type = shape_type
        self.item_type = dict

    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> ShapeRef[T]:
        """Create a reference to a shape at the given index."""
        return ShapeRef(
            address=ensure_term(index),
            shape_type=self._shape_type,
            parent=self,
            shape=self._shape,
        )


# =============================================================================
# SHAPES DICT REF
# =============================================================================


class ShapesDictRef[K, T: ShapeBase](
    MutableShapesDictRef[K, T],
    RefBase[dict[K, dict]],
):
    """Dict shapes dict reference — mapping of homogeneous shapes."""

    def __init__(
        self,
        address: str | int | Term,
        key_type: type[K],
        key_value_type: type,
        shape_type: type[T],
        parent: RefBase | None = None,
        shape: type[ShapeBase] | None = None,
    ) -> None:
        """Initialize shapes dict reference."""
        super().__init__(address, parent, shape)
        self.value_type = dict
        self.key_type = key_type
        self.key_value_type = key_value_type
        self._shape_type = shape_type

    def _create_child_ref(self, key: K | Sentinel | Term[K | Sentinel]) -> ShapeRef[T]:
        """Create a reference to a shape at the given key."""
        return ShapeRef(
            address=ensure_term(key),
            shape_type=self._shape_type,
            parent=self,
            shape=self._shape,
        )
