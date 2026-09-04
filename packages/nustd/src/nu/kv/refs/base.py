"""Virtuals storage substrate refs: navigate the virtuals View hierarchy.

``ViewRef`` and ``PrimitiveRef`` are the two concrete substrates against the
shape Ref seam (``StructuredRef``): they fill the plug-points with virtuals
View navigation, backed by a tkv snapshot / transaction resolved from the
Context.

A ref names one path segment: its address, held as ``children[1]`` and
resolved through the runtime like any child. The parent chain lives on the tree
at ``children[0]`` (walked via ``parent_ref``); for the common shape-field case
those are static slot names, read off each parent's stored ``(_segment,
_type_marker)`` at compile time. The Navigator + storage context (snapshot/transaction) come from the
Context under ``(Navigator, root_shape)`` / ``(TransactionProtocol|SnapshotProtocol,
root_shape)`` and are resolved with predicate routing (site + path).

Read is the Ref's dual role:
- ``ViewRef._compile`` returns the navigate-and-fetch-the-view thunk (faceted
  lazy / eager), so collection ops run against a live virtuals View.
- ``PrimitiveRef._compile`` navigates to the parent View and subscripts the leaf.

``write`` / ``erase`` resolve the address and mutate through the parent View
(``parent[addr] = value`` / ``del parent[addr]``), which the virtuals library
decomposes / cleans up.
"""

from __future__ import annotations

from enum import Enum
from logging import getLogger
from typing import TYPE_CHECKING, Generic, TypeVar

from nu.domains.shape.refs.base import StructuredRef
from nu.kv.paths import ViewPathSer
from nu.lang import EMPTY
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


T = TypeVar("T")


class Facet(Enum):
    """How a fetched View hands its contents back: unfaceted, lazy, or eager.

    NONE returns the View as the Navigator opened it. A ViewRef with no facet
    on its payload reads as LAZY, so LAZY is the effective default.
    """

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


class _VirtualsRefBase(StructuredRef, Generic[T]):
    """Shared virtuals navigation: path building off the parent chain + Navigator.

    Each ref stores its raw static address in payload as ``"segment"`` and its
    type marker as ``"type_marker"`` (a View subclass for containers, a Python
    type for leaves). The full path is ``((addr, marker), ...)`` root-first.
    """

    def __init__(
        self,
        address: object,
        *,
        parent_ref: _VirtualsRefBase | None = None,
        owner_shape: type[Shape] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape, **kwargs)
        # raw static segment, in payload so it rides base with_children
        self._payload["segment"] = address

    # --- path building -------------------------------------------------------

    def _resolve_path(self, rt: Runtime, nid: int) -> tuple[tuple[object, type], ...]:
        """Full ``(addr, marker)`` path, root-first, resolving every level at runtime.

        Walks the on-tree parent chain via ``rt.program.children`` (``[0]`` =
        structural parent, ``[1]`` = this level's address), evaluating each
        level's address child and reading its ``"type_marker"`` off the term
        payload. Because the parent lives on the tree, a *dynamic* parent key
        resolves here like any other child - no static-segment shortcut needed.
        """
        segs: list[tuple[object, type]] = []
        cur = nid
        while True:
            kids = rt.program.children[cur]
            term = rt.program.terms[cur]
            segs.append((rt.eval(kids[1]), term._payload["type_marker"]))  # type: ignore[attr-defined]
            parent = kids[0]
            if not isinstance(rt.program.terms[parent], StructuredRef):
                break  # parent is the ANCHOR -> chain root
            cur = parent
        segs.reverse()
        return tuple(segs)

    async def _aresolve_path(self, rt: Runtime, nid: int) -> tuple[tuple[object, type], ...]:
        """Async sibling of :meth:`_resolve_path`."""
        segs: list[tuple[object, type]] = []
        cur = nid
        while True:
            kids = rt.program.children[cur]
            term = rt.program.terms[cur]
            segs.append((await rt.aeval(kids[1]), term._payload["type_marker"]))  # type: ignore[attr-defined]
            parent = kids[0]
            if not isinstance(rt.program.terms[parent], StructuredRef):
                break
            cur = parent
        segs.reverse()
        return tuple(segs)


