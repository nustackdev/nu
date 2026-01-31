"""Concrete PV collection ref implementations.

Collection refs need LAZY implementations because PV storage can be huge
(e.g., petabyte-scale RocksDB). Operations like find(), filter(), map()
must work streaming without loading everything into memory.

Unlike primitive refs, collection refs don't inherit from everybase RefBases
because the interface is fundamentally different:
- everybase collection refs: fetch() loads entire collection, then run operations
- PV collection refs: operations work lazily/streaming on the view directly
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pv.collections import MutableMappingView, MutableSequenceView
from pv.types import Value as StorageValue

from every_pv.ref import PVRefBase, PVViewRef
from every_pv.shape import PVShape
from every_pv.traits.bases_collections import (
    MutableMappingRefBase,
    MutableSequenceRefBase,
)
from everyabc import Ref, RValue, Sentinel, Term, Value
from everybase import (
    AnyValue,
    DictValue,
    IntValue,
    ListValue,
    StrValue,
    ensure_term,
)

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


class PVShapeRef[T: PVShape](
    PVViewRef[dict[str, StorageValue], MutableMappingView],
    MutableMappingRefBase[
        dict[str, StorageValue],  # CollectionT
        str,  # KeyT
        StorageValue,  # ValueT
        DictValue[str, StorageValue],  # CollectionValueT
        StrValue,  # KeyValueT
        AnyValue,  # ValueValueT
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
            "_address",
            "view_type",
            "_view_type",
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
            "result",
            "_create_child_ref",
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
        self.collection_type: type[dict[str, StorageValue]] = dict
        self.collection_value_type: type[DictValue[str, StorageValue]] = DictValue
        self.key_value_type: type[StrValue] = StrValue
        self.value_value_type: type[AnyValue] = AnyValue

    @property
    def shape_type(self) -> type[T]:
        """The Shape class type at this location."""
        return self._shape_type

    def result(self, op: RValue) -> DictValue[str, StorageValue]:
        """Wrap an operation result in a DictValue container."""
        return DictValue(op)

    def _create_child_ref(self, key: str | Sentinel | RValue[str | Sentinel]) -> Ref:
        """Create a reference to a child at the given key."""
        if isinstance(key, RValue):
            raise TypeError("ShapeRef does not support computed keys; use attribute access")

        if not isinstance(key, str):
            raise TypeError(f"key must be str, `{type(key).__name__}` given")

        if hasattr(self._shape_type, "_slots") and key in self._shape_type._slots:
            slot = self._shape_type._slots[key]
            return slot.create_ref(owner_shape=self._shape_type, parent_ref=self)

        raise KeyError(f"{self._shape_type.__name__} has no slot '{key}'")

    def __getattribute__(self, name: str) -> object:
        """Navigate to nested fields via attribute access."""
        passthrough = object.__getattribute__(self, "_PASSTHROUGH_ATTRS")
        if name in passthrough:
            return object.__getattribute__(self, name)

        shape_type: type[PVShape] = object.__getattribute__(self, "_shape_type")

        if hasattr(shape_type, "_slots") and name in shape_type._slots:
            slot = shape_type._slots[name]
            return slot.create_ref(owner_shape=shape_type, parent_ref=self)

        raise AttributeError(f"{shape_type.__name__} has no slot '{name}'")


# =============================================================================
# DICT REF
# =============================================================================


class PVDictRef[K: int | str, V: StorageValue, KeyValueT, ValueValueT: Value](
    PVViewRef[dict[K, V], MutableMappingView],
    MutableMappingRefBase[
        dict[K, V],  # CollectionT
        K,  # KeyT
        V,  # ValueT
        DictValue[K, V],  # CollectionValueT
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
    collection_value_type: type[DictValue[K, V]] = DictValue

    def __init__(
        self,
        address: path.PathAddress | Term,
        value_type: type[V],
        key_type: type[K],
        view_type: type[MutableMappingView],
        key_value_type: type[KeyValueT],
        value_value_type: type[ValueValueT],
        parent: PVRefBase | None = None,
        shape: type[PVShape] | None = None,
    ) -> None:
        """Initialize mapping reference."""
        super().__init__(address, view_type, parent, shape)
        self.value_type = value_type
        self.key_type = key_type
        self.key_value_type = key_value_type
        self.value_value_type = value_value_type

    def result(self, op: RValue) -> DictValue[K, V]:
        """Wrap an operation result in a DictValue container."""
        return DictValue(op)

    def _create_child_ref(
        self, key: K | Sentinel | RValue[K | Sentinel]
    ) -> PVDictItemRef[V, ValueValueT]:
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
    PVViewRef[list[T], MutableSequenceView],
    MutableSequenceRefBase[
        list[T],  # CollectionT
        T,  # ItemT
        ListValue[T],  # CollectionValueT
        ItemValueT,  # ItemValueT
        MutableSequenceView,  # ViewT
        int,  # IndexT
        IntValue,  # IndexValueT
        ListValue[T],  # SliceValueT
        PVListItemRef[T, ItemValueT],  # ItemRefT
        SequenceSliceRef,  # SliceRefT
    ],
):
    """Reference to a sequence container with lazy operations.

    All operations (filter, find, map, etc.) work lazily on the view
    without loading everything into memory.
    """

    collection_type: type[list[T]] = list
    collection_value_type: type[ListValue[T]] = ListValue
    index_type: type[int] = int
    index_value_type: type[IntValue] = IntValue

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

    def result(self, op: RValue) -> ListValue[T]:
        """Wrap an operation result in a ListValue container."""
        return ListValue(op)

    def _create_item_ref(
        self, index: int | Sentinel | RValue[int | Sentinel]
    ) -> PVListItemRef[T, ItemValueT]:
        """Create a reference to an item at the given index."""
        return PVListItemRef(
            address=ensure_term(index),
            value_type=self.item_type,
            value_value_type=self.item_value_type,
            parent=self,
            shape=self._shape,
        )

    def _create_slice_ref(self, key: slice) -> SequenceSliceRef:
        """Create a reference to a slice of the sequence."""
        raise NotImplementedError("Slice refs not yet implemented")


# =============================================================================
# SHAPES LIST REF
# =============================================================================


class PVShapesListRef[T: PVShape](
    PVViewRef[list[dict], MutableSequenceView],
    MutableSequenceRefBase[
        list[dict],  # CollectionT
        dict,  # ItemT (shapes serialize to dicts)
        ListValue[dict],  # CollectionValueT
        DictValue[str, StorageValue],  # ItemValueT (shape items are dicts)
        MutableSequenceView,  # ViewT
        int,  # IndexT
        IntValue,  # IndexValueT
        ListValue[dict],  # SliceValueT
        PVShapeRef[T],  # ItemRefT
        SequenceShapeSliceRef,  # SliceRefT
    ],
):
    """Reference to a list of homogeneous shapes."""

    collection_type: type[list[dict]] = list
    collection_value_type: type[ListValue[dict]] = ListValue
    item_value_type: type[DictValue[str, StorageValue]] = DictValue
    index_type: type[int] = int
    index_value_type: type[IntValue] = IntValue

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

    @property
    def shape_type(self) -> type[T]:
        """The Shape class for items in this list."""
        return self._shape_type

    def result(self, op: RValue) -> ListValue[dict]:
        """Wrap an operation result in a ListValue container."""
        return ListValue(op)

    def _create_item_ref(self, index: int | Sentinel | RValue[int | Sentinel]) -> PVShapeRef[T]:
        """Create a reference to a shape at the given index."""
        from every_view import DictView

        return PVShapeRef(
            address=ensure_term(index),
            shape_type=self._shape_type,
            view_type=DictView,
            parent=self,
            shape=self._shape,
        )

    def _create_slice_ref(self, key: slice) -> SequenceShapeSliceRef:
        """Create a reference to a slice of the sequence."""
        raise NotImplementedError("Slice refs not yet implemented")


# =============================================================================
# SHAPES DICT REF
# =============================================================================


class PVShapesDictRef[K: int | str, T: PVShape, KeyValueT](
    PVViewRef[dict[K, dict], MutableMappingView],
    MutableMappingRefBase[
        dict[K, dict],  # CollectionT
        K,  # KeyT
        dict,  # ValueT (shapes serialize to dicts)
        DictValue[K, dict],  # CollectionValueT
        KeyValueT,  # KeyValueT
        DictValue[str, StorageValue],  # ValueValueT (shape values are dicts)
        MutableMappingView,  # ViewT
        PVShapeRef[T],  # ChildRefT
    ],
):
    """Reference to a mapping of homogeneous shapes."""

    collection_type: type[dict[K, dict]] = dict
    collection_value_type: type[DictValue[K, dict]] = DictValue
    value_value_type: type[DictValue[str, StorageValue]] = DictValue

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

    @property
    def shape_type(self) -> type[T]:
        """The Shape class for values in this dict."""
        return self._shape_type

    def result(self, op: RValue) -> DictValue[K, dict]:
        """Wrap an operation result in a DictValue container."""
        return DictValue(op)

    def _create_child_ref(self, key: K | Sentinel | RValue[K | Sentinel]) -> PVShapeRef[T]:
        """Create a reference to a shape at the given key."""
        from every_view import DictView

        return PVShapeRef(
            address=ensure_term(key),
            shape_type=self._shape_type,
            view_type=DictView,
            parent=self,
            shape=self._shape,
        )
