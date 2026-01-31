"""Concrete PV collection ref implementations.

PV collection refs combine everyshape document model bases (navigation,
capabilities) with PVViewRef (PV substrate: view hierarchy navigation).

Lazy operations note: find(), filter(), map() etc. work streaming on
PV views without loading everything into memory. The everybase collection
capabilities (exists, length, clear) added via everyshape are cheap
single-operation calls, not bulk iteration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pv.collections import MutableMappingView, MutableSequenceView
from pv.types import Value as StorageValue

from every_pv.primitives import PVDictItemRef, PVListItemRef
from every_pv.ref import PVRefBase, PVViewRef
from everybase import ensure_term
from everyshape import ShapeBase as PVShape
from everyshape.collections import (
    ReactiveMappingRef,
    ReactiveSequenceRef,
    ReactiveShapeRef,
    ReactiveShapesDictRef,
    ReactiveShapesListRef,
    ShapeRef,
)


if TYPE_CHECKING:
    from pv.loc import path

    from everyabc import Sentinel, Term


__all__ = [
    "PVDictRef",
    "PVListRef",
    "PVShapeRef",
    "PVShapesDictRef",
    "PVShapesListRef",
]


# =============================================================================
# SHAPE REF
# =============================================================================


class PVShapeRef[T: PVShape](
    ReactiveShapeRef[T],
    PVViewRef[dict[str, StorageValue], MutableMappingView],
):
    """PV shape reference — document model + PV substrate.

    Inherits attribute navigation and _create_child_ref from everyshape ShapeRef.
    Inherits PV path resolution and view fetching from PVViewRef.
    """

    # Extend passthrough with PV-specific attributes
    _PASSTHROUGH_ATTRS: ClassVar[frozenset[str]] = ShapeRef._PASSTHROUGH_ATTRS | frozenset(
        {
            "view_type",
            "_view_type",
        }
    )

    def __init__(
        self,
        address: path.PathAddress | Term,
        shape_type: type[T],
        view_type: type[MutableMappingView],
        parent: PVRefBase | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize shape reference."""
        super().__init__(address, view_type, parent, shape)
        self._shape_type = shape_type
        self.key_type: type = str
        self.value_type: type = object


# =============================================================================
# DICT REF
# =============================================================================


class PVDictRef[K: int | str, V: StorageValue](
    ReactiveMappingRef[K, V],
    PVViewRef[dict[K, V], MutableMappingView],
):
    """PV mapping reference — document model + PV substrate.

    Operations work lazily on PV views without loading into memory.
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        value_type: type[V],
        key_type: type[K],
        view_type: type[MutableMappingView],
        key_value_type: type,
        value_value_type: type,
        parent: PVRefBase | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize mapping reference."""
        super().__init__(address, view_type, parent, shape)
        self.value_type = value_type
        self.key_type = key_type
        self.key_value_type = key_value_type
        self.value_value_type = value_value_type

    def _create_child_ref(self, key: K | Sentinel | Term[K | Sentinel]) -> PVDictItemRef[V, ...]:
        """Create a reference to a child at the given key."""
        return PVDictItemRef(
            address=ensure_term(key),
            value_type=self.value_type,
            value_value_type=self.value_value_type,
            parent=self,
            shape=self._shape,
        )


# =============================================================================
# LIST REF
# =============================================================================


class PVListRef[T, ItemValueT](
    ReactiveSequenceRef[T],
    PVViewRef[list[T], MutableSequenceView],
):
    """PV sequence reference — document model + PV substrate.

    Operations work lazily on PV views without loading into memory.
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        item_type: type[T],
        item_value_type: type[ItemValueT],
        view_type: type[MutableSequenceView],
        parent: PVRefBase | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize sequence reference."""
        super().__init__(address, view_type, parent, shape)
        self.item_type = item_type
        self.item_value_type = item_value_type

    def _create_item_ref(
        self, index: int | Sentinel | Term[int | Sentinel]
    ) -> PVListItemRef[T, ItemValueT]:
        """Create a reference to an item at the given index."""
        return PVListItemRef(
            address=ensure_term(index),
            value_type=self.item_type,
            value_value_type=self.item_value_type,
            parent=self,
            shape=self._shape,
        )


# =============================================================================
# SHAPES LIST REF
# =============================================================================


class PVShapesListRef[T: PVShape](
    ReactiveShapesListRef[T],
    PVViewRef[list[dict], MutableSequenceView],
):
    """PV shapes list reference — document model + PV substrate."""

    def __init__(
        self,
        address: path.PathAddress | Term,
        shape_type: type[T],
        view_type: type[MutableSequenceView],
        parent: PVRefBase | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize sequence shape reference."""
        super().__init__(address, view_type, parent, shape)
        self._shape_type = shape_type
        self.item_type = dict

    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> PVShapeRef[T]:
        """Create a reference to a shape at the given index."""
        from every_pv.views import DictView

        return PVShapeRef(
            address=ensure_term(index),
            shape_type=self._shape_type,
            view_type=DictView,
            parent=self,
            shape=self._shape,
        )


# =============================================================================
# SHAPES DICT REF
# =============================================================================


class PVShapesDictRef[K: int | str, T: PVShape, KeyValueT](
    ReactiveShapesDictRef[K, T],
    PVViewRef[dict[K, dict], MutableMappingView],
):
    """PV shapes dict reference — document model + PV substrate."""

    def __init__(
        self,
        address: path.PathAddress | Term,
        key_type: type[K],
        key_value_type: type[KeyValueT],
        shape_type: type[T],
        view_type: type[MutableMappingView],
        parent: PVRefBase | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize mapping shape reference."""
        super().__init__(address, view_type, parent, shape)
        self.value_type = dict
        self.key_type = key_type
        self.key_value_type = key_value_type
        self._shape_type = shape_type

    def _create_child_ref(self, key: K | Sentinel | Term[K | Sentinel]) -> PVShapeRef[T]:
        """Create a reference to a shape at the given key."""
        from every_pv.views import DictView

        return PVShapeRef(
            address=ensure_term(key),
            shape_type=self._shape_type,
            view_type=DictView,
            parent=self,
            shape=self._shape,
        )
