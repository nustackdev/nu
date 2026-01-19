"""Typed reference to storage location.

Term                        - executable node
├── LValue                  - addressable location (has path)
│   └── Ref                 - typed reference to storage location
│       ├── ViewRef         - reference to container (dict, list, set)
│       └── PrimitiveRef    - reference to leaf value (int, str, etc.)
"""

from __future__ import annotations

from abc import ABC
from logging import getLogger
from typing import TYPE_CHECKING, Generic, TypeVar

from everyshape.loc import path
from everyshape.typing.ref import Extractable, Gettable

from ..context import Context
from ..term import LValue, Term


if TYPE_CHECKING:
    from everyshape.shape import Shape
    from everyshape.view import View

    from ..context import Context


__all__ = [
    "PrimitiveRef",
    "Ref",
    "ViewRef",
]

ViewT_co = TypeVar("ViewT_co", covariant=True, bound="View")
ViewRefResultT = TypeVar("ViewRefResultT")

logger = getLogger(__name__)


class Ref[T, PathTypeT: path.Path](LValue[T, PathTypeT], ABC):
    """Typed reference to a location in the tree.

    Combines addressability (LValue) with type information.
    Refs are both locations AND terms (dual nature):

    As Ref:
    - Can resolve to paths
    - Can navigate to parent

    As Term:
    - Can execute (returns self)
    - Can be used in children tuples

    Generic type T specifies value type at this location:
        Ref[float] → location holding float
        Ref[str]   → location holding string
        Ref[Order] → location holding Order shape

    Concrete implementations (see in standard library or ecosystem repo):
        ValueRef[T]     - primitive values
        ShapeRef[T]     - nested structures
        MapRef[K,V]     - mapping containers
        MapItemRef[T]   - specific map entries

    Implementations determine:
    - Storage strategy (caching, lazy evaluation)
    - Navigation behavior (nested field access)
    - Available operations (get/set for values, keys/items for maps)
    """

    def __init__(self, parent_ref: Ref | None, owner_shape: type[Shape] | None) -> None:
        """Init Ref."""
        self.parent_ref = parent_ref
        self.owner_shape = owner_shape

    @property
    def is_pure(self) -> bool:
        """Refs are always pure.

        Returns:
            True - refs never have side effects
        """
        return True

    @property
    def parent(self) -> Ref | None:
        """Get parent location in the navigation chain.

        Used for path construction and hierarchy traversal.
        Root locations return None.

        Returns:
            Parent Ref, or None if this is root
        """
        return self.parent_ref

    def get_owner_shape(self) -> type[Shape] | None:
        """Get the Shape class this Ref was created by."""
        if self.owner_shape is not None:
            return self.owner_shape

        if self.parent is not None:
            return self.parent.owner_shape

        return None

    def get_root_shape(self) -> type[Shape] | None:
        """Get the Shape class this Ref was originated from."""
        if self.parent is not None:
            return self.parent.get_root_shape()

        if self.owner_shape is not None:
            return self.owner_shape

        return None


class ViewRef(Generic[ViewRefResultT, ViewT_co], Ref[ViewRefResultT, path.PathToView], ABC):  # noqa: UP046
    """Ref that points to a View (container in the tree)."""

    def __init__(
        self,
        address: path.PathAddress | Term,
        view_type: type[ViewT_co],
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Init ViewRef."""
        super().__init__(parent_ref, owner_shape)

        self.address = address
        self.view_type = view_type

    def resolve(self, context: Context) -> path.PathToView:
        """Resolve to path ending at this shape's view.

        Args:
            context: Execution context

        Returns:
            Path ending with view segment
        """
        if isinstance(self.address, Term):
            address = self.address.execute(context)
        else:
            address = self.address

        if self.parent_ref is None:
            resolved_path = ((address, self.view_type),)
        else:
            parent_path = self.parent_ref.resolve(context)
            resolved_path = (*parent_path, (address, self.view_type))

        logger.debug(
            "ViewRef resolved",
            extra={
                "address": address,
                "view_type": self.view_type.__name__,
                "has_parent": self.parent_ref is not None,
                "resolved_path": resolved_path,
            },
        )
        return resolved_path

    def __repr__(self) -> str:
        """ViewRef representation in machine-friendly format."""
        if self.parent_ref:
            return f"<ViewRef: {self.parent_ref!r} -> {self.address!r}>"
        return f"<ViewRef: {self.address!r}>"

    def __str__(self) -> str:
        """ViewRef representation in human-friendly format."""
        if self.parent_ref:
            return f"ViewRef({self.parent_ref!s} -> {self.address!s})"
        return f"ViewRef({self.address!s})"

    def execute(self, context: Context) -> ViewRefResultT:
        """Execute the Ref."""
        # TODO: proper implementation
        if isinstance(self, Extractable):
            return self.extract().execute(context)
        raise TypeError


class PrimitiveRef[T](Ref[T, path.PathToValue], ABC):
    """Ref that points to a primtive value in the tree (leaf node)."""

    def __init__(
        self,
        address: path.PathAddress | Term,
        value_type: type[T],
        parent_ref: Ref | None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Init ValueRef."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.value_type = value_type

    def resolve(self, context: Context) -> path.PathToValue:
        """Resolve to complete path ending at value.

        Args:
            context: Execution context

        Returns:
            Path ending with value segment
        """
        if isinstance(self.address, Term):
            address = self.address.execute(context)
        else:
            address = self.address

        if self.parent_ref is None:
            resolved_path = ((self.address, self.value_type),)
        else:
            parent_path = self.parent_ref.resolve(context)
            resolved_path = (*parent_path, (address, self.value_type))

        logger.debug(
            "PrimitiveRef resolved",
            extra={
                "address": address,
                "value_type": type(self.value_type).__name__,
                "has_parent": self.parent_ref is not None,
                "resolved_path": resolved_path,
            },
        )
        return resolved_path  # type: ignore

    def __repr__(self) -> str:
        """PrimitiveRef representation in machine-friendly format."""
        if self.parent_ref:
            return f"<PrimitiveRef: {self.parent_ref!r} -> {self.address!r}>"
        return f"<PrimitiveRef: {self.address!r}>"

    def __str__(self) -> str:
        """PrimitiveRef representation in human-friendly format."""
        if self.parent_ref:
            return f"PrimitiveRef({self.parent_ref!s} -> {self.address!s})"
        return f"PrimitiveRef({self.address!s})"

    def execute(self, context: Context) -> T:
        """Execute the Ref."""
        # TODO: proper implementation
        if isinstance(self, Gettable):
            return self.get().execute(context)
        raise TypeError
