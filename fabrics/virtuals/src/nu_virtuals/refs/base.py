"""Virtuals storage substrate refs — navigate the virtuals View hierarchy.

``ViewRef`` and ``PrimitiveRef`` are the two concrete substrates against the
shape Ref seam (``_StructuredRef``): they fill the plug-points with virtuals
View navigation, backed by a tkv snapshot / transaction resolved from the
Context.

A ref names one path segment — its address, held as ``children[0]`` and
resolved through the runtime like any child. The parent chain (``_parent_ref``)
supplies the segments above it; for the common shape-field case those are static
slot names, read off each parent's stored ``(_segment, _type_marker)`` at compile
time. The Navigator + storage context (snapshot/transaction) come from the
Context under ``(Navigator, root_shape)`` / ``(TransactionProtocol|SnapshotProtocol,
root_shape)`` and are resolved with predicate routing (site + path).

Read is the Ref's dual role:
- ``ViewRef.compile`` returns the navigate-and-fetch-the-view thunk (faceted
  lazy / eager), so collection ops run against a live virtuals View.
- ``PrimitiveRef.compile`` navigates to the parent View and subscripts the leaf.

``write`` / ``erase`` resolve the address and mutate through the parent View
(``parent[addr] = value`` / ``del parent[addr]``), which the virtuals library
decomposes / cleans up.
"""

from __future__ import annotations

import copy
from enum import Enum
from logging import getLogger
from typing import TYPE_CHECKING

from nu import EMPTY
from nu.domains.shape.refs.base import _StructuredRef
from nu_virtuals.paths import ViewPathSer
from virtuals import Empty as StorageEmpty
from virtuals import Navigator
from virtuals.collections import Subscriptable
from virtuals.tkv.storage import SnapshotProtocol, TransactionProtocol


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.domains.shape.dsl import Shape
    from nu.lang.runtime import Runtime
    from virtuals.view import View


__all__ = [
    "Facet",
    "PrimitiveRef",
    "ViewRef",
]


logger = getLogger(__name__)


class Facet(Enum):
    """View facet — none (default), lazy, or eager."""

    NONE = "none"
    LAZY = "lazy"
    EAGER = "eager"


def _resolve_navigator(rt: Runtime, scope: type | None, resolved_path: tuple) -> Navigator:
    """Resolve Navigator from the runtime ctx, passing site and path for routing."""
    if not resolved_path:
        return rt.ctx.get(Navigator, scope) if scope is not None else rt.ctx.get(Navigator)
    site = tuple(addr for addr, _ in resolved_path)
    if scope is not None:
        return rt.ctx.get(Navigator, scope, site=site, path=resolved_path)
    return rt.ctx.get(Navigator, site=site, path=resolved_path)


def _resolve_storage_ctx(rt: Runtime, scope: type | None, resolved_path: tuple) -> object:
    """Resolve storage context (transaction / snapshot) from the runtime ctx."""
    tags = (scope,) if scope is not None else ()
    if not resolved_path:
        try:
            return rt.ctx.get(TransactionProtocol, *tags)
        except (KeyError, LookupError):
            return rt.ctx.get(SnapshotProtocol, *tags)
    site = tuple(addr for addr, _ in resolved_path)
    try:
        return rt.ctx.get(TransactionProtocol, *tags, site=site, path=resolved_path)
    except (KeyError, LookupError):
        return rt.ctx.get(SnapshotProtocol, *tags, site=site, path=resolved_path)


class _VirtualsRefBase[T](_StructuredRef):
    """Shared virtuals navigation: path building off the parent chain + Navigator.

    Each ref stores its raw static address as ``_segment`` and its type marker
    as ``_type_marker`` (a View subclass for containers, a Python type for
    leaves). The full path is ``((addr, marker), ...)`` root-first.
    """

    _type_marker: type

    def __init__(
        self,
        address: object,
        *,
        parent_ref: _VirtualsRefBase | None = None,
        owner_shape: type[Shape] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape, **kwargs)
        self._segment = address  # raw static segment, for parent-chain path building

    # --- path building -------------------------------------------------------

    def _parent_segments(self) -> tuple[tuple[object, type], ...]:
        """Static ``(addr, marker)`` segments of the parent chain, root-first."""
        segs: list[tuple[object, type]] = []
        ref = self._parent_ref
        while ref is not None:
            segs.append((ref._segment, ref._type_marker))  # type: ignore[attr-defined]
            ref = ref._parent_ref
        segs.reverse()
        return tuple(segs)

    def _resolve_path(self, rt: Runtime, nid: int) -> tuple[tuple[object, type], ...]:
        """Full ``(addr, marker)`` path for this ref, resolving own dynamic address."""
        address = self.address(rt, nid)
        return (*self._parent_segments(), (address, self._type_marker))

    async def _aresolve_path(self, rt: Runtime, nid: int) -> tuple[tuple[object, type], ...]:
        """Async sibling of :meth:`_resolve_path`."""
        address = await self.aaddress(rt, nid)
        return (*self._parent_segments(), (address, self._type_marker))


