"""PV storage substrate refs.

PV (Polymorphic Views) storage refs navigate through a view hierarchy
to access values stored in key-value backends.

Hierarchy:
    PVRefBase[T]           - PV substrate root with address/parent/shape
    ├── PVPrimitiveRef[T]  - refs to leaf values (int, str, etc.)
    └── PVViewRef[T, V]    - refs to container views (dict, list, set)

Core vocabulary:
    resolve(ctx) → Path    - build path from parent chain
    fetch(ctx) → T         - navigate views and extract value
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from logging import getLogger
from typing import TYPE_CHECKING, Generic, TypeVar

import pv.traits as view_traits
from pv.loc import path

from every import EMPTY, Context, Ref, Sentinel, Term


if TYPE_CHECKING:
    from pv.view import View

    from every import Shape


__all__ = [
    "PVPrimitiveRef",
    "PVRefBase",
    "PVViewRef",
]


T = TypeVar("T")
ViewT = TypeVar("ViewT", bound="View")

logger = getLogger(__name__)


class PVRefBase[T](Ref[T], ABC):
    """Base for all PV storage refs.

    PV refs navigate through a view hierarchy to access values.
    They maintain parent chains for path construction and shape
    associations for context lookup.

    Attributes:
        _address: The address/key for this ref's segment
        _parent: Parent ref in the navigation chain
        _shape: Shape class for context lookup
    """

    __slots__ = ("_address", "_parent", "_shape")

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVRefBase | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        """Initialize PV ref.

        Args:
            address: Address/key for this segment (or Term for dynamic)
            parent: Parent ref in navigation chain
            shape: Shape class for context lookup
        """
        self._address = address
        self._parent = parent
        self._shape = shape

    @property
    def address(self) -> path.PathAddress | Term:
        """The address/key for this ref's path segment."""
        return self._address

    @property
    def parent(self) -> PVRefBase | None:
        """Parent ref in the navigation chain."""
        return self._parent

    @property
    def shape(self) -> type[Shape] | None:
        """Shape class for context lookup."""
        return self._shape

    def get_root_shape(self) -> type[Shape] | None:
        """Get the root shape for context lookup.

        Traverses up the parent chain to find the shape.
        """
        if self._shape is not None:
            return self._shape
        if self._parent is not None:
            return self._parent.get_root_shape()
        return None

    @property
    @abstractmethod
    def _type_marker(self) -> type:
        """Type marker for path segments (value_type or view_type)."""
        ...

    def _resolve_address(self, ctx: Context) -> path.PathAddress:
        """Resolve dynamic address if needed."""
        if isinstance(self._address, Term):
            return self._address.execute(ctx)
        return self._address

    def __repr__(self) -> str:
        if self._parent:
            return f"<{self.__class__.__name__}: {self._parent!r} -> {self._address!r}>"
        return f"<{self.__class__.__name__}: {self._address!r}>"

    def __str__(self) -> str:
        if self._parent:
            return f"{self.__class__.__name__}({self._parent!s} -> {self._address!s})"
        return f"{self.__class__.__name__}({self._address!s})"


class PVPrimitiveRef[T](PVRefBase[T]):
    """PV ref to a primitive/leaf value.

    Used for scalar values like int, str, float, etc.
    fetch() navigates to the parent view and subscripts to get the value.
    """

    __slots__ = ("_value_type",)

    def __init__(
        self,
        address: path.PathAddress | Term,
        value_type: type[T],
        parent: PVRefBase | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        """Initialize primitive ref.

        Args:
            address: Key/address for this value
            value_type: The Python type of the value
            parent: Parent ref in navigation chain
            shape: Shape class for context lookup
        """
        super().__init__(address, parent, shape)
        self._value_type = value_type

    @property
    def value_type(self) -> type[T]:
        """The Python type of the value at this location."""
        return self._value_type

    @property
    def _type_marker(self) -> type:
        return self._value_type

    def resolve(self, ctx: Context) -> path.PathToValue:
        """Build path from parent chain ending at this value.

        Args:
            ctx: Execution context

        Returns:
            Path tuple ending with (address, value_type)
        """
        address = self._resolve_address(ctx)

        if self._parent is None:
            resolved_path = ((address, self._value_type),)
        else:
            parent_path = self._parent.resolve(ctx)
            resolved_path = (*parent_path, (address, self._value_type))

        logger.debug(
            "PVPrimitiveRef resolved",
            extra={
                "address": address,
                "value_type": self._value_type.__name__,
                "has_parent": self._parent is not None,
                "resolved_path": resolved_path,
            },
        )
        return resolved_path  # type: ignore

    def fetch(self, ctx: Context) -> T | Sentinel:
        """Fetch the value from PV storage.

        Navigates through the view hierarchy and reads the value.
        Returns Empty if the value doesn't exist.

        Args:
            ctx: Execution context with root_view access

        Returns:
            The value, or Empty if not found
        """
        value_path = self.resolve(ctx)
        root_view = ctx.get_context_for_shape(self.get_root_shape()).root_view

        try:
            parent_view, key = path.navigate_value(root_view, value_path)
            if isinstance(parent_view, view_traits.Subscriptable):
                return parent_view[key]
            raise TypeError(f"View {parent_view.__class__.__name__} is not subscriptable")
        except (KeyError, IndexError):
            return EMPTY


class PVViewRef(Generic[T, ViewT], PVRefBase[T]):  # noqa: UP046
    """PV ref to a container view.

    Used for collection types like dict, list, set views.
    fetch() navigates to and returns the view itself.
    """

    __slots__ = ("_view_type",)

    def __init__(
        self,
        address: path.PathAddress | Term,
        view_type: type[ViewT],
        parent: PVRefBase | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        """Initialize view ref.

        Args:
            address: Key/address for this view
            view_type: The View class type
            parent: Parent ref in navigation chain
            shape: Shape class for context lookup
        """
        super().__init__(address, parent, shape)
        self._view_type = view_type

    @property
    def view_type(self) -> type[ViewT]:
        """The View class type at this location."""
        return self._view_type

    @property
    def _type_marker(self) -> type:
        return self._view_type

    def resolve(self, ctx: Context) -> path.PathToView:
        """Build path from parent chain ending at this view.

        Args:
            ctx: Execution context

        Returns:
            Path tuple ending with (address, view_type)
        """
        address = self._resolve_address(ctx)

        if self._parent is None:
            resolved_path = ((address, self._view_type),)
        else:
            parent_path = self._parent.resolve(ctx)
            resolved_path = (*parent_path, (address, self._view_type))

        logger.debug(
            "PVViewRef resolved",
            extra={
                "address": address,
                "view_type": self._view_type.__name__,
                "has_parent": self._parent is not None,
                "resolved_path": resolved_path,
            },
        )
        return resolved_path

    def fetch(self, ctx: Context) -> ViewT:
        """Fetch the view from PV storage.

        Navigates through the view hierarchy to get this view.

        Args:
            ctx: Execution context with root_view access

        Returns:
            The view instance
        """
        view_path = self.resolve(ctx)
        root_view = ctx.get_context_for_shape(self.get_root_shape()).root_view

        if not view_path:
            return root_view  # type: ignore
        return path.navigate_view(root_view, view_path)  # type: ignore
