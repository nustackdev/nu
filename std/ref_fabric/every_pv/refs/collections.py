"""Ref implementations.

This module provides ready-to-use ref classes for collection-like values (list, dict, etc).

Usage:
    class MyShape(Shape):
        fruits = ListRef(str)

    # Create operations
    MyShape.fruits.store(["apple", "orange"])
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pv.typing import Value
from pv.typing.view import MutableMappingView, MutableSequenceView
from term.shape import Shape
from term.types import (
    AnyType,
    DictType,
    IntType,
    ListType,
    StrType,
)
from term.typing import Sentinel

from every._abc import Ref, RValue, literal

from .bases_collections import (
    MutableMappingRefBase,
    MutableSequenceRefBase,
)
from .primitives import DictItemRef, ListItemRef
from .ref import ViewRef


if TYPE_CHECKING:
    from pv.loc import path


__all__ = [
    "DictRef",
    "ListRef",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
]


# ===============================================================
# FIXME: tmply disabled slice interfaces
# ===============================================================
# from ..exp.islices import MappingISliceRef, MappingShapeISliceRef
# from ..exp.slices import SequenceShapeSliceRef, SequenceSliceRef
# ===============================================================


class MappingISliceRef:
    pass


class MappingShapeISliceRef:
    pass


class SequenceShapeSliceRef:
    pass


class SequenceSliceRef:
    pass


# =====================


class ShapeRef[T: Shape](
    MutableMappingRefBase[
        dict[str, Value],  # CollectionT
        str,  # KeyT
        Value,  # ValueT
        DictType[str, Value],  # CollectionValueT
        StrType,  # KeyValueT
        AnyType,  # ValueValueT
        MutableMappingView,  # ViewT
        Ref,  # ChildRefT
    ],
    ViewRef,
):
    """Reference to a nested shape location.

    Points to container nodes with structure defined by a Shape.
    Supports navigation to nested fields via attribute access.

    Type Parameters:
        T: The Shape class this reference points to

    Example:
        class Profile(Shape):
            email: ItemRef[str, StrType] = ItemSlot(str)

        class User(Shape):
            profile: ShapeRef[Profile] = ShapeSlot(Profile)

        # Navigate to nested field
        User.profile.email  # Returns ItemRef[str, StrType]
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
            # Type annotation attributes
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
        """Initialize shape reference.

        Args:
            address: Address of this field in parent's domain
            shape_type: Shape class defining structure
            view_type: View class for this container
            parent_ref: Parent reference in navigation chain
            owner_shape: Shape class this ref belongs to
        """
        super().__init__(address, view_type, parent_ref, owner_shape)
        self.shape_type = shape_type
        self.key_type: type = str
        self.value_type: type = object
        self.collection_type: type[dict[str, Value]] = dict
        self.collection_value_type: type[DictType[str, Value]] = DictType
        self.key_value_type: type[StrType] = StrType
        self.value_value_type: type[AnyType] = AnyType

    def result(self, op: RValue) -> DictType[str, Value]:
        """Wrap an operation result in a DictType container.

        Args:
            op: The operation to wrap

        Returns:
            DictType wrapping the operation
        """
        return DictType(op)

    def _create_child_ref(self, key: str | Sentinel | RValue[str | Sentinel]) -> Ref:
        """Create a reference to a child at the given key.

        For ShapeRef, this delegates to the slot's create_ref.

        Args:
            key: Child key (field name)

        Returns:
            Ref to the child field

        Raises:
            KeyError: If key is not a valid field name
        """
        if isinstance(key, RValue):
            raise TypeError("ShapeRef does not support computed keys; use attribute access")

        if not isinstance(key, str):
            # actually unreachable
            raise TypeError(f"key must be str, `{type(key).__name__}` given")

        if hasattr(self.shape_type, "_slots") and key in self.shape_type._slots:
            slot = self.shape_type._slots[key]
            return slot.create_ref(owner_shape=self.shape_type, parent_ref=self)

        raise KeyError(f"{self.shape_type.__name__} has no slot '{key}'")

    def __getattribute__(self, name: str) -> object:
        """Navigate to nested fields via attribute access.

        Args:
            name: Field name to access

        Returns:
            Ref created by the nested slot

        Raises:
            AttributeError: If field doesn't exist
        """
        passthrough = object.__getattribute__(self, "_PASSTHROUGH_ATTRS")
        if name in passthrough:
            return object.__getattribute__(self, name)

        shape_type: type[Shape] = object.__getattribute__(self, "shape_type")

        if hasattr(shape_type, "_slots") and name in shape_type._slots:
            slot = shape_type._slots[name]
            return slot.create_ref(owner_shape=shape_type, parent_ref=self)

        raise AttributeError(f"{shape_type.__name__} has no slot '{name}'")