class ViewRef[T](_VirtualsRefBase[T]):
    """Virtuals ref to a container view (dict / list / set / shape).

    ``compile`` navigates to and returns the faceted View itself, so the
    collection ops (keys/values/items/get/append/add/...) run against the live
    virtuals View. Supports lazy/eager facets (default: lazy).
    """

    _facet: Facet = Facet.LAZY

    def __init__(
        self,
        address: object,
        *,
        view_type: type[View] | None = None,
        parent_ref: _VirtualsRefBase | None = None,
        owner_shape: type[Shape] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape, **kwargs)
        # ``view_type`` may be None when the shape-blueprint __init__ routes
        # through here without threading it; the concrete shape ref then sets
        # ``_view_type`` itself right after super().__init__.
        if view_type is not None:
            self._view_type = view_type

    @property
    def view_type(self) -> type[View]:
        """The View class type at this location."""
        return self._view_type

    @property
    def _type_marker(self) -> type:  # type: ignore[override]
        return self._view_type

    @property
    def lazy(self) -> ViewRef[T]:
        """Return a lazy-faceted clone. No-op if already lazy."""
        if self._facet is Facet.LAZY:
            return self
        clone = copy.copy(self)
        clone._facet = Facet.LAZY
        return clone

    @property
    def eager(self) -> ViewRef[T]:
        """Return an eager-faceted clone. Iteration extracts to Python objects."""
        if self._facet is Facet.EAGER:
            return self
        clone = copy.copy(self)
        clone._facet = Facet.EAGER
        return clone

    def _apply_facet(self, view: object) -> object:
        """Apply the lazy/eager facet to a fetched view, when supported."""
        if self._facet is Facet.EAGER and hasattr(view, "eager"):
            return view.eager
        if self._facet is Facet.LAZY and hasattr(view, "lazy"):
            return view.lazy
        return view

    # --- read (the dual role) ------------------------------------------------

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        scope = self.get_root_shape()

        def thunk(rt: Runtime) -> object:
            path = self._resolve_path(rt, nid)
            nav = _resolve_navigator(rt, scope, path)
            storage_ctx = _resolve_storage_ctx(rt, scope, path)
            view = nav.open_at_path(ViewPathSer(path), storage_ctx)
            return self._apply_facet(view)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        scope = self.get_root_shape()

        async def athunk(rt: Runtime) -> object:
            path = await self._aresolve_path(rt, nid)
            nav = _resolve_navigator(rt, scope, path)
            storage_ctx = _resolve_storage_ctx(rt, scope, path)
            view = nav.open_at_path(ViewPathSer(path), storage_ctx)
            return self._apply_facet(view)

        return athunk

    # --- write / erase (whole-view store via parent decomposition) -----------

    def _fetch_parent_view(self, rt: Runtime, path: tuple) -> object:
        nav = _resolve_navigator(rt, self.get_root_shape(), path)
        storage_ctx = _resolve_storage_ctx(rt, self.get_root_shape(), path)
        if len(path) <= 1:
            return nav.root(storage_ctx)
        return nav.open_at_path(ViewPathSer(path[:-1]), storage_ctx)

    def write(self, rt: Runtime, value: object, nid: int) -> None:
        """Store a whole container value through the parent View (decomposed)."""
        path = self._resolve_path(rt, nid)
        parent = self._fetch_parent_view(rt, path)
        parent[path[-1][0]] = value  # type: ignore[index]

    async def awrite(self, rt: Runtime, value: object, nid: int) -> None:
        """Async sibling of :meth:`write`."""
        path = await self._aresolve_path(rt, nid)
        parent = self._fetch_parent_view(rt, path)
        parent[path[-1][0]] = value  # type: ignore[index]

    def erase(self, rt: Runtime, nid: int) -> None:
        """Remove this ref's slot from its parent View, if present."""
        path = self._resolve_path(rt, nid)
        parent = self._fetch_parent_view(rt, path)
        key = path[-1][0]
        try:
            del parent[key]  # type: ignore[attr-defined]
        except (KeyError, IndexError):
            pass

    async def aerase(self, rt: Runtime, nid: int) -> None:
        """Async sibling of :meth:`erase`."""
        path = await self._aresolve_path(rt, nid)
        parent = self._fetch_parent_view(rt, path)
        key = path[-1][0]
        try:
            del parent[key]  # type: ignore[attr-defined]
        except (KeyError, IndexError):
            pass

    # --- substrate plug-points (for unsafe ops / EnsureLayout) ---------------

    def fetch(self, rt: Runtime, nid: int) -> object:
        """Navigate to and return the faceted View (sync)."""
        return self.compile(nid, ())(rt)

    async def afetch(self, rt: Runtime, nid: int) -> object:
        """Async sibling of :meth:`fetch`."""
        return await self.acompile(nid, ())(rt)


