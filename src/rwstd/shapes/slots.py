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

    from .refs import ShapeRef, ValueRef


__all__ = [
    "ShapeSlot",
    "ValueSlot",
]


# =============================================================================
# VALUE SLOT
# =============================================================================


class _ValueSlot(Slot):
    """Internal slot implementation for primitive values."""

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
            field_name=self.name,
            value_type=self.value_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
        )


def ValueSlot(value_type: type, view_type: type | None = None) -> Any:
    """Create a value slot for primitive types.

    Factory function that returns a slot instance.

    Args:
        value_type: Python type of the value (int, str, float, etc.)
        view_type: Optional view type (defaults to DictView)

    Returns:
        Slot instance

    Example:
        class User(Shape):
            name: ValueRef[str] = ValueSlot(str)
            age: ValueRef[int] = ValueSlot(int)
            balance: ValueRef[float] = ValueSlot(float)
    """
    from rwstd.views import DictView

    return _ValueSlot(value_type=value_type, view_type=view_type or DictView)


# =============================================================================
# SHAPE SLOT
# =============================================================================


class _ShapeSlot(Slot):
    """Internal slot implementation for nested shapes."""

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
            field_name=self.name,
            shape_type=self.value_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
        )


def ShapeSlot(shape_type: type[Shape], view_type: type | None = None) -> Any:
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
    from rwstd.views import DictView

    return _ShapeSlot(value_type=shape_type, view_type=view_type or DictView)
