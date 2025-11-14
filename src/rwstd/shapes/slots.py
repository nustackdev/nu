"""Slot implementations for Shape system.

This module provides concrete slot types that create refs:
- ValueSlot: creates ValueRef for primitive values
- ShapeSlot: creates ShapeRef for nested structures
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from redwood.shape import Slot


if TYPE_CHECKING:
    from redwood.shape import LValue, Shape
    from redwood.types import Value
    from redwood.view import View

    from .refs import MappingRef, SequenceRef, ShapeRef, ValueRef


__all__ = [
    "MappingSlot",
    "PrimitiveSlot",
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
        parent_ref: LValue | None = None,
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


def PrimitiveSlot(value_type: type[Value]) -> Any:  # noqa: ANN401, N802
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
    return _PrimitiveSlot(value_type=value_type)


# =============================================================================
# SHAPE SLOT
# =============================================================================


class _ShapeSlot(Slot):
    """Internal slot implementation for nested shapes."""

    def __init__(self, shape_type: type[Shape], view_type: type[View]) -> None:
        super().__init__()
        self.shape_type = shape_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: LValue | None = None,
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


def ShapeSlot(shape_type: type[Shape], view_type: type[View] | None = None) -> Any:  # noqa: ANN401, N802
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
    from rwstd.collections.views import DictView

    return _ShapeSlot(shape_type=shape_type, view_type=view_type or DictView)


# =============================================================================
# MAPPING SLOT
# =============================================================================


class _MappingSlot(Slot):
    """Internal slot implementation for mapping collections."""

    def __init__(self, value_type: type, view_type: type[View]) -> None:
        super().__init__()
        self.value_type = value_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: LValue | None = None,
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


def MappingSlot(value_type: type, view_type: type | None = None) -> Any:  # noqa: ANN401, N802
    """Create a mapping slot for dict-like collections.

    Factory function that returns a slot instance.

    Args:
        value_type: Python type of values (primitives, Shapes, or CollectionDescriptor)
        view_type: Optional view type (defaults to DictView)

    Returns:
        Slot instance

    Example:
        from rwstd.shapes import MappingSlot, Sequence

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
    """
    from rwstd.collections.views import DictView

    return _MappingSlot(value_type=value_type, view_type=view_type or DictView)


# =============================================================================
# SEQUENCE SLOT
# =============================================================================


class _SequenceSlot(Slot):
    """Internal slot implementation for sequence collections."""

    def __init__(self, item_type: type, view_type: type[View]) -> None:
        super().__init__()
        self.item_type = item_type
        self.view_type = view_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: LValue | None = None,
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


def SequenceSlot(item_type: type, view_type: type | None = None) -> Any:  # noqa: ANN401, N802
    """Create a sequence slot for list-like collections.

    Factory function that returns a slot instance.

    Args:
        item_type: Python type of values (primitives, Shapes, or CollectionDescriptor)
        view_type: Optional view type (defaults to ListView)

    Returns:
        Slot instance

    Example:
        from rwstd.shapes import SequenceSlot, Mapping

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
    """
    from rwstd.collections.views import ListView

    return _SequenceSlot(item_type=item_type, view_type=view_type or ListView)
