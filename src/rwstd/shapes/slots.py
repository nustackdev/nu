"""Slot definitions - building blocks for Shapes.

Slots are factories that create Refs. They define:
- What type of data lives at a location (value_type)
- How to access it (view_type)
- How to create refs to it (create_ref)

Slots are declarative - they describe structure, not behavior.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .slot import Slot


if TYPE_CHECKING:
    from ..semantics import LValue
    from .shape import Shape


# ============================================================================
# Value Slot - Primitive Values
# ============================================================================


class ValueSlot(Slot):
    """Slot for primitive values (int, float, str, bool, etc.).

    Creates ValueRef when accessed.

    Example:
        class Market(Shape):
            signal = ValueSlot(float)
            volume = ValueSlot(int)

        Market.signal  # → ValueRef
    """

    def __init__(self, value_type: type, view_type: type | None = None) -> None:
        """Initialize value slot.

        Args:
            value_type: Primitive type (int, float, str, bool)
            view_type: View class (defaults to DictView)
        """
        super().__init__(value_type, view_type)

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: LValue | None = None,
    ) -> LValue:
        """Create ValueRef for this slot.

        Args:
            owner_shape: Shape class owning this slot
            parent_ref: Parent ref (for nested access)

        Returns:
            ValueRef pointing to this location
        """
        from ..behavior.refs import ValueRef

        if self.name is None:
            raise ValueError("Slot name not set - should be set by metaclass")

        return ValueRef(
            field_name=self.name,
            value_type=self.value_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
        )


# ============================================================================
# Map Slot - Mapping Containers
# ============================================================================


class MapSlot(Slot):
    """Slot for mapping containers (key → value).

    Creates MapRef when accessed. Items can be any type.

    Example:
        class Market(Shape):
            orders = MapSlot(Order)
            prices = MapSlot(float)

        Market.orders  # → MapRef
        Market.orders["AAPL"]  # → MapItemRef
    """

    def __init__(self, value_type: type, view_type: type | None = None) -> None:
        """Initialize map slot.

        Args:
            value_type: Type of values in the map (Order, float, etc.)
            view_type: View class (defaults to DictView)
        """
        super().__init__(value_type, view_type)

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: LValue | None = None,
    ) -> LValue:
        """Create MapRef for this slot.

        Args:
            owner_shape: Shape class owning this slot
            parent_ref: Parent ref (for nested access)

        Returns:
            MapRef pointing to this mapping
        """
        from ..behavior.refs import MapRef

        if self.name is None:
            raise ValueError("Slot name not set - should be set by metaclass")

        return MapRef(
            field_name=self.name,
            value_type=self.value_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
        )


# ============================================================================
# Shape Slot - Nested Shapes
# ============================================================================


class ShapeSlot(Slot):
    """Slot for nested Shape instances.

    Creates ShapeRef when accessed, which allows navigation to
    nested fields.

    Example:
        class Profile(Shape):
            email = ValueSlot(str)
            age = ValueSlot(int)

        class User(Shape):
            name = ValueSlot(str)
            profile = ShapeSlot(Profile)

        User.profile  # → ShapeRef
        User.profile.email  # → Navigate through ShapeRef to ValueRef
    """

    def __init__(self, shape_type: type[Shape], view_type: type | None = None) -> None:
        """Initialize shape slot.

        Args:
            shape_type: Shape class for nested structure
            view_type: View class (defaults to DictView)
        """
        super().__init__(shape_type, view_type)
        self.shape_type = shape_type

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: LValue | None = None,
    ) -> LValue:
        """Create ShapeRef for this slot.

        Args:
            owner_shape: Shape class owning this slot
            parent_ref: Parent ref (for nested access)

        Returns:
            ShapeRef pointing to nested shape
        """
        from ..behavior.refs import ShapeRef

        if self.name is None:
            raise ValueError("Slot name not set - should be set by metaclass")

        return ShapeRef(
            field_name=self.name,
            shape_type=self.shape_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
        )


__all__ = [
    "MapSlot",
    "ShapeSlot",
    "Slot",
    "ValueSlot",
]