class PrimitiveRef[T](_VirtualsRefBase[T]):
    """Virtuals ref to a primitive / leaf value.

    ``compile`` navigates to the parent View and subscripts to read the value;
    ``write`` / ``erase`` mutate the parent View at this leaf's address.
    """

    def __init__(
        self,
        address: object,
        *,
        value_type: type[T],
        parent_ref: _VirtualsRefBase | None = None,
        owner_shape: type[Shape] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape, **kwargs)
        self._value_type = value_type

    @property
    def value_type(self) -> type[T]:
        """The Python type of the value at this location."""
        return self._value_type

    @property
    def _type_marker(self) -> type:  # type: ignore[override]
        return self._value_type

    # --- read (the dual role) ------------------------------------------------

    def _read(self, rt: Runtime, path: tuple) -> object:
        nav = _resolve_navigator(rt, self.get_root_shape(), path)
        storage_ctx = _resolve_storage_ctx(rt, self.get_root_shape(), path)
        parent_path = path[:-1]
        key = path[-1][0]
        try:
            parent_view = nav.root(storage_ctx) if not parent_path else nav.open_at_path(
                ViewPathSer(parent_path), storage_ctx
            )
            if isinstance(parent_view, Subscriptable):
                val = parent_view[key]
                if isinstance(val, StorageEmpty):
                    return EMPTY
                return self.coerce(val)
            msg = f"View {parent_view.__class__.__name__} is not subscriptable"
            raise TypeError(msg)
        except (KeyError, IndexError):
            return EMPTY

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            return self._read(rt, self._resolve_path(rt, nid))

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            return self._read(rt, await self._aresolve_path(rt, nid))

        return athunk

    # --- write / erase -------------------------------------------------------

    def _fetch_parent_view(self, rt: Runtime, path: tuple) -> object:
        nav = _resolve_navigator(rt, self.get_root_shape(), path)
        storage_ctx = _resolve_storage_ctx(rt, self.get_root_shape(), path)
        parent_path = path[:-1]
        if not parent_path:
            return nav.root(storage_ctx)
        return nav.open_at_path(ViewPathSer(parent_path), storage_ctx)

    def write(self, rt: Runtime, value: object, nid: int) -> None:
        """Write a leaf value through the parent View."""
        path = self._resolve_path(rt, nid)
        parent = self._fetch_parent_view(rt, path)
        parent[path[-1][0]] = value  # type: ignore[index]

    async def awrite(self, rt: Runtime, value: object, nid: int) -> None:
        """Async sibling of :meth:`write`."""
        path = await self._aresolve_path(rt, nid)
        parent = self._fetch_parent_view(rt, path)
        parent[path[-1][0]] = value  # type: ignore[index]

    def erase(self, rt: Runtime, nid: int) -> None:
        """Remove this ref's leaf from its parent View, if present."""
        path = self._resolve_path(rt, nid)
        parent = self._fetch_parent_view(rt, path)
        key = path[-1][0]
        try:
            del parent[key]  # type: ignore[attr-defined]
        except (KeyError, IndexError):
            pass

    async def aerase(self, rt: Runtime, nid: int) -> None:
        """Async sibling of :meth:`erase`."""
        path = await self._aresolve_path(rt, nid)
        parent = self._fetch_parent_view(rt, path)
        key = path[-1][0]
        try:
            del parent[key]  # type: ignore[attr-defined]
        except (KeyError, IndexError):
            pass
