"""Virtuals storage substrate refs.

Refs navigate through a view hierarchy to access values stored
in key-value backends via the virtuals library.

Hierarchy:
    everybase.shape.Ref[T]  - document-model base (address/parent/shape)
        |
    Ref[T]                  - virtuals substrate base
    ├── PrimitiveRef[T]     - refs to leaf values (int, str, etc.)
    └── ViewRef[T, V]       - refs to container views (dict, list, set)

Core vocabulary:
    resolve(ctx) -> Path    - build path from parent chain
    fetch(ctx) -> T         - navigate views and extract value

Lazy/eager facets:
    ViewRefs default to lazy. Use .lazy / .eager to switch facet.
    The facet determines how the fetched view behaves on iteration:
    - lazy: values()/items() yield child Views for containers (no extraction)
    - eager: values()/items() extract containers to Python objects
"""

from __future__ import annotations

import copy
from enum import Enum
from logging import getLogger
from typing import Generic, Self, TypeVar

from virtuals import Empty as StorageEmpty
from virtuals.collections import Subscriptable
from virtuals.loc import path
from virtuals.view import View

from everybase import EMPTY, Context, Sentinel
from everybase.shape import Ref


__all__ = [
    "PrimitiveRef",
    "ViewRef",
]


T = TypeVar("T")
ViewT = TypeVar("ViewT", bound="View")

logger = getLogger(__name__)


def _path_to_site(resolved_path: tuple) -> tuple:
    """Extract site (address tuple) from a resolved path.

    Path: ((addr, type), ...) -> Site: (addr, ...)
    """
    return tuple(addr for addr, _ in resolved_path)


def _resolve_root_view(ctx: Context, scope: type, resolved_path: tuple) -> View:
    """Resolve root view from context, passing site and path as predicate data.

    When no predicate bindings exist for (View, scope), this is a fast
    dict lookup. When sharding predicates are bound, site and path are
    passed so predicates can route to the correct storage.
    """
    if not resolved_path:
        return ctx.get(View, scope)
    site = _path_to_site(resolved_path)
    return ctx.get(View, scope, site=site, path=resolved_path)


class Facet(Enum):
    """View facet — lazy (default) or eager."""

    LAZY = "lazy"
    EAGER = "eager"


def _try_build_static_path(ref: Ref) -> tuple | None:
    """Build full path tuple at construction time if all addresses are static.

    Walks the parent chain collecting (raw_address, type_marker) segments.
    Returns None if any address in the chain is dynamic (i.e. a Term)
    or if any ref lacks a type marker (non-virtuals ref in the chain).
    """
    segments: list[tuple] = []
    current: Ref | None = ref
    while current is not None:
        raw = current._raw_address  # type: ignore[attr-defined]
        if raw is None:
            return None  # Dynamic address — cannot pre-compute
        marker = getattr(current, "_type_marker", None)
        if marker is None:
            return None  # Non-virtuals ref in chain — bail out
        segments.append((raw, marker))
        current = current.parent
    return tuple(reversed(segments))


class ViewRef(Generic[T, ViewT], Ref[T]):  # noqa: UP046
    """Virtuals ref to a container view.

    Used for collection types like dict, list, set views.
    fetch() navigates to and returns the view itself.

    Supports lazy/eager facets (default: lazy).
    Use .lazy / .eager to switch facet before calling iteration methods.
    """

    _facet: Facet = Facet.LAZY

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
    def lazy(self) -> Self:
        """Return lazy-faceted ref. Lazy is default — no-op if already lazy."""
        if self._facet is Facet.LAZY:
            return self
        clone = copy.copy(self)
        clone._facet = Facet.LAZY
        return clone

    @property
    def eager(self) -> Self:
        """Return eager-faceted ref. Iteration extracts containers to Python objects."""
        if self._facet is Facet.EAGER:
            return self
        clone = copy.copy(self)
        clone._facet = Facet.EAGER
        return clone

    @property
    def view_type(self) -> type[ViewT]:
        """The View class type at this location."""
        return self._view_type

    @property
    def _type_marker(self) -> type:
        return self._view_type

    def _apply_facet(self, view: ViewT) -> ViewT:
        """Apply lazy/eager facet to a view if it supports facets."""
        if self._facet is Facet.EAGER and hasattr(view, "eager"):
            return view.eager  # type: ignore[return-value]
        if self._facet is Facet.LAZY and hasattr(view, "lazy"):
            return view.lazy  # type: ignore[return-value]
        return view

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
        view_path = await self.resolve(ctx)
        root_view = _resolve_root_view(ctx, self._root_shape, view_path)
        parent = self.parent
        if parent is None:
            return root_view
        return await parent.fetch(ctx)

    async def fetch(self, ctx: Context) -> ViewT | Sentinel:
        """Fetch the view from virtuals storage.

        Navigates through the view hierarchy to get this view.
        Applies lazy/eager facet to the returned view.

        Args:
            ctx: Execution context with root_view access

        Returns:
            The faceted view instance
        """
        view_path = await self.resolve(ctx)
        root_view = _resolve_root_view(ctx, self._root_shape, view_path)

        if not view_path:
            return self._apply_facet(root_view)  # type: ignore

        view = path.navigate_view(root_view, view_path)
        return self._apply_facet(view)  # type: ignore


class PrimitiveRef[T](Ref[T]):
    """Virtuals ref to a primitive/leaf value.

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
        root_view = _resolve_root_view(ctx, self._root_shape, value_path)
        parent_view, _key = path.navigate_value(root_view, value_path)
        return parent_view

    async def fetch(self, ctx: Context) -> T | Sentinel:
        """Fetch the value from virtuals storage.

        Navigates through the view hierarchy and reads the value.
        Returns Empty if the value doesn't exist.

        Args:
            ctx: Execution context with root_view access

        Returns:
            The value, or Empty if not found
        """
        value_path = await self.resolve(ctx)
        root_view = _resolve_root_view(ctx, self._root_shape, value_path)

        try:
            parent_view, key = path.navigate_value(root_view, value_path)
            if isinstance(parent_view, Subscriptable):
                val = parent_view[key]
                if isinstance(val, StorageEmpty):
                    return EMPTY
                return self.coerce(val)
            raise TypeError(f"View {parent_view.__class__.__name__} is not subscriptable")
        except (KeyError, IndexError):
            return EMPTY
