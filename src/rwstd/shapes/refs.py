"""Reference implementations for Shape system.

This module provides concrete Ref types that work with the View layer:
- ValueRef: references to primitive values
- ShapeRef: references to nested structures

These build on the contracts in term.py and integrate with the Path
navigation system from redwood.loc.path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from redwood.shape import LValue, PrimitiveRefBase, RValue, Shape, ViewRefBase, literal


if TYPE_CHECKING:
    from redwood.loc import path
    from redwood.shape import RValue, Shape
    from redwood.view import View

    from .commands import AppendCmd, SetCmd, StoreCmd
    from .operations import ExtractOp, GetOp


__all__ = [
    "MappingRef",
    "SequenceRef",
    "ShapeRef",
    "ValueRef",
]


# =============================================================================
# VALUE REFERENCES
# =============================================================================


class ValueRef[T](PrimitiveRefBase):
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

    def get(self) -> GetOp[T]:
        """Create read operation."""
        from .operations import GetOp

        return GetOp(self)

    def set(self, value: T | RValue[T]) -> SetCmd[T]:
        """Create write command."""
        from .commands import SetCmd

        return SetCmd(self, literal(value))


class SequenceValueRef[T](PrimitiveRefBase):
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

    def get(self) -> GetOp[T]:
        """Create read operation."""
        from .operations import GetOp

        return GetOp(self)

    def set(self, value: T | RValue[T]) -> SetCmd[T]:
        """Create write command."""
        from .commands import SetCmd

        return SetCmd(self, literal(value))


class MappingValueRef[T](PrimitiveRefBase):
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

    def get(self) -> GetOp[T]:
        """Create read operation."""
        from .operations import GetOp

        return GetOp(self)

    def set(self, value: T | RValue[T]) -> SetCmd[T]:
        """Create write command."""
        from .commands import SetCmd

        return SetCmd(self, literal(value))


# =============================================================================
# SHAPE REFERENCE
# =============================================================================


class ShapeRef[T](ViewRefBase):
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
        address: path.PathAddress,
        shape_type: type[Shape],
        view_type: type[View],
        parent_ref: LValue | None = None,
    ) -> None:
        """Initialize shape reference.

        Args:
            address: Address of this field in parent's domain
            shape_type: Shape class defining structure
            view_type: View class for this container
            parent_ref: Parent reference in navigation chain
        """
        super().__init__(address, view_type, parent_ref)

        self.shape_type = shape_type

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
            "address",
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

        return StoreCmd(self, literal(data))


# =============================================================================
# MAPPING REFERENCE
# =============================================================================


class MappingRef[K: int | str, V](ViewRefBase):
    """Reference to a mapping container.

    Points to dict-like nodes in the tree. Supports subscripting to access items.
    Items can be primitives, shapes, or nested collections.

    Example:
        class Market(Shape):
            signals: MappingRef[float] = MappingSlot(float)
            symbols: MappingRef[SymbolInfo] = MappingSlot(SymbolInfo)
            data: MappingRef = MappingSlot(Sequence(float))

        # Access items
        Market.signals["vix"].get()           # ValueRef[float]
        Market.symbols["AAPL"].price.get()    # ShapeRef navigation
        Market.data["timeseries"][0].get()    # Nested collection
    """

    def __init__(
        self,
        address: path.PathAddress,
        value_type: type[V],
        view_type: type[View],
        parent_ref: LValue | None = None,
    ) -> None:
        """Initialize mapping reference.

        Args:
            address: Address of this field in parent's domain
            value_type: Python type of values (or CollectionDescriptor for nested)
            view_type: View class for this mapping (e.g., DictView)
            parent_ref: Parent reference in navigation chain
        """
        super().__init__(address, view_type, parent_ref)
        self.value_type = value_type

    def __getitem__(self, key: K | RValue[K]) -> MappingValueRef[V]:
        """Subscript to get item reference.

        Returns appropriate ref type based on value_type:
        - Primitive → ValueRef
        - Shape → ShapeRef
        - Mapping descriptor → MappingRef
        - Sequence descriptor → SequenceRef

        Args:
            key: Key to access in mapping

        Returns:
            Reference to the item
        """
        return MappingValueRef(
            address=literal(key),
            value_type=self.value_type,
            parent_ref=self,
        )

    def extract(self) -> ExtractOp[dict[K, V]]:
        """Create extract operation.

        Returns:
            ExtractOp that reads entire structure
        """
        from .operations import ExtractOp

        return ExtractOp(self)

    def store(self, data: dict[K, V] | RValue[dict[K, V]]) -> StoreCmd[dict[K, V]]:
        """Create store command.

        Args:
            data: Dictionary to store, or RValue producing dict

        Returns:
            StoreCmd that writes entire structure
        """
        from .commands import StoreCmd

        return StoreCmd(self, literal(data))


# =============================================================================
# SEQUENCE REFERENCE
# =============================================================================


class SequenceRef[T](ViewRefBase):
    """Reference to a sequence container.

    Points to list-like nodes in the tree. Supports subscripting to access items.
    Items can be primitives, shapes, or nested collections.

    Example:
        class Market(Shape):
            prices: SequenceRef[float] = SequenceSlot(float)
            orders: SequenceRef[Order] = SequenceSlot(Order)
            nested: SequenceRef = SequenceSlot(Mapping(str))

        # Access items
        Market.prices[0].get()              # ValueRef[float]
        Market.orders[0].id.get()           # ShapeRef navigation
        Market.nested[0]["key"].get()       # Nested collection
    """

    def __init__(
        self,
        address: path.PathAddress,
        item_type: type[T],
        view_type: type[View],
        parent_ref: LValue | None = None,
    ) -> None:
        """Initialize mapping reference.

        Args:
            address: Address of this field in parent's domain
            item_type: Python type of values (or CollectionDescriptor for nested)
            view_type: View class for this mapping (e.g., DictView)
            parent_ref: Parent reference in navigation chain
        """
        super().__init__(address, view_type, parent_ref)
        self.item_type = item_type

    def __getitem__(self, key: str | int | RValue[str | int]) -> SequenceValueRef[T]:
        """Subscript to get item reference.

        Returns appropriate ref type based on value_type:
        - Primitive → ValueRef
        - Shape → ShapeRef
        - Mapping descriptor → MappingRef
        - Sequence descriptor → SequenceRef

        Args:
            key: Key to access in mapping

        Returns:
            Reference to the item
        """
        return SequenceValueRef(
            address=literal(key),
            value_type=self.item_type,
            parent_ref=self,
        )

    def append(self, value: T | RValue[T]) -> AppendCmd[T]:
        """Create write command."""
        from .commands import AppendCmd

        return AppendCmd(ref=self, value=literal(value))

    def extract(self) -> ExtractOp[list[T]]:
        """Create extract operation.

        Returns:
            ExtractOp that reads entire structure
        """
        from .operations import ExtractOp

        return ExtractOp(self)

    def store(self, data: list[T] | RValue[list[T]]) -> StoreCmd[list[T]]:
        """Create store command.

        Args:
            data: Dictionary to store, or RValue producing dict

        Returns:
            StoreCmd that writes entire structure
        """
        from .commands import StoreCmd

        return StoreCmd(self, literal(data))