class ViewRef(_VirtualsRefBase[T], Generic[T]):
    """A ref to one container slot in KV storage, read as a live virtuals View.

    Evaluating it navigates to its path and hands back the View itself, not a
    copy, so every container op written on the ref (``keys``, ``append``,
    ``add``, ``len``, ...) runs against storage rather than against a
    materialized Python value.

    The path is the parent chain: each level contributes an address that is a
    child on the tree and is evaluated at run time, so a key may be a literal,
    a computed expression, or a ref from another fabric. The Navigator and the
    storage context are pulled from the Context under the ref's root shape,
    with the resolved path passed along so a binding can route on it.

    Notes:
        - Read and write take different doors: reads open the path as-is,
          while a write materializes every ancestor first, so writing deep
          into never-touched storage creates the whole chain.
        - A whole-container write stores through the parent with the ref's
          own declared view class, so a slot declared as Kh57View keeps that
          layout instead of collapsing onto the container layer's default.
        - Erasing a slot that is not there is a no-op, not an error.
        - Never yields EMPTY: an unwritten path opens as an empty View, which
          reads as length zero.
        - The storage context is a transaction when one is bound, otherwise a
          snapshot; a snapshot is read-only, so writes need the transaction.

    Example:
        class Portfolio(Shape):
            tags = ListRef.slot(str)
        run(Portfolio.tags.append("core"), ctx)
        run(Portfolio.tags.len(), ctx)
    """

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
        # ``payload["type_marker"]`` itself right after super().__init__.
        if view_type is not None:
            self._payload["type_marker"] = view_type

    def _with_facet(self, facet: Facet) -> ViewRef[T]:
        """A faceted variant: same tree, fresh payload with the facet overridden."""
        variant = object.__new__(type(self))
        variant._children = self._children
        variant._payload = {**self._payload, "facet": facet}
        return variant

    @property
    def lazy(self) -> ViewRef[T]:
        """The same ref read lazily: nested containers stay Views.

        Notes:
            - Already the default, so this is only worth writing to undo an
              eager facet picked up earlier in a chain.
            - Returns the ref unchanged when it is already lazy.
        """
        return (
            self
            if self._payload.get("facet", Facet.LAZY) is Facet.LAZY
            else self._with_facet(Facet.LAZY)
        )

    @property
    def eager(self) -> ViewRef[T]:
        """The same ref read eagerly: reads extract to plain Python values.

        Notes:
            - Nested containers come back extracted rather than as child
              Views, so the whole subtree is read out of storage.
            - The facet rides the ref's payload, so it applies to the ops
              written on it, not to the refs descended from it.
            - Returns the ref unchanged when it is already eager, and leaves
              the view alone when its type has no eager facet.
        """
        return (
            self
            if self._payload.get("facet", Facet.LAZY) is Facet.EAGER
            else self._with_facet(Facet.EAGER)
        )

    def _apply_facet(self, view: object) -> object:
        """Apply the lazy/eager facet to a fetched view, when supported.

        Support is checked against the ref's declared ``type_marker`` (a View
        subclass), not the fetched instance. Instance ``hasattr`` on a remote
        proxy triggers an RPC round-trip per read and logs an AttributeError
        on the server for every view type without the facet (SetView, etc).
        """
        facet = self._payload.get("facet", Facet.LAZY)
        if facet is Facet.NONE:
            return view
        view_type = self._payload.get("type_marker")
        probe: object = view_type if view_type is not None else view
        if facet is Facet.EAGER and hasattr(probe, "eager"):
            return view.eager
        if facet is Facet.LAZY and hasattr(probe, "lazy"):
            return view.lazy
        return view

    # --- read (the dual role) ------------------------------------------------

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        scope = self._root_shape

        def thunk(rt: Runtime) -> object:
            path = self._resolve_path(rt, nid)
            nav = _resolve_navigator(rt, scope, path)
            storage_ctx = _resolve_storage_ctx(rt, scope, path)
            view = nav.open_at_path(ViewPathSer(path), storage_ctx)
            return self._apply_facet(view)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        scope = self._root_shape

        async def athunk(rt: Runtime) -> object:
            path = await self._aresolve_path(rt, nid)
            nav = _resolve_navigator(rt, scope, path)
            storage_ctx = _resolve_storage_ctx(rt, scope, path)
            view = nav.open_at_path(ViewPathSer(path), storage_ctx)
            return self._apply_facet(view)

        return athunk

    # --- write / erase (whole-view store via parent decomposition) -----------

    def _fetch_parent_view(self, rt: Runtime, path: tuple) -> object:
        """Read-side parent open -- pure navigation, no side effects.

        Safe on read-only storage contexts (snapshots, RO secondaries).
        Callers that intend to WRITE via the returned view should use
        ``_fetch_and_ensure_parent_view`` instead so every ancestor along
        the path is materialized with its declared view type before the
        leaf write can auto-create it with the container layer's default
        marker.
        """
        nav = _resolve_navigator(rt, self._root_shape, path)
        storage_ctx = _resolve_storage_ctx(rt, self._root_shape, path)
        if len(path) <= 1:
            return nav.root(storage_ctx)
        return nav.open_at_path(ViewPathSer(path[:-1]), storage_ctx)

    def _fetch_and_ensure_parent_view(self, rt: Runtime, path: tuple) -> object:
        """Write-side parent open.

        Walks the path and ensures each level is materialized with its
        declared view type.

        Same shape as ``_fetch_parent_view`` but uses
        ``open_at_path_and_ensure`` so every intermediate container gets
        stamped with the correct marker (via ``ensure_created`` at each
        level, which also runs ``_ensure_internal_layout`` on views like
        ``LogIndexedDictView`` that carry a custom sub-layout). Only call
        on a write-capable context.
        """
        nav = _resolve_navigator(rt, self._root_shape, path)
        storage_ctx = _resolve_storage_ctx(rt, self._root_shape, path)
        if len(path) <= 1:
            root = nav.root(storage_ctx)
            root.ensure_created()
            return root
        return nav.open_at_path_and_ensure(ViewPathSer(path[:-1]), storage_ctx)

    def _write(self, rt: Runtime, value: object, nid: int) -> None:
        """Store a whole container value through the parent View (decomposed).

        Uses ``set_child_container_as`` so the ref's declared view class
        (``path[-1][1]``) drives the child layout, rather than the parent's
        default type→view registry lookup, which would collapse every
        ``dict``-valued ref onto ``DictView`` regardless of what the slot
        declared (``Kh57View``, ``IndexedDictView``, …).
        """
        value = self._lower(value)
        path = self._resolve_path(rt, nid)
        parent = self._fetch_and_ensure_parent_view(rt, path)
        key, view_class = path[-1]
        parent.set_child_container_as(key, value, view_class)  # type: ignore[attr-defined]

    async def _awrite(self, rt: Runtime, value: object, nid: int) -> None:
        """Async sibling of :meth:`_write`."""
        value = await self._alower(value)
        path = await self._aresolve_path(rt, nid)
        parent = self._fetch_and_ensure_parent_view(rt, path)
        key, view_class = path[-1]
        parent.set_child_container_as(key, value, view_class)  # type: ignore[attr-defined]

    def _erase(self, rt: Runtime, nid: int) -> None:
        """Remove this ref's slot from its parent View, if present."""
        path = self._resolve_path(rt, nid)
        parent = self._fetch_parent_view(rt, path)
        key = path[-1][0]
        try:
            del parent[key]  # type: ignore[attr-defined]
        except (KeyError, IndexError):
            pass

    async def _aerase(self, rt: Runtime, nid: int) -> None:
        """Async sibling of :meth:`erase`."""
        path = await self._aresolve_path(rt, nid)
        parent = self._fetch_parent_view(rt, path)
        key = path[-1][0]
        try:
            del parent[key]  # type: ignore[attr-defined]
        except (KeyError, IndexError):
            pass

    # --- substrate plug-points (for unsafe ops) ------------------------------

    def _fetch(self, rt: Runtime, nid: int) -> object:
        """Navigate to and return the faceted View (sync)."""
        return self._compile(nid, ())(rt)

    async def _afetch(self, rt: Runtime, nid: int) -> object:
        """Async sibling of :meth:`_fetch`."""
        return await self._acompile(nid, ())(rt)


