"""Base LValue implementation.

This module defines the base classes for concrete LValue implementations.
LValueBase and RefBase provide the foundation for building type-specific
references that represent locations in storage.

Key difference from RValues:
- LValues are LOCATIONS in storage (lazy access)
- RValues are ALREADY COMPUTED values in memory

LValues compose through parent references and resolve to paths
for storage access.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from everyshape.loc import path


if TYPE_CHECKING:
    from everyshape.shape.context import ContextProtocol
    from everyshape.shape.shape import Shape


__all__ = [
    "LValueBase",
    "PrimitiveRefBase",
    "RefBase",
    "ViewRefBase",
]


class LValueBase[PathT, ContextT: ContextProtocol](ABC):
    """Base class for all LValue implementations.

    LValueBase provides the foundation for location references:
    - Path resolution to storage locations
    - Parent navigation for hierarchical access
    - Owner shape tracking

    Type Parameters:
        PathT: The path type this LValue resolves to
        ContextT: The execution context type

    Design Principles:
        - Lazy: LValues don't access storage until operations are executed
        - Composable: Parent refs form navigation chains
        - Type-safe: Generic types ensure type consistency

    Example:
        >>> # Navigate to nested location
        >>> price_ref = Market.orders["AAPL"].price
        >>> # Create operation
        >>> get_op = price_ref.get()
        >>> # Execute to access storage
        >>> value = get_op.execute(ctx)
    """

    @abstractmethod
    def resolve(self, context: ContextT) -> PathT:
        """Resolve this LValue to a concrete storage path.

        Args:
            context: Execution context for dynamic path resolution

        Returns:
            Path to the storage location
        """
        ...

    @property
    @abstractmethod
    def parent(self) -> LValueBase | None:
        """Get parent LValue in the navigation chain.

        Returns:
            Parent LValue or None if at root
        """
        ...

    @property
    def is_pure(self) -> bool:
        """LValues are always pure (no side effects).

        Returns:
            True (always pure)
        """
        return True


class RefBase[PathT, ContextT: ContextProtocol](LValueBase[PathT, ContextT], ABC):
    """Base class for typed references.

    RefBase extends LValueBase with:
    - Owner shape tracking
    - Parent ref access
    - Common ref operations

    Type Parameters:
        PathT: The path type this Ref resolves to
        ContextT: The execution context type

    Attributes:
        parent_ref: Parent reference in navigation chain
        owner_shape: Shape class that owns this ref

    Example:
        >>> class MyRef(RefBase[PathToValue, Context]):
        ...     def resolve(self, ctx):
        ...         # Resolve to path
        ...         pass
    """

    def __init__(
        self,
        parent_ref: RefBase | None,
        owner_shape: type[Shape] | None,
    ) -> None:
        """Initialize ref with parent and owner.

        Args:
            parent_ref: Parent reference in navigation chain
            owner_shape: Shape class that owns this ref
        """
        self._parent_ref = parent_ref
        self._owner_shape = owner_shape

    @property
    def parent(self) -> RefBase | None:
        """Get parent reference.

        Returns:
            Parent ref or None if at root
        """
        return self._parent_ref

    @property
    def parent_ref(self) -> RefBase | None:
        """Alias for parent property.

        Returns:
            Parent ref or None if at root
        """
        return self._parent_ref

    @property
    def owner_shape(self) -> type[Shape] | None:
        """Get the Shape class this ref belongs to.

        Returns:
            Owner shape class or None
        """
        return self._owner_shape

    def get_owner_shape(self) -> type[Shape] | None:
        """Get the Shape class this ref was created by.

        Walks up parent chain if owner not set directly.

        Returns:
            Owner shape class or None
        """
        if self._owner_shape is not None:
            return self._owner_shape

        if self._parent_ref is not None:
            return self._parent_ref.get_owner_shape()

        return None

    def get_root_shape(self) -> type[Shape] | None:
        """Get the root Shape class in the navigation chain.

        Returns:
            Root shape class or None
        """
        if self._parent_ref is not None:
            return self._parent_ref.get_root_shape()

        if self._owner_shape is not None:
            return self._owner_shape

        return None


class PrimitiveRefBase[T, ContextT: ContextProtocol](
    RefBase[path.PathToValue, ContextT],
    ABC,
):
    """Base class for primitive (leaf) value references.

    PrimitiveRefBase provides foundation for refs to single values
    like int, str, float, bool.

    Type Parameters:
        T: Type of the value at this location
        ContextT: The execution context type

    Attributes:
        address: Address/key for this value
        value_type: Python type of the value

    Example:
        >>> class IntValueRef(PrimitiveRefBase[int, Context]):
        ...     def get(self):
        ...         return GetOp(self)
    """

    def __init__(
        self,
        address: path.PathAddress,
        value_type: type[T],
        parent_ref: RefBase | None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize primitive ref.

        Args:
            address: Address/key for this value
            value_type: Python type of the value
            parent_ref: Parent reference
            owner_shape: Owner shape class
        """
        super().__init__(parent_ref, owner_shape)
        self._address = address
        self._value_type = value_type

    @property
    def address(self) -> path.PathAddress:
        """Get the address for this value.

        Returns:
            Address/key
        """
        return self._address

    @property
    def value_type(self) -> type[T]:
        """Get the value type.

        Returns:
            Python type of value
        """
        return self._value_type


class ViewRefBase[ViewT, ContextT: ContextProtocol](
    RefBase[path.PathToView, ContextT],
    ABC,
):
    """Base class for container (view) references.

    ViewRefBase provides foundation for refs to containers
    like dict, list, set.

    Type Parameters:
        ViewT: Type of the view at this location
        ContextT: The execution context type

    Attributes:
        address: Address/key for this container
        view_type: View class for this container

    Example:
        >>> class DictRef(ViewRefBase[MutableMapping, Context]):
        ...     def extract(self):
        ...         return ExtractOp(self)
    """

    def __init__(
        self,
        address: path.PathAddress,
        view_type: type[ViewT],
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize view ref.

        Args:
            address: Address/key for this container
            view_type: View class for this container
            parent_ref: Parent reference
            owner_shape: Owner shape class
        """
        super().__init__(parent_ref, owner_shape)
        self._address = address
        self._view_type = view_type

    @property
    def address(self) -> path.PathAddress:
        """Get the address for this container.

        Returns:
            Address/key
        """
        return self._address

    @property
    def view_type(self) -> type[ViewT]:
        """Get the view type.

        Returns:
            View class
        """
        return self._view_type