class DictRef[K: int | str, V: Value, KeyValueT, ValueValueT](
    MutableMappingRefBase[
        dict[K, V],  # CollectionT
        K,  # KeyT
        V,  # ValueT
        DictType[K, V],  # CollectionValueT
        KeyValueT,  # KeyValueT
        ValueValueT,  # ValueValueT
        MutableMappingView,  # ViewT
        DictItemRef[V, ValueValueT],  # ChildRefT
    ],
    ViewRef,
):
    """Reference to a mapping container.

    Points to dict-like nodes in the tree. Supports subscripting to access items.
    Items can be primitives, shapes, or nested collections.

    Type Parameters:
        K: Native Python key type (str, int)
        V: Native Python value type (int, str, float, etc.)
        KeyValueT: Type type for keys (StrType, IntType)
        ValueValueT: Type type for values (IntType, StrType, etc.)

    Example:
        class Market(Shape):
            signals: DictRef[str, float, StrType, FloatType] = DictSlot(float)
            symbols: DictRef[str, SymbolInfo, StrType, AnyType] = DictSlot(SymbolInfo)

        # Access items
        Market.signals["vix"].get()           # DictItemRef[float, FloatType]
        Market.symbols["AAPL"].price.get()    # ShapeRef navigation
    """

    # Class-level type annotations (set dynamically per instance)
    collection_type: type[dict[K, V]] = dict
    collection_value_type: type[DictType[K, V]] = DictType

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
        """Initialize mapping reference.

        Args:
            address: Address of this field in parent's domain
            value_type: Python type of values
            key_type: Python type of keys
            view_type: View class for this mapping (e.g., DictView)
            key_value_type: Type type for keys
            value_value_type: Type type for values
            parent_ref: Parent reference in navigation chain
            owner_shape: Shape class this ref belongs to
        """
        super().__init__(address, view_type, parent_ref, owner_shape)
        self.value_type = value_type
        self.key_type = key_type
        self.key_value_type = key_value_type
        self.value_value_type = value_value_type

    def result(self, op: RValue) -> DictType[K, V]:
        """Wrap an operation result in a DictType container.

        Args:
            op: The operation to wrap

        Returns:
            DictType wrapping the operation
        """
        return DictType(op)

    def _create_child_ref(
        self, key: K | Sentinel | RValue[K | Sentinel]
    ) -> DictItemRef[V, ValueValueT]:
        """Create a reference to a child at the given key.

        Args:
            key: Child key (literal or RValue[K] for computed key)

        Returns:
            DictItemRef to item at the specified key
        """
        return DictItemRef(
            address=literal(key),
            value_type=self.value_type,
            value_value_type=self.value_value_type,
            parent_ref=self,
            owner_shape=self.owner_shape,
        )


