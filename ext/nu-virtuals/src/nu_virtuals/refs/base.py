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
from typing import TYPE_CHECKING, ClassVar, Generic, Self, TypeVar

from nu import EMPTY, Context, Sentinel
from nu.shapes import Ref
from nu.terms import Mode
from nu_virtuals.paths import ViewPathSer
from virtuals import Empty as StorageEmpty
from virtuals import Navigator
from virtuals.collections import Subscriptable
from virtuals.tkv.storage import SnapshotProtocol, TransactionProtocol


if TYPE_CHECKING:
    from virtuals.loc import path
    from virtuals.view import View


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


def _resolve_navigator(ctx: Context, scope: type, resolved_path: tuple) -> Navigator:
    """Resolve Navigator from context, passing site and path for predicate routing."""
    if not resolved_path:
        return ctx.get(Navigator, scope)
    site = _path_to_site(resolved_path)
    return ctx.get(Navigator, scope, site=site, path=resolved_path)


def _resolve_ctx(ctx: Context, scope: type, resolved_path: tuple) -> object:
    """Resolve storage context (transaction/snapshot) from context."""
    if not resolved_path:
        try:
            return ctx.get(TransactionProtocol, scope)
        except (KeyError, LookupError):
            return ctx.get(SnapshotProtocol, scope)
    site = _path_to_site(resolved_path)
    try:
        return ctx.get(TransactionProtocol, scope, site=site, path=resolved_path)
    except (KeyError, LookupError):
        return ctx.get(SnapshotProtocol, scope, site=site, path=resolved_path)


class Facet(Enum):
    """View facet — none (default), lazy, or eager."""

    NONE = "none"
    LAZY = "lazy"
    EAGER = "eager"


