"""Slot implementations for Shape system.

This module provides concrete slot types that create refs:
- ValueSlot: creates ValueRef for primitive values
- ShapeSlot: creates ShapeRef for nested structures
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyshape.shape import Slot


if TYPE_CHECKING:
    from everyshape.shape import Ref, Shape
    from everyshape.types import MutableMapping, MutableSequence, Value

    from .refs import MappingRef, MappingShapeRef, SequenceRef, SequenceShapeRef, ShapeRef, ValueRef


__all__ = [
    "MappingShapeSlot",
    "MappingSlot",
    "PrimitiveSlot",
    "SequenceShapeSlot",
    "SequenceSlot",
    "ShapeSlot",
]


# =============================================================================
# VALUE SLOT
# =============================================================================


class _PrimitiveSlot(Slot):
    """Internal slot implementation for primitive values."""

    def __init__(self, value_type: type[Value]) -> None:
        super().__init__()
        self.value_type = value_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> ValueRef:
        """Create ValueRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            ValueRef instance
        """
        from .refs import ValueRef

        return ValueRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
        )


def PrimitiveSlot[V: Value](value_type: type[V]) -> ValueRef[V]:  # noqa: N802
    """Create a value slot for primitive types.

    Factory function that returns a slot instance.

    Args:
        value_type: Python type of the value (int, str, float, etc.)

    Returns:
        Slot instance

    Example:
        class User(Shape):
            name: ValueRef[str] = ValueSlot(str)
            age: ValueRef[int] = ValueSlot(int)
            balance: ValueRef[float] = ValueSlot(float)
    """
    return _PrimitiveSlot(value_type=value_type)  # type: ignore


# =============================================================================
# SHAPE SLOT
# =============================================================================


class _ShapeSlot(Slot):
    """Internal slot implementation for nested shapes."""

    def __init__(self, shape_type: type[Shape], view_type: type[MutableMapping]) -> None:
        super().__init__()
        self.shape_type = shape_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> ShapeRef:
        """Create ShapeRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            ShapeRef instance
        """
        from .refs import ShapeRef

        return ShapeRef(
            address=self.name,
            shape_type=self.shape_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
        )


def ShapeSlot[S: Shape](shape_type: type[S], view_type: type[MutableMapping] | None = None) -> S:  # noqa: N802
    """Create a shape slot for nested shapes.

    Factory function that returns a slot instance.

    Args:
        shape_type: Shape class for the nested structure
        view_type: Optional view type (defaults to DictView)

    Returns:
        Slot instance

    Example:
        class Profile(Shape):
            email: ValueRef[str] = ValueSlot(str)

        class User(Shape):
            profile: Profile = ShapeSlot(Profile)

        # Navigate to nested field
        User.profile.email  # Returns ValueRef[str]
    """
    from esstd.collections.views import DictView

    return _ShapeSlot(shape_type=shape_type, view_type=view_type or DictView)  # type: ignore


# =============================================================================
# MAPPING SLOT
# =============================================================================


class _MappingSlot(Slot):
    """Internal slot implementation for mapping collections."""

    def __init__(self, value_type: type, view_type: type[MutableMapping]) -> None:
        super().__init__()
        self.value_type = value_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> MappingRef:
        """Create MappingRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            MappingRef instance
        """
        from .refs import MappingRef

        return MappingRef(
            address=self.name,
            value_type=self.value_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
        )


def MappingSlot[V: Value, M: MutableMapping](  # noqa: N802
    value_type: type[V], view_type: type[M] | None = None
) -> MappingRef[str | int, V]:
    """Create a mapping slot for dict-like collections.

    Factory function that returns a slot instance.

    Args:
        value_type: Python type of values (primitives, Shapes, or CollectionDescriptor)
        view_type: Optional view type implementing MutableMapping protocol (defaults to DictView)

    Returns:
        Slot instance

    Example:
        from esstd.shapes import MappingSlot, Sequence

        class Market(Shape):
            # Mapping of primitives
            signals: MappingRef[float] = MappingSlot(float)

            # Mapping of shapes
            symbols: MappingRef[SymbolInfo] = MappingSlot(SymbolInfo)

            # Nested: mapping of sequences
            data: MappingRef = MappingSlot(Sequence(float))

        # Access items
        Market.signals["vix"].get()           # ValueRef[float]
        Market.symbols["AAPL"].price.get()    # ShapeRef navigation
        Market.data["timeseries"][0].get()    # Nested collection

    Note:
        The view_type must structurally implement the MutableMapping protocol
        from everyshape.types.collections.
    """
    from esstd.collections.views import DictView

    return _MappingSlot(value_type=value_type, view_type=view_type or DictView)  # type: ignore


# =============================================================================
# SEQUENCE SLOT
# =============================================================================


class _SequenceSlot(Slot):
    """Internal slot implementation for sequence collections."""

    def __init__(self, item_type: type, view_type: type[MutableSequence]) -> None:
        super().__init__()
        self.item_type = item_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> SequenceRef:
        """Create SequenceRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            SequenceRef instance
        """
        from .refs import SequenceRef

        return SequenceRef(
            address=self.name,
            item_type=self.item_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
        )


def SequenceSlot[V: Value, S: MutableSequence](  # noqa: N802
    item_type: type[V], view_type: type[S] | None = None
) -> SequenceRef[V]:
    """Create a sequence slot for list-like collections.

    Factory function that returns a slot instance.

    Args:
        item_type: Python type of values (primitives, Shapes, or CollectionDescriptor)
        view_type: Optional view type implementing MutableSequence protocol (defaults to ListView)

    Returns:
        Slot instance

    Example:
        from esstd.shapes import SequenceSlot, Mapping

        class Market(Shape):
            # Sequence of primitives
            prices: SequenceRef[float] = SequenceSlot(float)

            # Sequence of shapes
            orders: SequenceRef[Order] = SequenceSlot(Order)

            # Nested: sequence of mappings
            data: SequenceRef = SequenceSlot(Mapping(str))

        # Access items
        Market.prices[0].get()              # ValueRef[float]
        Market.orders[0].id.get()           # ShapeRef navigation
        Market.data[0]["key"].get()         # Nested collection

    Note:
        The view_type must structurally implement the MutableSequence protocol
        from everyshape.types.collections.
    """
    from esstd.collections.views import ListView

    return _SequenceSlot(item_type=item_type, view_type=view_type or ListView)  # type: ignore


# =============================================================================
# SEQUENCE SHAPE SLOT
# =============================================================================


class _SequenceShapeSlot(Slot):
    """Internal slot implementation for sequence of shapes."""

    def __init__(self, shape_type: type[Shape], view_type: type[MutableSequence]) -> None:
        super().__init__()
        self.shape_type = shape_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> SequenceShapeRef:
        """Create SequenceShapeRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            SequenceShapeRef instance
        """
        from .refs import SequenceShapeRef

        return SequenceShapeRef(
            address=self.name,
            shape_type=self.shape_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
        )


def SequenceShapeSlot[S: Shape, SeqT: MutableSequence](  # noqa: N802
    shape_type: type[S], view_type: type[SeqT] | None = None
) -> SequenceShapeRef[S]:
    """Create a sequence slot for list-like collections of shapes.

    Factory function that returns a slot instance for homogeneous shape collections.

    Args:
        shape_type: Shape class for items in the sequence
        view_type: Optional view type implementing MutableSequence protocol (defaults to ListView)

    Returns:
        Slot instance

    Example:
        class Order(Shape):
            id: ValueRef[str] = PrimitiveSlot(str)
            price: ValueRef[float] = PrimitiveSlot(float)
            quantity: ValueRef[int] = PrimitiveSlot(int)

        class Market(Shape):
            # Sequence of Order shapes
            orders: SequenceShapeRef[Order] = SequenceShapeSlot(Order)

        # Access items and navigate to their fields
        Market.orders[0].id.get()           # Get order ID
        Market.orders[0].price.set(100.5)   # Set order price
        Market.orders.extract()             # Get list of all order dicts
        Market.orders.append({"id": "123", "price": 99.0, "quantity": 10})

    Note:
        The view_type must structurally implement the MutableSequence protocol
        from everyshape.types.collections.
    """
    from esstd.collections.views import ListView

    return _SequenceShapeSlot(shape_type=shape_type, view_type=view_type or ListView)  # type: ignore


# =============================================================================
# MAPPING SHAPE SLOT
# =============================================================================


class _MappingShapeSlot(Slot):
    """Internal slot implementation for mapping of shapes."""

    def __init__(self, shape_type: type[Shape], view_type: type[MutableMapping]) -> None:
        super().__init__()
        self.shape_type = shape_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> MappingShapeRef:
        """Create MappingShapeRef for this slot.

        Args:
            owner_shape: Shape class this slot belongs to
            parent_ref: Parent reference for nested access

        Returns:
            MappingShapeRef instance
        """
        from .refs import MappingShapeRef

        return MappingShapeRef(
            address=self.name,
            shape_type=self.shape_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
        )


def MappingShapeSlot[S: Shape, M: MutableMapping](  # noqa: N802
    shape_type: type[S], view_type: type[M] | None = None
) -> MappingShapeRef[str | int, S]:
    """Create a mapping slot for dict-like collections of shapes.

    Factory function that returns a slot instance for homogeneous shape collections.

    Args:
        shape_type: Shape class for values in the mapping
        view_type: Optional view type implementing MutableMapping protocol (defaults to DictView)

    Returns:
        Slot instance

    Example:
        class SymbolInfo(Shape):
            price: ValueRef[float] = PrimitiveSlot(float)
            volume: ValueRef[int] = PrimitiveSlot(int)
            exchange: ValueRef[str] = PrimitiveSlot(str)

        class Market(Shape):
            # Mapping of symbol name to SymbolInfo
            symbols: MappingShapeRef[str, SymbolInfo] = MappingShapeSlot(SymbolInfo)

        # Access items and navigate to their fields
        Market.symbols["AAPL"].price.get()           # Get AAPL price
        Market.symbols["AAPL"].volume.set(1000000)   # Set AAPL volume
        Market.symbols.extract()                     # Get dict of all symbols
        Market.symbols.store({"AAPL": {"price": 150.0, "volume": 1000000, "exchange": "NASDAQ"}})

    Note:
        The view_type must structurally implement the MutableMapping protocol
        from everyshape.types.collections.
    """
    from esstd.collections.views import DictView

    return _MappingShapeSlot(shape_type=shape_type, view_type=view_type or DictView)  # type: ignore