class ListRef[T, ItemValueT](
    MutableSequenceRefBase[
        list[T],  # CollectionT
        T,  # ItemT
        ListType[T],  # CollectionValueT
        ItemValueT,  # ItemValueT
        MutableSequenceView,  # ViewT
        int,  # IndexT
        IntType,  # IndexValueT
        ListType[T],  # SliceValueT
        ListItemRef[T, ItemValueT],  # ItemRefT
        SequenceSliceRef,  # SliceRefT
    ],
    ViewRef,
):
    """Reference to a sequence container.

    Points to list-like nodes in the tree. Supports subscripting to access items.
    Items can be primitives, shapes, or nested collections.

    Type Parameters:
        T: Native Python item type (int, str, float, etc.)
        ItemValueT: Type type for items (IntType, StrType, etc.)

    Example:
        class Market(Shape):
            prices: ListRef[float, FloatType] = ListSlot(float)
            orders: ListRef[Order, AnyType] = ListSlot(Order)

        # Access items
        Market.prices[0].get()              # ListItemRef[float, FloatType]
        Market.orders[0].id.get()           # ShapeRef navigation
    """

    # Class-level type annotations
    collection_type: type[list[T]] = list
    collection_value_type: type[ListType[T]] = ListType
    index_type: type[int] = int
    index_value_type: type[IntType] = IntType

    def __init__(
        self,
        address: path.PathAddress,
        item_type: type[T],
        item_value_type: type[ItemValueT],
        view_type: type[MutableSequenceView],
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize sequence reference.

        Args:
            address: Address of this field in parent's domain
            item_type: Python type of items
            item_value_type: Type type for items
            view_type: View class for this sequence (e.g., ListView)
            parent_ref: Parent reference in navigation chain
            owner_shape: Shape class this ref belongs to
        """
        super().__init__(address, view_type, parent_ref, owner_shape)
        self.item_type = item_type
        self.item_value_type = item_value_type

    def result(self, op: RValue) -> ListType[T]:
        """Wrap an operation result in a ListType container.

        Args:
            op: The operation to wrap

        Returns:
            ListType wrapping the operation
        """
        return ListType(op)

    def _create_item_ref(
        self, index: int | Sentinel | RValue[int | Sentinel]
    ) -> ListItemRef[T, ItemValueT]:
        """Create a reference to an item at the given index.

        Args:
            index: Item index (int or RValue[int] for computed index)

        Returns:
            ListItemRef to item at the specified index
        """
        return ListItemRef(
            address=literal(index),
            value_type=self.item_type,
            value_value_type=self.item_value_type,
            parent_ref=self,
            owner_shape=self.owner_shape,
        )

    def _create_slice_ref(self, key: slice) -> SequenceSliceRef:
        """Create a reference to a slice of the sequence.

        Args:
            key: Slice specification (start:stop:step)

        Returns:
            Reference to the specified slice
        """
        # TODO: Implement slice refs when ready
        raise NotImplementedError("Slice refs not yet implemented")


class ShapesListRef[T: Shape](
    MutableSequenceRefBase[
        list[dict],  # CollectionT
        dict,  # ItemT (shapes serialize to dicts)
        ListType[dict],  # CollectionValueT
        DictType[str, Value],  # ItemValueT (shape items are dicts)
        MutableSequenceView,  # ViewT
        int,  # IndexT
        IntType,  # IndexValueT
        ListType[dict],  # SliceValueT
        T,  # ItemRefT
        SequenceShapeSliceRef,  # SliceRefT
    ],
    ViewRef,
):
    """Reference to a list of homogeneous shapes.

    Points to list-like nodes containing shape instances.
    Supports subscripting to access individual shapes.

    Type Parameters:
        T: The Shape class for items in this list

    Example:
        class Order(Shape):
            id: ItemRef[str, StrType] = ItemSlot(str)
            price: ItemRef[float, FloatType] = ItemSlot(float)

        class Market(Shape):
            orders: ShapesListRef[Order] = ShapesListSlot(Order)

        # Access items
        Market.orders[0].id.get()       # Navigate to shape and its fields
        Market.orders.extract()         # Get list of all order dicts
        Market.orders.append({...})     # Add new order
    """

    # Class-level type annotations
    collection_type: type[list[dict]] = list
    collection_value_type: type[ListType[dict]] = ListType
    item_value_type: type[DictType[str, Value]] = DictType
    index_type: type[int] = int
    index_value_type: type[IntType] = IntType

    def __init__(
        self,
        address: path.PathAddress,
        shape_type: type[T],
        view_type: type[MutableSequenceView],
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize sequence shape reference.

        Args:
            address: Address of this field in parent's domain
            shape_type: Shape class for items
            view_type: View class for this sequence (e.g., ListView)
            parent_ref: Parent reference in navigation chain
            owner_shape: Shape class this ref belongs to
        """
        super().__init__(address, view_type, parent_ref, owner_shape)
        self.shape_type = shape_type
        self.item_type = dict

    def result(self, op: RValue) -> ListType[dict]:
        """Wrap an operation result in a ListType container.

        Args:
            op: The operation to wrap

        Returns:
            ListType wrapping the operation
        """
        return ListType(op)

    def _create_item_ref(self, index: int | Sentinel | RValue[int | Sentinel]) -> ShapeRef[T]:
        """Create a reference to a shape at the given index.

        Args:
            index: Item index (int or RValue[int] for computed index)

        Returns:
            ShapeRef to shape at the specified index
        """
        from everybase.view import DictView

        return ShapeRef(
            address=literal(index),
            shape_type=self.shape_type,
            view_type=DictView,
            parent_ref=self,
            owner_shape=self.owner_shape,
        )

    def _create_slice_ref(self, key: slice) -> SequenceShapeSliceRef:
        """Create a reference to a slice of the sequence.

        Args:
            key: Slice specification (start:stop:step)

        Returns:
            Reference to the specified slice
        """
        # TODO: Implement slice refs when ready
        raise NotImplementedError("Slice refs not yet implemented")


class ShapesDictRef[K: int | str, T: Shape, KeyValueT](
    MutableMappingRefBase[
        dict[K, dict],  # CollectionT
        K,  # KeyT
        dict,  # ValueT (shapes serialize to dicts)
        DictType[K, dict],  # CollectionValueT
        KeyValueT,  # KeyValueT
        DictType[str, Value],  # ValueValueT (shape values are dicts)
        MutableMappingView,  # ViewT
        T,  # ChildRefT
    ],
    ViewRef,
):
    """Reference to a mapping of homogeneous shapes.

    Points to dict-like nodes containing shape instances.
    Supports subscripting to access individual shapes by key.

    Type Parameters:
        K: Native Python key type (str, int)
        T: The Shape class for values in this mapping
        KeyValueT: Type type for keys (StrType, IntType)

    Example:
        class SymbolInfo(Shape):
            price: ItemRef[float, FloatType] = ItemSlot(float)
            volume: ItemRef[int, IntType] = ItemSlot(int)

        class Market(Shape):
            symbols: ShapesDictRef[str, SymbolInfo, StrType] = ShapesDictSlot(SymbolInfo)

        # Access items
        Market.symbols["AAPL"].price.get()   # Navigate to shape and its fields
        Market.symbols.extract()             # Get dict of all symbols
        Market.symbols.store({...})          # Store multiple symbols
    """

    # Class-level type annotations
    collection_type: type[dict[K, dict]] = dict
    collection_value_type: type[DictType[K, dict]] = DictType
    value_value_type: type[DictType[str, Value]] = DictType

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
        """Initialize mapping shape reference.

        Args:
            address: Address of this field in parent's domain
            key_type: Python type of keys
            key_value_type: Type type for keys
            shape_type: Shape class for values
            view_type: View class for this mapping (e.g., DictView)
            parent_ref: Parent reference in navigation chain
            owner_shape: Shape class this ref belongs to
        """
        super().__init__(address, view_type, parent_ref, owner_shape)
        self.value_type = dict
        self.key_type = key_type
        self.key_value_type = key_value_type
        self.shape_type = shape_type

    def result(self, op: RValue) -> DictType[K, dict]:
        """Wrap an operation result in a DictType container.

        Args:
            op: The operation to wrap

        Returns:
            DictType wrapping the operation
        """
        return DictType(op)

    def _create_child_ref(self, key: K | Sentinel | RValue[K | Sentinel]) -> ShapeRef[T]:
        """Create a reference to a shape at the given key.

        Args:
            key: Child key (literal or RValue[K] for computed key)

        Returns:
            ShapeRef to shape at the specified key
        """
        from everybase.view import DictView

        return ShapeRef(
            address=literal(key),
            shape_type=self.shape_type,
            view_type=DictView,
            parent_ref=self,
            owner_shape=self.owner_shape,
        )
