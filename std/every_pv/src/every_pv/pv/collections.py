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
from pv.types import Value

from every_pv.ref import PVRefBase, PVViewRef
from every_pv.shape import PVShape
from every_pv.traits.bases_collections import (
    MutableMappingRefBase,
    MutableSequenceRefBase,
)
from everyabc import Ref, RValue, Sentinel, Term
from everybase import (
    AnyRef,
    DictRef,
    IntRef,
    ListRef,
    StrRef,
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
    PVViewRef[dict[str, Value], MutableMappingView],
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
        self.collection_type: type[dict[str, Value]] = dict
        self.collection_value_type: type[DictRef[str, Value]] = DictRef
        self.key_value_type: type[StrRef] = StrRef
        self.value_value_type: type[AnyRef] = AnyRef

    @property
    def shape_type(self) -> type[T]:
        """The Shape class type at this location."""
        return self._shape_type

    def result(self, op: RValue) -> DictRef[str, Value]:
        """Wrap an operation result in a DictRef container."""
        return DictRef(op)

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


class PVDictRef[K: int | str, V: Value, KeyValueT, ValueValueT](
    PVViewRef[dict[K, V], MutableMappingView],
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

    def result(self, op: RValue) -> ListRef[dict]:
        """Wrap an operation result in a ListRef container."""
        return ListRef(op)

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

    def result(self, op: RValue) -> DictRef[K, dict]:
        """Wrap an operation result in a DictRef container."""
        return DictRef(op)

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
