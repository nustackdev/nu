"""PV storage substrate refs.

PV (Polymorphic Views) storage refs navigate through a view hierarchy
to access values stored in key-value backends.

Hierarchy:
    everyshape.Ref[T]    - document-model base (address/parent/shape)
        |
    Ref[T]           - PV substrate base
    ├── PrimitiveRef[T]  - refs to leaf values (int, str, etc.)
    └── ViewRef[T, V]    - refs to container views (dict, list, set)

Core vocabulary:
    resolve(ctx) -> Path    - build path from parent chain
    fetch(ctx) -> T         - navigate views and extract value
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Generic, TypeVar

import pv.traits as view_traits
from pv import Empty as PVEmpty
from pv.loc import path
from pv.view import View

from everyabc import EMPTY, Arg, Context, Sentinel
from everyshape import Ref


if TYPE_CHECKING:
    from everyshape import Shape


__all__ = [
    "PrimitiveRef",
    "ViewRef",
]


T = TypeVar("T")
ViewT = TypeVar("ViewT", bound="View")

logger = getLogger(__name__)


class ViewRef(Generic[T, ViewT], Ref[T]):  # noqa: UP046
    """PV ref to a container view.

    Used for collection types like dict, list, set views.
    fetch() navigates to and returns the view itself.
    """

    def __init__(
        self,
        address: Arg[path.PathAddress],
        view_type: type[ViewT],
        parent: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize view ref.

        Args:
            address: Key/address for this view
            view_type: The View class type
            parent: Parent ref in navigation chain
            owner_shape: Shape class for context lookup
        """
        super().__init__(address, parent, owner_shape)
        self._view_type = view_type

    @property
    def view_type(self) -> type[ViewT]:
        """The View class type at this location."""
        return self._view_type

    @property
    def _type_marker(self) -> type:
        return self._view_type

    async def resolve(self, ctx: Context) -> path.PathToView:
        """Build path from parent chain ending at this view.

        Args:
            ctx: Execution context

        Returns:
            Path tuple ending with (address, view_type)
        """
        address = await self.resolve_address(ctx)

        if self._parent is None:
            resolved_path = ((address, self._view_type),)
        else:
            parent_path = await self._parent.resolve(ctx)
            resolved_path = (*parent_path, (address, self._view_type))

        logger.debug(
            "ViewRef resolved",
            extra={
                "address": address,
                "view_type": self._view_type.__name__,
                "has_parent": self._parent is not None,
                "resolved_path": resolved_path,
            },
        )
        return resolved_path

    async def fetch(self, ctx: Context) -> ViewT | Sentinel:
        """Fetch the view from PV storage.

        Navigates through the view hierarchy to get this view.

        Args:
            ctx: Execution context with root_view access

        Returns:
            The view instance
        """
        view_path = await self.resolve(ctx)
        shape = self.get_root_shape()
        root_view = ctx.get(View, shape=shape)

        if not view_path:
            return root_view  # type: ignore
        return path.navigate_view(root_view, view_path)  # type: ignore


class PrimitiveRef[T](Ref[T]):
    """PV ref to a primitive/leaf value.

    Used for scalar values like int, str, float, etc.
    fetch() navigates to the parent view and subscripts to get the value.
    """

    def __init__(
        self,
        address: Arg[path.PathAddress],
        value_type: type[T],
        parent: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize primitive ref.

        Args:
            address: Key/address for this value
            value_type: The Python type of the value
            parent: Parent ref in navigation chain
            owner_shape: Shape class for context lookup
        """
        super().__init__(address, parent, owner_shape)
        self._value_type = value_type

    @property
    def value_type(self) -> type[T]:
        """The Python type of the value at this location."""
        return self._value_type

    @property
    def _type_marker(self) -> type:
        return self._value_type

    async def resolve(self, ctx: Context) -> path.PathToValue:
        """Build path from parent chain ending at this value.

        Args:
            ctx: Execution context

        Returns:
            Path tuple ending with (address, value_type)
        """
        address = await self.resolve_address(ctx)

        if self._parent is None:
            resolved_path = ((address, self._value_type),)
        else:
            parent_path = await self._parent.resolve(ctx)
            resolved_path = (*parent_path, (address, self._value_type))

        logger.debug(
            "PrimitiveRef resolved",
            extra={
                "address": address,
                "value_type": self._value_type.__name__,
                "has_parent": self._parent is not None,
                "resolved_path": resolved_path,
            },
        )
        return resolved_path  # type: ignore

    async def fetch_parent(self, ctx: Context) -> object:
        """Fetch the parent collection (view) for item access.

        Navigates through the view hierarchy and returns the parent view
        that contains this primitive value.

        Args:
            ctx: Execution context with root_view access

        Returns:
            The parent view object
        """
        value_path = await self.resolve(ctx)
        shape = self.owner_shape
        root_view = ctx.get(View, shape=shape)
        parent_view, _key = path.navigate_value(root_view, value_path)
        return parent_view

    async def fetch(self, ctx: Context) -> T | Sentinel:
        """Fetch the value from PV storage.

        Navigates through the view hierarchy and reads the value.
        Returns Empty if the value doesn't exist.

        Args:
            ctx: Execution context with root_view access

        Returns:
            The value, or Empty if not found
        """
        value_path = await self.resolve(ctx)
        shape = self.get_root_shape()
        root_view = ctx.get(View, shape=shape)

        try:
            parent_view, key = path.navigate_value(root_view, value_path)
            if isinstance(parent_view, view_traits.Subscriptable):
                val = parent_view[key]
                return val if not isinstance(val, PVEmpty) else EMPTY
            raise TypeError(f"View {parent_view.__class__.__name__} is not subscriptable")
        except (KeyError, IndexError):
            return EMPTY
