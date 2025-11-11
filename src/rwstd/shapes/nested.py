"""Field references - primitives and nested shapes.

This module provides references for:
- Primitive values (ValueRef via ValueSlot)
- Nested shapes (ShapeRef via ShapeSlot)

These are the building blocks for declarative shape definitions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from redwood.shape import Command, LValue, Operation, Ref, Slot
from redwood.view import navigate_value


if TYPE_CHECKING:
    from redwood.abc import KeyComponent
    from redwood.shape import Context, Shape
    from redwood.view import ValuePath, View, ViewPath


__all__ = [
    "GetOp",
    "SetCmd",
    "ShapeRef",
    "ShapeSlot",
    "ValueRef",
    "ValueSlot",
]


# =============================================================================
# VALUE REFERENCES
# =============================================================================


class ValueRef[T](Ref[T]):
    """Reference to a primitive value.

    Represents an addressable location containing a primitive value
    (int, str, float, bool, etc.). Supports read and write operations.

    Example:
        class User(Shape):
            name: ValueRef[str] = ValueSlot(str)
            age: ValueRef[int] = ValueSlot(int)

        # Create operations
        read_op = User.name.get()
        write_cmd = User.name.set("Alice")
    """

    def __init__(
        self,
        field_name: KeyComponent,
        value_type: type[T],
        view_type: type[View],
        parent_ref: Ref | None = None,
    ) -> None:
        """Initialize value reference.

        Args:
            field_name: Name of this field
            value_type: Python type of the value (int, str, etc.)
            view_type: View class for parent container access
            parent_ref: Parent reference in navigation chain
        """
        self.field_name = field_name
        self.value_type = value_type
        self.view_type = view_type
        self.parent_ref = parent_ref

        # Cache static path for performance
        self._compute_static_path()

    def _compute_static_path(self) -> None:
        """Compute and cache static ViewPath."""
        if self.parent_ref is None:
            self.static_view_path: ViewPath = ()
            self.is_dynamic = False
        else:
            # Build from parent's view path
            self.static_view_path = self.parent_ref.resolve_view_path()
            self.is_dynamic = False

    def resolve_view_path(self) -> ViewPath:
        """Get ViewPath to parent container.

        Returns:
            Cached ViewPath
        """
        return self.static_view_path

    def resolve(self, context: Context) -> ValuePath:
        """Resolve to complete ValuePath.

        Args:
            context: Execution context (unused for static refs)

        Returns:
            Complete path including value segment
        """
        view_path = self.resolve_view_path()
        return (*view_path, (self.field_name, self.value_type))

    def parent(self) -> Ref | None:
        """Get parent reference.

        Returns:
            Parent ref or None if root
        """
        return self.parent_ref

    def last_segment(self) -> KeyComponent:
        """Get last path segment.

        Returns:
            Field name
        """
        return self.field_name

    def execute(self, context: Context) -> ValueRef[T]:
        """Execute returns self - refs are locations, not computations.

        Args:
            context: Unused

        Returns:
            Self
        """
        return self

    # ---- Operations ----

    def get(self) -> GetOp[T]:
        """Create read operation.

        Returns:
            Operation that reads this value
        """
        return GetOp(self)

    def set(self, value: T) -> SetCmd[T]:
        """Create write command.

        Args:
            value: Value to write

        Returns:
            Command that writes this value
        """
        return SetCmd(self, value)

    def __repr__(self) -> str:
        """String representation."""
        if self.parent_ref:
            return f"{self.parent_ref!r}.{self.field_name}"
        return str(self.field_name)


class ShapeRef[T](Ref[T]):
    """Reference to a nested shape.

    Represents an addressable location containing a nested shape structure.
    Supports navigation to nested fields via attribute access.

    Example:
        class Profile(Shape):
            email: ValueRef[str] = ValueSlot(str)

        class User(Shape):
            profile: Profile = ShapeSlot(Profile)

        # Navigate to nested field
        email_ref = User.profile.email  # Returns ValueRef
    """

    def __init__(
        self,
        field_name: KeyComponent,
        shape_type: type[Shape],
        view_type: type[View],
        parent_ref: Ref | None = None,
    ) -> None:
        """Initialize shape reference.

        Args:
            field_name: Name of this field
            shape_type: Shape class definition
            view_type: View class for container access
            parent_ref: Parent reference in navigation chain
        """
        self.field_name = field_name
        self.shape_type = shape_type
        self.value_type = shape_type  # For Ref[T] compatibility
        self.view_type = view_type
        self.parent_ref = parent_ref

        # Cache static path
        self._compute_static_path()

    def _compute_static_path(self) -> None:
        """Compute and cache static ViewPath."""
        if self.parent_ref is None:
            self.static_view_path: ViewPath = ()
            self.is_dynamic = False
        else:
            self.static_view_path = self.parent_ref.resolve_view_path()
            self.is_dynamic = False

    def resolve_view_path(self) -> ViewPath:
        """Get ViewPath including this container.

        Returns:
            ViewPath with this shape's segment appended
        """
        parent_path = self.static_view_path
        return (*parent_path, (self.field_name, self.view_type))

    def resolve(self, context: Context) -> ValuePath:
        """Resolve to ValuePath (same as ViewPath for containers).

        Args:
            context: Execution context (unused)

        Returns:
            Path to this container
        """
        return self.resolve_view_path()

    def parent(self) -> Ref | None:
        """Get parent reference.

        Returns:
            Parent ref or None if root
        """
        return self.parent_ref

    def last_segment(self) -> KeyComponent:
        """Get last path segment.

        Returns:
            Field name
        """
        return self.field_name

    def execute(self, context: Context) -> ShapeRef[T]:
        """Execute returns self.

        Args:
            context: Unused

        Returns:
            Self
        """
        return self

    def __getattribute__(self, name: str) -> object:
        """Navigate to nested fields in the shape.

        When accessing User.profile.email:
        1. User.profile returns ShapeRef (this instance)
        2. .email calls this method
        3. Look up 'email' in Profile._slots
        4. Call slot.create_ref(Profile, parent_ref=self)
        5. Return the new ref

        Args:
            name: Field name to access

        Returns:
            Ref created by the nested slot

        Raises:
            AttributeError: If field doesn't exist in nested shape
        """
        # Allow access to internal attributes
        if name in {
            "field_name",
            "shape_type",
            "value_type",
            "view_type",
            "parent_ref",
            "static_view_path",
            "is_dynamic",
            "resolve",
            "resolve_view_path",
            "execute",
            "parent",
            "last_segment",
            "_compute_static_path",
        }:
            return object.__getattribute__(self, name)

        # Get shape type
        shape_type: type[Shape] = object.__getattribute__(self, "shape_type")

        # Check if shape has this slot
        if hasattr(shape_type, "_slots") and name in shape_type._slots:
            slot = shape_type._slots[name]
            return slot.create_ref(owner_shape=shape_type, parent_ref=self)

        # Not a slot - raise error
        raise AttributeError(f"{shape_type.__name__} has no slot '{name}'")

    def __repr__(self) -> str:
        """String representation."""
        if self.parent_ref:
            return f"{self.parent_ref!r}.{self.field_name}"
        return str(self.field_name)


# =============================================================================
# OPERATIONS
# =============================================================================


class GetOp[T](Operation[T]):
    """Read operation for primitive values.

    Pure operation with no side effects. Navigates to the target location
    using layer 3 View system and reads the value.

    Example:
        value = User.name.get().execute(ctx)
    """

    def __init__(self, ref: ValueRef[T]) -> None:
        """Initialize read operation.

        Args:
            ref: Reference to read from
        """
        self.ref = ref

    @property
    def is_pure(self) -> bool:
        """Read operations are pure.

        Returns:
            True
        """
        return True

    def execute(self, context: Context) -> T:
        """Execute read operation.

        Uses layer 3 navigation to reach the target and read the value.

        Args:
            context: Execution context with root view and storage context

        Returns:
            Value read from storage

        Raises:
            KeyError: If value doesn't exist
        """
        # Resolve ref to ValuePath
        value_path = self.ref.resolve(context)

        # Navigate using layer 3
        parent_view, key = navigate_value(context.root_view, value_path)

        # Read primitive value through View
        value = parent_view._get_child_value(key)
        return cast("T", value)

    def __repr__(self) -> str:
        """String representation."""
        return f"GetOp({self.ref!r})"


class SetCmd[T](Command):
    """Write command for primitive values.

    Impure command with side effects. Navigates to the target location
    using layer 3 View system and writes the value.

    Example:
        User.name.set("Alice").execute(ctx)
    """

    def __init__(self, ref: ValueRef[T], value: T) -> None:
        """Initialize write command.

        Args:
            ref: Reference to write to
            value: Value to write
        """
        self.ref = ref
        self.value = value

    @property
    def is_pure(self) -> bool:
        """Write commands are impure.

        Returns:
            False
        """
        return False

    def execute(self, context: Context) -> None:
        """Execute write command.

        Uses layer 3 navigation to reach the target and write the value.

        Args:
            context: Execution context with root view and storage context
        """
        # Resolve ref to ValuePath
        value_path = self.ref.resolve(context)

        # Navigate using layer 3
        parent_view, key = navigate_value(context.root_view, value_path)

        # Write primitive value through View
        parent_view._set_child_value(key, self.value)

    def __repr__(self) -> str:
        """String representation."""
        return f"SetCmd({self.ref!r}, {self.value!r})"


# =============================================================================
# SLOT FACTORIES
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
        return ValueRef(
            field_name=self.name,
            value_type=self.value_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
        )


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
        return ShapeRef(
            field_name=self.name,
            shape_type=self.value_type,
            view_type=self.view_type,
            parent_ref=parent_ref,
        )


def ValueSlot(value_type: type, view_type: type[View] | None = None) -> Any:
    """Create a value slot for primitive types.

    Factory function that returns a slot instance. The return type is Any
    to support proper IDE type hints in shape definitions.

    Args:
        value_type: Python type of the value (int, str, float, etc.)
        view_type: Optional view type (defaults to DictView in parent)

    Returns:
        Slot instance (typed as Any for IDE support)

    Example:
        class User(Shape):
            name: ValueRef[str] = ValueSlot(str)
            age: ValueRef[int] = ValueSlot(int)
            balance: ValueRef[float] = ValueSlot(float)
    """
    # Import here to avoid circular dependency
    from rwstd.views import DictView

    return _ValueSlot(value_type=value_type, view_type=view_type or DictView)


def ShapeSlot(shape_type: type[Shape], view_type: type[View] | None = None) -> Any:
    """Create a shape slot for nested shapes.

    Factory function that returns a slot instance. The return type is Any
    to support proper IDE type hints in shape definitions.

    Args:
        shape_type: Shape class for the nested structure
        view_type: Optional view type (defaults to DictView in parent)

    Returns:
        Slot instance (typed as Any for IDE support)

    Example:
        class Profile(Shape):
            email: ValueRef[str] = ValueSlot(str)

        class User(Shape):
            profile: Profile = ShapeSlot(Profile)

        # Navigate to nested field
        User.profile.email  # Returns ValueRef[str]
    """
    # Import here to avoid circular dependency
    from rwstd.views import DictView

    return _ShapeSlot(value_type=shape_type, view_type=view_type or DictView)
