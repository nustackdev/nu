"""Slot implementations for Shape system.

This module provides concrete slot types that create refs:
- ItemSlot: creates ItemRef for primitive values
- DictSlot: creates PVDictRef for dict-like collections
- ListSlot: creates PVListRef for list-like collections
- ShapesListSlot: creates ShapesListRef for lists of shapes
- ShapesDictSlot: creates ShapesDictRef for dicts of shapes
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from every_pv.collections import PVDictRef, PVListRef, PVShapeRef, PVShapesDictRef, PVShapesListRef
from every_pv.primitives import PVItemRef
from everyabc import Slot, Value
from everybase import (
    AnyValue,
    BoolValue,
    BytesValue,
    DictValue,
    FloatValue,
    IntValue,
    ListValue,
    SetValue,
    StrValue,
)


if TYPE_CHECKING:
    from pv.collections import MutableMappingView, MutableSequenceView
    from pv.types import Value as StorageValue

    from every_pv.shape import PVShape
    from everyabc import Ref
    from everybase import AnyValue, IntValue, StrValue  # noqa: TC004


def _value_type_for(python_type: type) -> type[Ref]:
    """Map Python type to its corresponding Value type.

    Args:
        python_type: Native Python type (int, str, float, etc.)

    Returns:
        Corresponding Value type (IntValue, StrValue, etc.)
    """
    mapping: dict[type, type[Value]] = {
        int: IntValue,
        str: StrValue,
        float: FloatValue,
        bool: BoolValue,
        bytes: BytesValue,
        list: ListValue,
        dict: DictValue,
        set: SetValue,
    }
    return mapping.get(python_type, AnyValue)


__all__ = [
    "BoolSlot",
    "BytesSlot",
    "DictSlot",
    "FloatSlot",
    # Primitive type slot aliases
    "IntSlot",
    "ItemSlot",
    "ListSlot",
    "ShapeSlot",
    "ShapesDictSlot",
    "ShapesListSlot",
    "StrSlot",
]


class _ItemSlot(Slot):
    """Create a value slot for primitive types.

    Args:
        value_type: Python type of the value (int, str, float, etc.)

    Example:
        class User(Shape):
            name: ItemRef[str, StrValue] = ItemSlot(str)
            age: ItemRef[int, IntValue] = ItemSlot(int)
            balance: ItemRef[float, FloatValue] = ItemSlot(float)
    """

    def __init__(self, value_type: type[StorageValue], value_value_type: type[Ref]) -> None:
        """Initialize value slot.

        Args:
            value_type: Python type for the primitive value
            value_value_type: Ref for the value's type
        """
        super().__init__()
        self.value_type = value_type
        self.value_value_type = value_value_type

    def create_ref(
        self,
        owner_shape: type[PVShape],
        parent_ref: Ref | None = None,
    ) -> PVItemRef:
        """Create ItemRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            ItemRef instance
        """
        return PVItemRef(
            address=self.name,
            value_type=self.value_type,
            value_value_type=self.value_value_type,
            parent=parent_ref,
            shape=owner_shape,
        )


def ItemSlot[V: StorageValue, VV: Ref](  # noqa: N802
    value_type: type[V], value_value_type: type[VV]
) -> PVItemRef[V, VV]:
    """Create a value slot for primitive types.

    Factory function that returns a slot instance.

    Args:
        value_type: Python type of the value (int, str, float, etc.)
        value_value_type: Ref for the value's type

    Returns:
        Slot instance

    Example:
        class User(Shape):
            name: ValueRef[str] = ValueSlot(str)
            age: ValueRef[int] = ValueSlot(int)
            balance: ValueRef[float] = ValueSlot(float)
    """
    return _ItemSlot(value_type=value_type, value_value_type=value_value_type)  # type: ignore


class _DictSlot(Slot):
    """Create a mapping slot for dict-like collections of primitives.

    Args:
        value_type: Python type of values (primitives)
        key_type: Python type of keys (default: str)
        view_type: View class implementing MutableMappingView protocol

    Example:
        class Market(Shape):
            # Mapping of primitives
            signals: PVDictRef[str, float, StrValue, FloatValue] = DictSlot(float)

        # Access items
        Market.signals["vix"].get()  # PVDictItemRef[float, FloatValue]
    """

    def __init__(
        self,
        value_type: type[StorageValue],
        view_type: type[MutableMappingView] | None = None,
        key_type: type[int | str] = str,
    ) -> None:
        """Initialize dict slot.

        Args:
            value_type: Python type for values
            view_type: View class for this mapping
            key_type: Python type for keys (default: str)
        """
        super().__init__()
        self.value_type = value_type
        self.view_type = view_type
        self.key_type = key_type
        self.key_value_type = _value_type_for(key_type)
        self.value_value_type = _value_type_for(value_type)

    def create_ref(
        self,
        owner_shape: type[PVShape],
        parent_ref: Ref | None = None,
    ) -> PVDictRef:
        """Create PVDictRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            PVDictRef instance
        """
        from every_view import DictView

        return PVDictRef(
            address=self.name,
            value_type=self.value_type,
            key_type=self.key_type,
            view_type=self.view_type or DictView,
            key_value_type=self.key_value_type,
            value_value_type=self.value_value_type,
            parent=parent_ref,
            shape=owner_shape,
        )


def DictSlot[K: int | str, V: StorageValue](  # noqa: N802
    value_type: type[V],
    view_type: type[MutableMappingView] | None = None,
    key_type: type[K] = str,
) -> PVDictRef[K, V, AnyValue, AnyValue]:
    """Create a mapping slot for dict-like collections of primitives.

    Factory function that returns a slot instance.

    Args:
        value_type: Python type of values (primitives)
        view_type: View class implementing MutableMappingView protocol
        key_type: Python type of keys (default: str)

    Returns:
        Slot instance

    Example:
        class Market(Shape):
            signals: PVDictRef[str, float] = DictSlot(float)
    """
    return _DictSlot(value_type=value_type, view_type=view_type, key_type=key_type)  # type: ignore


class _ListSlot(Slot):
    """Create a sequence slot for list-like collections of primitives.

    Args:
        item_type: Python type of items (primitives)
        view_type: View class implementing MutableSequenceView protocol

    Example:
        class Market(Shape):
            prices: PVListRef[float, FloatValue] = ListSlot(float)

        # Access items
        Market.prices[0].get()  # PVListItemRef[float, FloatValue]
    """

    def __init__(
        self,
        item_type: type[StorageValue],
        view_type: type[MutableSequenceView] | None = None,
    ) -> None:
        """Initialize list slot.

        Args:
            item_type: Python type for items
            view_type: View class for this sequence
        """
        super().__init__()
        self.item_type = item_type
        self.view_type = view_type
        self.item_value_type = _value_type_for(item_type)

    def create_ref(
        self,
        owner_shape: type[PVShape],
        parent_ref: Ref | None = None,
    ) -> PVListRef:
        """Create PVListRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            PVListRef instance
        """
        from every_view import ListView

        return PVListRef(
            address=self.name,
            item_type=self.item_type,
            item_value_type=self.item_value_type,
            view_type=self.view_type or ListView,
            parent=parent_ref,
            shape=owner_shape,
        )


def ListSlot[V: StorageValue](  # noqa: N802
    item_type: type[V],
    view_type: type[MutableSequenceView] | None = None,
) -> PVListRef[V, AnyValue]:
    """Create a sequence slot for list-like collections of primitives.

    Factory function that returns a slot instance.

    Args:
        item_type: Python type of items (primitives)
        view_type: View class implementing MutableSequenceView protocol

    Returns:
        Slot instance

    Example:
        class Market(Shape):
            prices: PVListRef[float] = ListSlot(float)
    """
    return _ListSlot(item_type=item_type, view_type=view_type)  # type: ignore


class _ShapeSlot(Slot):
    """Create a slot for nested shapes.

    Args:
        shape_type: Shape class for the nested structure
        view_type: View class implementing MutableMappingView protocol

    Example:
        class Profile(Shape):
            email: ItemRef[str] = ItemSlot(str)

        class User(Shape):
            profile: ShapeRef[Profile] = ShapeSlot(Profile)

        # Navigate to nested field
        User.profile.email.get()  # Returns ItemRef[str]
    """

    def __init__(
        self,
        shape_type: type[PVShape],
        view_type: type[MutableMappingView] | None = None,
    ) -> None:
        """Initialize shape slot.

        Args:
            shape_type: Shape class for the nested structure
            view_type: View class for this container
        """
        super().__init__()
        self.shape_type = shape_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[PVShape],
        parent_ref: Ref | None = None,
    ) -> PVShapeRef:
        """Create ShapeRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            ShapeRef instance
        """
        from every_view import DictView

        return PVShapeRef(
            address=self.name,
            shape_type=self.shape_type,
            view_type=self.view_type or DictView,
            parent=parent_ref,
            shape=owner_shape,
        )


def ShapeSlot[S: PVShape](  # noqa: N802
    shape_type: type[S],
    view_type: type[MutableMappingView] | None = None,
) -> S:
    """Create a slot for nested shapes.

    Factory function that returns a slot instance.

    Args:
        shape_type: Shape class for the nested structure
        view_type: View class implementing MutableMappingView protocol

    Returns:
        Slot instance

    Example:
        class User(Shape):
            profile: ShapeRef[Profile] = ShapeSlot(Profile)
    """
    return _ShapeSlot(shape_type=shape_type, view_type=view_type)  # type: ignore


class _ShapesListSlot(Slot):
    """Create a sequence slot for lists of shapes.

    Args:
        shape_type: Shape class for items
        view_type: View class implementing MutableSequenceView protocol

    Example:
        class Order(Shape):
            id: ItemSlot[str] = ItemSlot(str)
            price: ItemSlot[float] = ItemSlot(float)

        class Market(Shape):
            orders: ShapesListRef[Order] = ShapesListSlot(Order)

        # Access items
        Market.orders[0].id.get()  # Navigate to shape fields
    """

    def __init__(
        self,
        shape_type: type[PVShape],
        view_type: type[MutableSequenceView] | None = None,
    ) -> None:
        """Initialize shapes list slot.

        Args:
            shape_type: Shape class for items
            view_type: View class for this sequence
        """
        super().__init__()
        self.shape_type = shape_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[PVShape],
        parent_ref: Ref | None = None,
    ) -> PVShapesListRef:
        """Create ShapesListRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            ShapesListRef instance
        """
        from every_view import ListView

        return PVShapesListRef(
            address=self.name,
            shape_type=self.shape_type,
            view_type=self.view_type or ListView,
            parent=parent_ref,
            shape=owner_shape,
        )


def ShapesListSlot[S: PVShape](  # noqa: N802
    shape_type: type[S],
    view_type: type[MutableSequenceView] | None = None,
) -> PVShapesListRef[S]:
    """Create a sequence slot for lists of shapes.

    Factory function that returns a slot instance.

    Args:
        shape_type: Shape class for items
        view_type: View class implementing MutableSequenceView protocol

    Returns:
        Slot instance

    Example:
        class Market(Shape):
            orders: ShapesListRef[Order] = ShapesListSlot(Order)
    """
    return _ShapesListSlot(shape_type=shape_type, view_type=view_type)  # type: ignore


class _ShapesDictSlot(Slot):
    """Create a mapping slot for dicts of shapes.

    Args:
        shape_type: Shape class for values
        key_type: Python type for keys (default: str)
        view_type: View class implementing MutableMappingView protocol

    Example:
        class SymbolInfo(Shape):
            price: ItemRef[float, FloatValue] = ItemSlot(float)
            volume: ItemRef[int, IntValue] = ItemSlot(int)

        class Market(Shape):
            symbols: ShapesDictRef[str, SymbolInfo, StrValue] = ShapesDictSlot(SymbolInfo)

        # Access items
        Market.symbols["AAPL"].price.get()  # Navigate to shape fields
    """

    def __init__(
        self,
        shape_type: type[PVShape],
        view_type: type[MutableMappingView] | None = None,
        key_type: type[int | str] = str,
    ) -> None:
        """Initialize shapes dict slot.

        Args:
            shape_type: Shape class for values
            view_type: View class for this mapping
            key_type: Python type for keys (default: str)
        """
        super().__init__()
        self.shape_type = shape_type
        self.view_type = view_type
        self.key_type = key_type
        self.key_value_type = _value_type_for(key_type)

    def create_ref(
        self,
        owner_shape: type[PVShape],
        parent_ref: Ref | None = None,
    ) -> PVShapesDictRef:
        """Create ShapesDictRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            ShapesDictRef instance
        """
        from every_view import DictView

        return PVShapesDictRef(
            address=self.name,
            key_type=self.key_type,
            key_value_type=self.key_value_type,
            shape_type=self.shape_type,
            view_type=self.view_type or DictView,
            parent=parent_ref,
            shape=owner_shape,
        )


def ShapesDictSlot[K: (int, str), S: PVShape](  # noqa: N802
    shape_type: type[S],
    view_type: type[MutableMappingView] | None = None,
    key_type: type[K] = str,
) -> PVShapesDictRef[K, S, AnyValue]:
    """Create a mapping slot for dicts of shapes.

    Factory function that returns a slot instance.

    Args:
        shape_type: Shape class for values
        view_type: View class implementing MutableMappingView protocol
        key_type: Python type for keys (default: str)

    Returns:
        Slot instance

    Example:
        class Market(Shape):
            symbols: ShapesDictRef[str, SymbolInfo] = ShapesDictSlot(SymbolInfo)
    """
    return _ShapesDictSlot(shape_type=shape_type, view_type=view_type, key_type=key_type)  # type: ignore


# =====================================================================
# Convenience Functions for Primitive Ref Slots
# =====================================================================


def IntSlot() -> PVItemRef[int, IntValue]:  # noqa: N802
    """Create a slot for int values."""
    return ItemSlot(int, IntValue)  # type: ignore


def StrSlot() -> PVItemRef[str, StrValue]:  # noqa: N802
    """Create a slot for str values."""
    return ItemSlot(str, StrValue)  # type: ignore


def FloatSlot() -> PVItemRef[float, FloatValue]:  # noqa: N802
    """Create a slot for float values."""
    return ItemSlot(float, FloatValue)  # type: ignore


def BoolSlot() -> PVItemRef[bool, BoolValue]:  # noqa: N802
    """Create a slot for bool values."""
    return ItemSlot(bool, BoolValue)  # type: ignore


def BytesSlot() -> PVItemRef[bytes, BytesValue]:  # noqa: N802
    """Create a slot for bytes values."""
    return ItemSlot(bytes, BytesValue)  # type: ignore
