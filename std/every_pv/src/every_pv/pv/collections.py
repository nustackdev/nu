"""Concrete PV collection ref implementations.

Collection refs need LAZY implementations because PV storage can be huge
(e.g., petabyte-scale RocksDB). Operations like find(), filter(), map()
must work streaming without loading everything into memory.

Unlike primitive refs, collection refs don't inherit from everybase RefBases
because the interface is fundamentally different:
- everybase collection refs: get() loads entire collection, then run operations
- PV collection refs: operations work lazily/streaming on the view directly
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pv.typing import Value
from pv.typing.view import MutableMappingView, MutableSequenceView

from every import Ref, RValue, Sentinel, Shape
from every_pv.traits.bases_collections import (
    MutableMappingRefBase,
    MutableSequenceRefBase,
)
from everybase import (
    AnyRef,
    DictRef,
    IntRef,
    ListRef,
    StrRef,
    ensure_term,
)

from .base import PVViewRefMixin
from .primitives import PVDictItemRef, PVListItemRef


if TYPE_CHECKING:
    from pv.loc import path


__all__ = [
    "PVDictRef",
    "PVListRef",
    "PVShapeRef",
    "PVShapesDictRef",
    "PVShapesListRef",
]


# Placeholder for slice refs (temporarily disabled)
class SequenceSliceRef:
    pass


class SequenceShapeSliceRef:
    pass


# =============================================================================
# SHAPE REF
# =============================================================================


class PVShapeRef[T: Shape](
    PVViewRefMixin[dict[str, Value], MutableMappingView],
    MutableMappingRefBase[
        dict[str, Value],  # CollectionT
        str,  # KeyT
        Value,  # ValueT
        DictRef[str, Value],  # CollectionValueT
        StrRef,  # KeyValueT
        AnyRef,  # ValueValueT
        MutableMappingView,  # ViewT
        Ref,  # ChildRefT
    ],
):
    """Reference to a nested shape location.

    Points to container nodes with structure defined by a Shape.
    Supports navigation to nested fields via attribute access.
    """

    # Passthrough attributes that should not trigger slot lookup
    _PASSTHROUGH_ATTRS: ClassVar[frozenset[str]] = frozenset(
        {
            # Python internals
            "__class__",
            "__dict__",
            "__repr__",
            "__str__",
            # Ref base
            "address",
            "view_type",
            "parent_ref",
            "parent",
            "owner_shape",
            "resolve",
            "execute",
            "is_pure",
            "get_root_shape",
            "get_owner_shape",
            # ShapeRef specific
            "shape_type",
            "key_type",
            "value_type",
            "result",
            "_create_child_ref",
            "get_view",
            # Ref annotation attributes
            "collection_type",
            "collection_value_type",
            "key_value_type",
            "value_value_type",
            # ExtractableBase / StorableBase
            "extract",
            "get",
            "store",
            # ClearableBase / LengthableBase
            "clear",
            "length",
            # ExistableBase
            "exists",
            "missing",
            # ViewObservableBase
            "on_change",
            "on_child_change",
            "on_children_change",
            "on_descendants_change",
            # Query bases
            "keys",
            "values",
            "items",
            # Mapping iterable
            "map_values",
            "map_items",
            "filter",
            "reduce",
            "find_key",
            "find_value",
            "find_item",
        }
    )

    def __init__(
        self,
        address: path.PathAddress,
        shape_type: type[T],
        view_type: type[MutableMappingView],
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize shape reference."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.shape_type = shape_type
        self.view_type = view_type
        self.key_type: type = str
        self.value_type: type = object
        self.collection_type: type[dict[str, Value]] = dict
        self.collection_value_type: type[DictRef[str, Value]] = DictRef
        self.key_value_type: type[StrRef] = StrRef
        self.value_value_type: type[AnyRef] = AnyRef

    def result(self, op: RValue) -> DictRef[str, Value]:
        """Wrap an operation result in a DictRef container."""
        return DictRef(op)

    def _create_child_ref(self, key: str | Sentinel | RValue[str | Sentinel]) -> Ref:
        """Create a reference to a child at the given key."""
        if isinstance(key, RValue):
            raise TypeError("ShapeRef does not support computed keys; use attribute access")

        if not isinstance(key, str):
            raise TypeError(f"key must be str, `{type(key).__name__}` given")

        if hasattr(self.shape_type, "_slots") and key in self.shape_type._slots:
            slot = self.shape_type._slots[key]
            return slot.create_ref(owner_shape=self.shape_type, parent_ref=self)

        raise KeyError(f"{self.shape_type.__name__} has no slot '{key}'")

    def __getattribute__(self, name: str) -> object:
        """Navigate to nested fields via attribute access."""
        passthrough = object.__getattribute__(self, "_PASSTHROUGH_ATTRS")
        if name in passthrough:
            return object.__getattribute__(self, name)

        shape_type: type[Shape] = object.__getattribute__(self, "shape_type")

        if hasattr(shape_type, "_slots") and name in shape_type._slots:
            slot = shape_type._slots[name]
            return slot.create_ref(owner_shape=shape_type, parent_ref=self)

        raise AttributeError(f"{shape_type.__name__} has no slot '{name}'")


# =============================================================================
# DICT REF
# =============================================================================


class PVDictRef[K: int | str, V: Value, KeyValueT, ValueValueT](
    PVViewRefMixin[dict[K, V], MutableMappingView],
    MutableMappingRefBase[
        dict[K, V],  # CollectionT
        K,  # KeyT
        V,  # ValueT
        DictRef[K, V],  # CollectionValueT
        KeyValueT,  # KeyValueT
        ValueValueT,  # ValueValueT
        MutableMappingView,  # ViewT
        PVDictItemRef[V, ValueValueT],  # ChildRefT
    ],
):
    """Reference to a mapping container with lazy operations.

    All operations (filter, find, etc.) work lazily on the view
    without loading everything into memory.
    """

    collection_type: type[dict[K, V]] = dict
    collection_value_type: type[DictRef[K, V]] = DictRef

    def __init__(
        self,
        address: path.PathAddress,
        value_type: type[V],
        key_type: type[K],
        view_type: type[MutableMappingView],
        key_value_type: type[KeyValueT],
        value_value_type: type[ValueValueT],
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize mapping reference."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.value_type = value_type
        self.key_type = key_type
        self.view_type = view_type
        self.key_value_type = key_value_type
        self.value_value_type = value_value_type

    def result(self, op: RValue) -> DictRef[K, V]:
        """Wrap an operation result in a DictRef container."""
        return DictRef(op)

    def _create_child_ref(
        self, key: K | Sentinel | RValue[K | Sentinel]
    ) -> PVDictItemRef[V, ValueValueT]:
        """Create a reference to a child at the given key."""
        return PVDictItemRef(
            address=ensure_term(key),
            value_type=self.value_type,
            value_value_type=self.value_value_type,
            parent_ref=self,
            owner_shape=self.owner_shape,
        )


# =============================================================================
# LIST REF
# =============================================================================


class PVListRef[T, ItemValueT](
    PVViewRefMixin[list[T], MutableSequenceView],
    MutableSequenceRefBase[
        list[T],  # CollectionT
        T,  # ItemT
        ListRef[T],  # CollectionValueT
        ItemValueT,  # ItemValueT
        MutableSequenceView,  # ViewT
        int,  # IndexT
        IntRef,  # IndexValueT
        ListRef[T],  # SliceValueT
        PVListItemRef[T, ItemValueT],  # ItemRefT
        SequenceSliceRef,  # SliceRefT
    ],
):
    """Reference to a sequence container with lazy operations.

    All operations (filter, find, map, etc.) work lazily on the view
    without loading everything into memory.
    """

    collection_type: type[list[T]] = list
    collection_value_type: type[ListRef[T]] = ListRef
    index_type: type[int] = int
    index_value_type: type[IntRef] = IntRef

    def __init__(
        self,
        address: path.PathAddress,
        item_type: type[T],
        item_value_type: type[ItemValueT],
        view_type: type[MutableSequenceView],
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize sequence reference."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.item_type = item_type
        self.item_value_type = item_value_type
        self.view_type = view_type

    def result(self, op: RValue) -> ListRef[T]:
        """Wrap an operation result in a ListRef container."""
        return ListRef(op)

    def _create_item_ref(
        self, index: int | Sentinel | RValue[int | Sentinel]
    ) -> PVListItemRef[T, ItemValueT]:
        """Create a reference to an item at the given index."""
        return PVListItemRef(
            address=ensure_term(index),
            value_type=self.item_type,
            value_value_type=self.item_value_type,
            parent_ref=self,
            owner_shape=self.owner_shape,
        )

    def _create_slice_ref(self, key: slice) -> SequenceSliceRef:
        """Create a reference to a slice of the sequence."""
        raise NotImplementedError("Slice refs not yet implemented")


# =============================================================================
# SHAPES LIST REF
# =============================================================================


class PVShapesListRef[T: Shape](
    PVViewRefMixin[list[dict], MutableSequenceView],
    MutableSequenceRefBase[
        list[dict],  # CollectionT
        dict,  # ItemT (shapes serialize to dicts)
        ListRef[dict],  # CollectionValueT
        DictRef[str, Value],  # ItemValueT (shape items are dicts)
        MutableSequenceView,  # ViewT
        int,  # IndexT
        IntRef,  # IndexValueT
        ListRef[dict],  # SliceValueT
        PVShapeRef[T],  # ItemRefT
        SequenceShapeSliceRef,  # SliceRefT
    ],
):
    """Reference to a list of homogeneous shapes."""

    collection_type: type[list[dict]] = list
    collection_value_type: type[ListRef[dict]] = ListRef
    item_value_type: type[DictRef[str, Value]] = DictRef
    index_type: type[int] = int
    index_value_type: type[IntRef] = IntRef

    def __init__(
        self,
        address: path.PathAddress,
        shape_type: type[T],
        view_type: type[MutableSequenceView],
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize sequence shape reference."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.shape_type = shape_type
        self.item_type = dict
        self.view_type = view_type

    def result(self, op: RValue) -> ListRef[dict]:
        """Wrap an operation result in a ListRef container."""
        return ListRef(op)

    def _create_item_ref(self, index: int | Sentinel | RValue[int | Sentinel]) -> PVShapeRef[T]:
        """Create a reference to a shape at the given index."""
        from every_view import DictView

        return PVShapeRef(
            address=ensure_term(index),
            shape_type=self.shape_type,
            view_type=DictView,
            parent_ref=self,
            owner_shape=self.owner_shape,
        )

    def _create_slice_ref(self, key: slice) -> SequenceShapeSliceRef:
        """Create a reference to a slice of the sequence."""
        raise NotImplementedError("Slice refs not yet implemented")


# =============================================================================
# SHAPES DICT REF
# =============================================================================


class PVShapesDictRef[K: int | str, T: Shape, KeyValueT](
    PVViewRefMixin[dict[K, dict], MutableMappingView],
    MutableMappingRefBase[
        dict[K, dict],  # CollectionT
        K,  # KeyT
        dict,  # ValueT (shapes serialize to dicts)
        DictRef[K, dict],  # CollectionValueT
        KeyValueT,  # KeyValueT
        DictRef[str, Value],  # ValueValueT (shape values are dicts)
        MutableMappingView,  # ViewT
        PVShapeRef[T],  # ChildRefT
    ],
):
    """Reference to a mapping of homogeneous shapes."""

    collection_type: type[dict[K, dict]] = dict
    collection_value_type: type[DictRef[K, dict]] = DictRef
    value_value_type: type[DictRef[str, Value]] = DictRef

    def __init__(
        self,
        address: path.PathAddress,
        key_type: type[K],
        key_value_type: type[KeyValueT],
        shape_type: type[T],
        view_type: type[MutableMappingView],
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize mapping shape reference."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.value_type = dict
        self.key_type = key_type
        self.key_value_type = key_value_type
        self.shape_type = shape_type
        self.view_type = view_type

    def result(self, op: RValue) -> DictRef[K, dict]:
        """Wrap an operation result in a DictRef container."""
        return DictRef(op)

    def _create_child_ref(self, key: K | Sentinel | RValue[K | Sentinel]) -> PVShapeRef[T]:
        """Create a reference to a shape at the given key."""
        from every_view import DictView

        return PVShapeRef(
            address=ensure_term(key),
            shape_type=self.shape_type,
            view_type=DictView,
            parent_ref=self,
            owner_shape=self.owner_shape,
        )