class PrimitiveRef(_VirtualsRefBase[T], Generic[T]):
    """A ref to one leaf value in KV storage, read by subscripting its parent.

    Evaluating it opens the parent container and subscripts it at this leaf's
    address, so what comes back is the stored value rather than a View. The
    path is built the same way as for a container ref: every level's address
    is a child on the tree, resolved at run time.

    Notes:
        - Yields EMPTY when the leaf is absent, when the parent has no such
          key or index, and when storage holds its own empty marker there.
          Reading a missing leaf is not an error.
        - A write materializes every ancestor along the path first, so a leaf
          can be written into storage that has nothing above it yet.
        - Erasing a leaf that is not there is a no-op.
        - A subclass that stores a value in some other form overrides the
          lift-on-read and the write command; the leaf address itself is
          unaffected by that.
        - Carries the parent lookup that primitive change observation needs,
          so a typed leaf ref gets ``on_change`` with no substrate work.

    Example:
        class Portfolio(Shape):
            name = StrRef.slot()
        run(Portfolio.name.set("core"), ctx)
        run(Portfolio.name, ctx)
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
        self._payload["type_marker"] = value_type

    # --- read (the dual role) ------------------------------------------------

    def _read(self, rt: Runtime, path: tuple) -> object:
        nav = _resolve_navigator(rt, self._root_shape, path)
        storage_ctx = _resolve_storage_ctx(rt, self._root_shape, path)
        parent_path = path[:-1]
        key = path[-1][0]
        try:
            parent_view = (
                nav.root(storage_ctx)
                if not parent_path
                else nav.open_at_path(ViewPathSer(parent_path), storage_ctx)
            )
            if isinstance(parent_view, Subscriptable):
                val = parent_view[key]
                if isinstance(val, StorageEmpty):
                    return EMPTY
                return self._lift(val)
            msg = f"View {parent_view.__class__.__name__} is not subscriptable"
            raise TypeError(msg)
        except (KeyError, IndexError):
            return EMPTY

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            return self._read(rt, self._resolve_path(rt, nid))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return self._read(rt, await self._aresolve_path(rt, nid))

        return athunk

    # --- write / erase -------------------------------------------------------

    def _fetch_parent_view(self, rt: Runtime, path: tuple) -> object:
        """Read-side parent open -- pure navigation, no side effects.

        See the sibling method on ``ViewRef`` for the rationale on the
        read/write split.
        """
        nav = _resolve_navigator(rt, self._root_shape, path)
        storage_ctx = _resolve_storage_ctx(rt, self._root_shape, path)
        parent_path = path[:-1]
        if not parent_path:
            return nav.root(storage_ctx)
        return nav.open_at_path(ViewPathSer(parent_path), storage_ctx)

    def _fetch_and_ensure_parent_view(self, rt: Runtime, path: tuple) -> object:
        """Write-side parent open -- ensures each level materializes.

        See the sibling method on ``ViewRef``.
        """
        nav = _resolve_navigator(rt, self._root_shape, path)
        storage_ctx = _resolve_storage_ctx(rt, self._root_shape, path)
        parent_path = path[:-1]
        if not parent_path:
            root = nav.root(storage_ctx)
            root.ensure_created()
            return root
        return nav.open_at_path_and_ensure(ViewPathSer(parent_path), storage_ctx)

    def _write(self, rt: Runtime, value: object, nid: int) -> None:
        """Write a leaf value through the parent View."""
        value = self._lower(value)
        path = self._resolve_path(rt, nid)
        parent = self._fetch_and_ensure_parent_view(rt, path)
        parent[path[-1][0]] = value  # type: ignore[index]

    async def _awrite(self, rt: Runtime, value: object, nid: int) -> None:
        """Async sibling of :meth:`write`."""
        value = await self._alower(value)
        path = await self._aresolve_path(rt, nid)
        parent = self._fetch_and_ensure_parent_view(rt, path)
        parent[path[-1][0]] = value  # type: ignore[index]

    def _erase(self, rt: Runtime, nid: int) -> None:
        """Remove this ref's leaf from its parent View, if present."""
        path = self._resolve_path(rt, nid)
        parent = self._fetch_parent_view(rt, path)
        key = path[-1][0]
        try:
            del parent[key]  # type: ignore[attr-defined]
        except (KeyError, IndexError):
            pass

    async def _aerase(self, rt: Runtime, nid: int) -> None:
        """Async sibling of :meth:`erase`."""
        path = await self._aresolve_path(rt, nid)
        parent = self._fetch_parent_view(rt, path)
        key = path[-1][0]
        try:
            del parent[key]  # type: ignore[attr-defined]
        except (KeyError, IndexError):
            pass

    # --- _fetch_parent (structured-ref plug-point; consumed by OnPrimitiveChange)

    def _fetch_parent(self, rt: Runtime, nid: int) -> object:
        """Return the parent view holding this leaf's slot (top-level -> root)."""
        return self._fetch_parent_view(rt, self._resolve_path(rt, nid))

    async def _afetch_parent(self, rt: Runtime, nid: int) -> object:
        """Async sibling of :meth:`_fetch_parent`."""
        return self._fetch_parent_view(rt, await self._aresolve_path(rt, nid))