def _try_build_static_path(ref: Ref) -> tuple | None:
    """Build full path tuple at construction time if all addresses are static.

    Walks the parent chain collecting (raw_address, type_marker) segments.
    Returns None if any address in the chain is dynamic (i.e. a Nu)
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

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})
    _facet: Facet = Facet.NONE

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

    async def aresolve(self, ctx: Context) -> path.PathToView:
        """Build path from parent chain ending at this view.

        Args:
            ctx: Execution context

        Returns:
            Path tuple ending with (address, view_type)
        """
        if self._static_path is not None:
            return self._static_path

        address = await self.aresolve_address(ctx)

        parent = self.parent
        if parent is None:
            resolved_path = ((address, self._view_type),)
        else:
            parent_path = await parent.aresolve(ctx)
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

    def resolve(self, ctx: Context) -> path.PathToView:
        """Sync counterpart of `aresolve`."""
        if self._static_path is not None:
            return self._static_path

        address = self.resolve_address(ctx)

        parent = self.parent
        if parent is None:
            resolved_path = ((address, self._view_type),)
        else:
            parent_path = parent.resolve(ctx)
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

    async def afetch_parent(self, ctx: Context) -> object:
        """Fetch the parent container of this view.

        Returns:
            The parent view, or root view if this is a top-level ref.
        """
        view_path = await self.aresolve(ctx)
        nav = _resolve_navigator(ctx, self._root_shape, view_path)
        storage_ctx = _resolve_ctx(ctx, self._root_shape, view_path)

        if not view_path or len(view_path) <= 1:
            return nav.root(storage_ctx)

        parent_path = view_path[:-1]
        return nav.open_at_path(ViewPathSer(parent_path), storage_ctx)

    def fetch_parent(self, ctx: Context) -> object:
        """Sync counterpart of `afetch_parent`."""
        view_path = self.resolve(ctx)
        nav = _resolve_navigator(ctx, self._root_shape, view_path)
        storage_ctx = _resolve_ctx(ctx, self._root_shape, view_path)

        if not view_path or len(view_path) <= 1:
            return nav.root(storage_ctx)

        parent_path = view_path[:-1]
        return nav.open_at_path(ViewPathSer(parent_path), storage_ctx)

    async def afetch(self, ctx: Context) -> ViewT | Sentinel:
        """Fetch the view from virtuals storage.

        Navigates through Navigator for proxy-transparent resolution.
        Applies lazy/eager facet to the returned view.

        Args:
            ctx: Execution context

        Returns:
            The faceted view instance
        """
        view_path = await self.aresolve(ctx)
        nav = _resolve_navigator(ctx, self._root_shape, view_path)
        storage_ctx = _resolve_ctx(ctx, self._root_shape, view_path)

        if not view_path:
            return self._apply_facet(nav.root(storage_ctx))  # type: ignore

        view = nav.open_at_path(ViewPathSer(view_path), storage_ctx)
        return self._apply_facet(view)  # type: ignore

    def fetch(self, ctx: Context) -> ViewT | Sentinel:
        """Sync counterpart of `afetch`."""
        view_path = self.resolve(ctx)
        nav = _resolve_navigator(ctx, self._root_shape, view_path)
        storage_ctx = _resolve_ctx(ctx, self._root_shape, view_path)

        if not view_path:
            return self._apply_facet(nav.root(storage_ctx))  # type: ignore

        view = nav.open_at_path(ViewPathSer(view_path), storage_ctx)
        return self._apply_facet(view)  # type: ignore


class PrimitiveRef[T](Ref[T]):
    """Virtuals ref to a primitive/leaf value.

    Used for scalar values like int, str, float, etc.
    fetch() navigates to the parent view and subscripts to get the value.
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

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

    async def aresolve(self, ctx: Context) -> path.PathToValue:
        """Build path from parent chain ending at this value.

        Args:
            ctx: Execution context

        Returns:
            Path tuple ending with (address, value_type)
        """
        if self._static_path is not None:
            return self._static_path  # type: ignore

        address = await self.aresolve_address(ctx)

        parent = self.parent
        if parent is None:
            resolved_path = ((address, self._value_type),)
        else:
            parent_path = await parent.aresolve(ctx)
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

    def resolve(self, ctx: Context) -> path.PathToValue:
        """Sync counterpart of `aresolve`."""
        if self._static_path is not None:
            return self._static_path  # type: ignore

        address = self.resolve_address(ctx)

        parent = self.parent
        if parent is None:
            resolved_path = ((address, self._value_type),)
        else:
            parent_path = parent.resolve(ctx)
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

    async def afetch_parent(self, ctx: Context) -> object:
        """Fetch the parent collection (view) for item access.

        Navigates through Navigator and returns the parent view
        that contains this primitive value.

        Args:
            ctx: Execution context

        Returns:
            The parent view object
        """
        value_path = await self.aresolve(ctx)
        nav = _resolve_navigator(ctx, self._root_shape, value_path)
        storage_ctx = _resolve_ctx(ctx, self._root_shape, value_path)

        parent_path = value_path[:-1]
        if not parent_path:
            return nav.root(storage_ctx)
        return nav.open_at_path(ViewPathSer(parent_path), storage_ctx)

    def fetch_parent(self, ctx: Context) -> object:
        """Sync counterpart of `afetch_parent`."""
        value_path = self.resolve(ctx)
        nav = _resolve_navigator(ctx, self._root_shape, value_path)
        storage_ctx = _resolve_ctx(ctx, self._root_shape, value_path)

        parent_path = value_path[:-1]
        if not parent_path:
            return nav.root(storage_ctx)
        return nav.open_at_path(ViewPathSer(parent_path), storage_ctx)

    async def afetch(self, ctx: Context) -> T | Sentinel:
        """Fetch the value from virtuals storage.

        Navigates through Navigator and reads the value.
        Returns Empty if the value doesn't exist.

        Args:
            ctx: Execution context

        Returns:
            The value, or Empty if not found
        """
        value_path = await self.aresolve(ctx)
        nav = _resolve_navigator(ctx, self._root_shape, value_path)
        storage_ctx = _resolve_ctx(ctx, self._root_shape, value_path)

        parent_path = value_path[:-1]
        key = value_path[-1][0]

        try:
            if not parent_path:
                parent_view = nav.root(storage_ctx)
            else:
                parent_view = nav.open_at_path(ViewPathSer(parent_path), storage_ctx)
            if isinstance(parent_view, Subscriptable):
                val = parent_view[key]
                if isinstance(val, StorageEmpty):
                    return EMPTY
                return self.coerce(val)
            raise TypeError(f"View {parent_view.__class__.__name__} is not subscriptable")
        except (KeyError, IndexError):
            return EMPTY

    def fetch(self, ctx: Context) -> T | Sentinel:
        """Sync counterpart of `afetch`."""
        value_path = self.resolve(ctx)
        nav = _resolve_navigator(ctx, self._root_shape, value_path)
        storage_ctx = _resolve_ctx(ctx, self._root_shape, value_path)

        parent_path = value_path[:-1]
        key = value_path[-1][0]

        try:
            if not parent_path:
                parent_view = nav.root(storage_ctx)
            else:
                parent_view = nav.open_at_path(ViewPathSer(parent_path), storage_ctx)
            if isinstance(parent_view, Subscriptable):
                val = parent_view[key]
                if isinstance(val, StorageEmpty):
                    return EMPTY
                return self.coerce(val)
            raise TypeError(f"View {parent_view.__class__.__name__} is not subscriptable")
        except (KeyError, IndexError):
            return EMPTY
