"""Reference implementations for Shape system.

This module provides concrete Ref types that work with the View layer:
- ValueRef: references to primitive values
- ShapeRef: references to nested structures

These build on the contracts in term.py and integrate with the Path
navigation system from redwood.loc.path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from redwood.shape import Ref


if TYPE_CHECKING:
    from redwood.loc import path
    from redwood.shape import Context, RValue, Shape

    from .commands import SetCmd, StoreCmd
    from .operations import ExtractOp, GetOp


__all__ = [
    "ShapeRef",
    "ValueRef",
]


# =============================================================================
# VALUE REFERENCE
# =============================================================================


class ValueRef[T](Ref[T]):
    """Reference to a primitive value location.

    Points to leaf nodes in the tree: int, str, float, bool, etc.
    Supports read (get) and write (set) operations.

    Example:
        class User(Shape):
            name: ValueRef[str] = ValueSlot(str)
            age: ValueRef[int] = ValueSlot(int)

        # Create operations
        User.name.get()         # GetOp[str]
        User.name.set("Alice")  # SetCmd[str]
    """

    def __init__(
        self,
        field_name: path.PathAddress,
        value_type: type[T],
        view_type: type,
        parent_ref: Ref | None = None,
    ) -> None:
        """Initialize value reference.

        Args:
            field_name: Address of this field in parent's domain
            value_type: Python type of the value (int, str, etc.)
            view_type: View class for parent container
            parent_ref: Parent reference in navigation chain
        """
        self.field_name = field_name
        self.value_type = value_type
        self.view_type = view_type
        self.parent_ref = parent_ref

    def resolve(self, context: Context) -> path.Path:
        """Resolve to complete path ending at value.

        Args:
            context: Execution context

        Returns:
            Path ending with value segment
        """
        if self.parent_ref is None:
            return ((self.field_name, self.value_type),)  # type: ignore[return-value]

        parent_path = self.parent_ref.resolve(context)
        return (*parent_path, (self.field_name, self.value_type))  # type: ignore[return-value]

    def parent(self) -> Ref | None:
        """Get parent reference."""
        return self.parent_ref

    def get(self) -> GetOp[T]:
        """Create read operation."""
        from .operations import GetOp

        return GetOp(self)

    def set(self, value: T | RValue[T]) -> SetCmd[T]:
        """Create write command."""
        from .commands import SetCmd

        return SetCmd(self, value)

    def __repr__(self) -> str:
        if self.parent_ref:
            return f"{self.parent_ref!r}.{self.field_name}"
        return str(self.field_name)


# =============================================================================
# SHAPE REFERENCE
# =============================================================================


class ShapeRef[T](Ref[T]):
    """Reference to a nested shape location.

    Points to container nodes with structure defined by a Shape.
    Supports navigation to nested fields via attribute access.

    Example:
        class Profile(Shape):
            email: ValueRef[str] = ValueSlot(str)

        class User(Shape):
            profile: ShapeRef[Profile] = ShapeSlot(Profile)

        # Navigate to nested field
        User.profile.email  # Returns ValueRef[str]
    """

    def __init__(
        self,
        field_name: path.PathAddress,
        shape_type: type[Shape],
        view_type: type,
        parent_ref: Ref | None = None,
    ) -> None:
        """Initialize shape reference.

        Args:
            field_name: Address of this field in parent's domain
            shape_type: Shape class defining structure
            view_type: View class for this container
            parent_ref: Parent reference in navigation chain
        """
        self.field_name = field_name
        self.shape_type = shape_type
        self.value_type = shape_type
        self.view_type = view_type
        self.parent_ref = parent_ref

    def resolve(self, context: Context) -> path.Path:
        """Resolve to path ending at this shape's view.

        Args:
            context: Execution context

        Returns:
            Path ending with view segment
        """
        if self.parent_ref is None:
            return ()

        parent_path = self.parent_ref.resolve(context)
        return (*parent_path, (self.field_name, self.view_type))  # type: ignore[return-value]

    def parent(self) -> Ref | None:
        """Get parent reference."""
        return self.parent_ref

    def __getattribute__(self, name: str) -> object:
        """Navigate to nested fields via attribute access.

        Args:
            name: Field name to access

        Returns:
            Ref created by the nested slot

        Raises:
            AttributeError: If field doesn't exist
        """
        if name in {
            "field_name",
            "shape_type",
            "value_type",
            "view_type",
            "parent_ref",
            "resolve",
            "execute",
            "parent",
            "extract",
            "store",
        }:
            return object.__getattribute__(self, name)

        shape_type: type[Shape] = object.__getattribute__(self, "shape_type")

        if hasattr(shape_type, "_slots") and name in shape_type._slots:
            slot = shape_type._slots[name]
            return slot.create_ref(owner_shape=shape_type, parent_ref=self)

        raise AttributeError(f"{shape_type.__name__} has no slot '{name}'")

    def __repr__(self) -> str:
        if self.parent_ref:
            return f"{self.parent_ref!r}.{self.field_name}"
        return str(self.field_name)

    def extract(self) -> ExtractOp[T]:
        """Create extract operation.

        Returns:
            ExtractOp that reads entire structure
        """
        from .operations import ExtractOp

        return ExtractOp(self)

    def store(self, data: T | RValue[T]) -> StoreCmd[T]:
        """Create store command.

        Args:
            data: Dictionary to store, or RValue producing dict

        Returns:
            StoreCmd that writes entire structure
        """
        from .commands import StoreCmd

        return StoreCmd(self, data)
