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
from typing import Generic, TypeVar

import pv.traits as view_traits
from pv import Empty as PVEmpty
from pv.loc import path
from pv.view import View

from everybase import EMPTY, Context, Sentinel
from everyshape import Ref


__all__ = [
    "PrimitiveRef",
    "ViewRef",
]


T = TypeVar("T")
ViewT = TypeVar("ViewT", bound="View")

logger = getLogger(__name__)


def _try_build_static_path(ref: Ref) -> tuple | None:
    """Build full path tuple at construction time if all addresses are static.

    Walks the parent chain collecting (raw_address, type_marker) segments.
    Returns None if any address in the chain is dynamic (i.e. a Term)
    or if any ref lacks a type marker (non-PV ref in the chain).
    """
    segments: list[tuple] = []
    current: Ref | None = ref
    while current is not None:
        raw = current._raw_address  # type: ignore[attr-defined]
        if raw is None:
            return None  # Dynamic address — cannot pre-compute
        marker = getattr(current, "_type_marker", None)
        if marker is None:
            return None  # Non-PV ref in chain — bail out
        segments.append((raw, marker))
        current = current.parent
    return tuple(reversed(segments))


class ViewRef(Generic[T, ViewT], Ref[T]):  # noqa: UP046
    """PV ref to a container view.

    Used for collection types like dict, list, set views.
    fetch() navigates to and returns the view itself.
    """

    def __init__(
        self,
        *,
        view_type: type[ViewT],
        **kwargs: object,
    ) -> None:
        """Initialize view ref.

        Args:
            view_type: The View class type
            **kwargs: Passed to super (address, parent, owner_shape, etc.)
        """
        super().__init__(**kwargs)
        self._view_type = view_type
        self._static_path = _try_build_static_path(self)

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
        if self._static_path is not None:
            return self._static_path

        address = await self.resolve_address(ctx)

        parent = self.parent
        if parent is None:
            resolved_path = ((address, self._view_type),)
        else:
            parent_path = await parent.resolve(ctx)
            resolved_path = (*parent_path, (address, self._view_type))

        logger.debug(
            "ViewRef resolved",
            extra={
                "address": address,
                "view_type": self._view_type.__name__,
                "has_parent": parent is not None,
                "resolved_path": resolved_path,
            },
        )
        return resolved_path

    async def fetch_parent(self, ctx: Context) -> object:
        """Fetch the parent container of this view.

        Returns:
            The parent view, or root view if this is a top-level ref.
        """
        scope = self._root_shape
        root_view = ctx[View, scope]
        parent = self.parent
        if parent is None:
            return root_view
        return await parent.fetch(ctx)

    async def fetch(self, ctx: Context) -> ViewT | Sentinel:
        """Fetch the view from PV storage.

        Navigates through the view hierarchy to get this view.

        Args:
            ctx: Execution context with root_view access

        Returns:
            The view instance
        """
        view_path = await self.resolve(ctx)
        scope = self._root_shape
        root_view = ctx[View, scope]

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
        *,
        value_type: type[T],
        **kwargs: object,
    ) -> None:
        """Initialize primitive ref.

        Args:
            value_type: The Python type of the value
            **kwargs: Passed to super (address, parent, owner_shape, etc.)
        """
        super().__init__(**kwargs)
        self._value_type = value_type
        self._static_path = _try_build_static_path(self)

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
        if self._static_path is not None:
            return self._static_path  # type: ignore

        address = await self.resolve_address(ctx)

        parent = self.parent
        if parent is None:
            resolved_path = ((address, self._value_type),)
        else:
            parent_path = await parent.resolve(ctx)
            resolved_path = (*parent_path, (address, self._value_type))

        logger.debug(
            "PrimitiveRef resolved",
            extra={
                "address": address,
                "value_type": self._value_type.__name__,
                "has_parent": parent is not None,
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
        scope = self._root_shape
        root_view = ctx[View, scope]
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
        scope = self._root_shape
        root_view = ctx[View, scope]

        try:
            parent_view, key = path.navigate_value(root_view, value_path)
            if isinstance(parent_view, view_traits.Subscriptable):
                val = parent_view[key]
                return val if not isinstance(val, PVEmpty) else EMPTY
            raise TypeError(f"View {parent_view.__class__.__name__} is not subscriptable")
        except (KeyError, IndexError):
            return EMPTY
