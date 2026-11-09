"""How a kv ref reads and writes: navigate the virtuals View hierarchy of a store.

Two substrates cover every kv ref. ``ViewRef`` reads a container as a live
View, so collection ops run against storage; ``PrimitiveRef`` subscripts its
parent View, so a leaf reads as a plain value. Each level of a ref's path is a
child on the tree, resolved at run time, so a key may be a literal, a computed
expression, or a ref from another fabric. The Navigator and the storage context
(transaction or snapshot) come from the Context under the chain's root shape.

A container also decides what its children are: the ref at ``ref[key]`` is
the kv ref for the value the container declared.

A key that reads NULL (an id looked up in an index with no entry for it)
leaves the path addressing nothing: a read, a write or a watch through it
raises ``NullAddressError``. Branch on the key first (``IsNull``).
"""

from __future__ import annotations

import typing
from enum import Enum
from logging import getLogger
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

import nu
from nu.domains.shape.base import StructuredRef
from nu.lang.null import Null, is_null
from nu.lang.typeinfo import TypeInfo
from nustd.kv.errors import NullAddressError
from nustd.kv.paths import ViewPathSer
from virtuals import Empty as StorageEmpty
from virtuals import Navigator
from virtuals.collections import Subscriptable
from virtuals.tkv.storage import SnapshotProtocol, TransactionProtocol
from virtuals.view import ViewBase


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.domains.shape.dsl import Shape
    from nu.lang.runtime import Runtime
    from nustd.kv.interactions.extract import ViewExtract
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


def _dotted(shape: type | None, path: tuple) -> str:
    """The dotted path a ref names, eg ``Space.state.recents``."""
    return ".".join([shape.__name__ if shape is not None else "?", *(str(a) for a, _ in path)])


def _resolve_navigator(rt: Runtime, scope: type | None, resolved_path: tuple) -> Navigator:
    """Resolve Navigator from the runtime ctx, passing site and path for routing.

    Every storage access on a ref passes through here, so this is where a path
    with a NULL segment stops: a read, a write or a watch through it raises
    ``NullAddressError``.
    """
    for i, (addr, _) in enumerate(resolved_path):
        if is_null(addr):
            where = _dotted(scope, resolved_path[:i])
            msg = f"a key under {where} read NULL, so the path addresses nothing"
            raise NullAddressError(msg)
    if not resolved_path:
        return (
            rt.ctx.fabrics.get(Navigator, scope)
            if scope is not None
            else rt.ctx.fabrics.get(Navigator)
        )
    site = tuple(addr for addr, _ in resolved_path)
    if scope is not None:
        return rt.ctx.fabrics.get(Navigator, scope, site=site, path=resolved_path)
    return rt.ctx.fabrics.get(Navigator, site=site, path=resolved_path)


def _resolve_storage_ctx(rt: Runtime, scope: type | None, resolved_path: tuple) -> object:
    """Resolve storage context (transaction / snapshot) from the runtime ctx."""
    tags = (scope,) if scope is not None else ()
    if not resolved_path:
        try:
            return rt.ctx.fabrics.get(TransactionProtocol, *tags)
        except (KeyError, LookupError):
            return rt.ctx.fabrics.get(SnapshotProtocol, *tags)
    site = tuple(addr for addr, _ in resolved_path)
    try:
        return rt.ctx.fabrics.get(TransactionProtocol, *tags, site=site, path=resolved_path)
    except (KeyError, LookupError):
        return rt.ctx.fabrics.get(SnapshotProtocol, *tags, site=site, path=resolved_path)


def _plain(value: object) -> object:
    """A stored value as a leaf reads it: a container stored decomposed comes back extracted."""
    if isinstance(value, ViewBase):
        return value.eager.extract()
    return value


def _refuse_container_value(owner: type, value: object) -> None:
    """Raise when a container slot is declared to hold a container ref.

    Only a Shape gives a container's value a layout of its own. A container
    ref there would be stored as one opaque value, with no keys, order or
    watch, so it is refused where it is declared.
    """
    held = typing.get_origin(value) or value
    if isinstance(held, type) and issubclass(held, ViewRef):
        msg = (
            f"{owner.__name__}.slot({held.__name__}): a container cannot hold a container ref, "
            f"it would be stored as one opaque value. Use a Shape: declare one with a "
            f"{held.__name__} slot and hold that Shape"
        )
        raise TypeError(msg)


class _VirtualsRefBase(StructuredRef, Generic[T]):
    """Shared virtuals navigation: path building off the parent chain + Navigator.

    Each ref stores its raw static address in payload as ``"segment"``; a
    container also stores its View class as ``"type_marker"``, and a leaf has
    none. The full path is ``((addr, marker), ...)`` root-first.
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
        payload (None for a leaf). Because the parent lives on the tree, a
        *dynamic* parent key resolves here like any other child - no
        static-segment shortcut needed.
        """
        segs: list[tuple[object, type]] = []
        cur = nid
        while True:
            kids = rt.program.children[cur]
            term = rt.program.terms[cur]
            segs.append((rt.eval(kids[1]), nu.tree.payload(term).get("type_marker")))  # type: ignore[attr-defined]
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
            segs.append((await rt.aeval(kids[1]), nu.tree.payload(term).get("type_marker")))  # type: ignore[attr-defined]
            parent = kids[0]
            if not isinstance(rt.program.terms[parent], StructuredRef):
                break
            cur = parent
        segs.reverse()
        return tuple(segs)

    def _hint(self, path: tuple) -> str:
        """The dotted path a NULL read names, eg ``Space.state.recents``."""
        return _dotted(self._root_shape, path)


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
        - Yields a lazy handle, never NULL, even where nothing is written:
          ask ``exists()``, or ``extract()`` the value and test it. On a
          never-written container ``len``, iteration and ``contains`` raise,
          ``extract()`` gives NULL.
        - A path with a key that read NULL addresses nothing: a read, a
          write or a watch through it raises ``NullAddressError``.
        - The storage context is a transaction when one is bound, otherwise a
          snapshot; a snapshot is read-only, so writes need the transaction.

    Example:
        class Portfolio(Shape):
            tags = ListRef.slot(str)
        run(Portfolio.tags.append("core"), ctx)
        run(Portfolio.tags.len(), ctx)
    """

    _default_view: ClassVar[type[View] | None] = None
    """The View class a slot of this ref lays its container out with, unless it names one."""

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
        self._payload["type_marker"] = view_type or self._default_view

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """What an annotation slot (``ids: DictRef[str, bool]``) passes on: nothing.

        Its last type argument is the value the container holds, refused here
        when it is a container ref, as ``slot()`` refuses it.
        """
        if args:
            _refuse_container_value(cls, args[-1])
        return {}

    def _wrap_item_ref(self, address: object) -> StructuredRef:
        """The child at ``address``: the kv ref for the value this container declared.

        A Shape gets a ``ShapeRef`` bound to it, a kv leaf class gets itself, a
        core Python type gets the kv leaf that holds it, and a value declared as
        anything else, or not at all, gets ``ObjectRef``. The child carries the
        declaration on, as a slot's ref does.
        """
        from .containers import LEAVES, ShapeRef
        from .items import ItemRef, ObjectRef

        declared: TypeInfo = self._payload.get("type_info") or TypeInfo.any()  # type: ignore[assignment]
        value = declared.elem or TypeInfo.any()
        held = value.py_type
        child: StructuredRef
        if value.is_shape:
            child = ShapeRef(
                address, shape_type=held, parent_ref=self, owner_shape=self._owner_shape
            )
        else:
            leaf = (
                held
                if isinstance(held, type) and issubclass(held, ItemRef)
                else LEAVES.get(held, ObjectRef)
            )
            child = leaf(address, parent_ref=self, owner_shape=self._owner_shape)
        child._payload["type_info"] = value
        return child

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
            - Still a handle, not the value: ``extract()`` is the value read.
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

    def _apply_facet(self, view: View) -> View:
        """Apply the lazy/eager facet to a fetched view.

        Every view declares both facets; one without a twin returns itself.
        """
        facet = self._payload.get("facet", Facet.LAZY)
        if facet is Facet.EAGER:
            return view.eager
        if facet is Facet.LAZY:
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

    def extract(self) -> ViewExtract:
        """Read the whole container as plain Python values.

        Notes:
            - NULL, hinted with the dotted path, when the container was never
              written; ``len``, iteration and ``contains`` raise there instead.

        Yields:
            The extracted value, or NULL.

        Example:
            run(Portfolio.tags.extract(), ctx)
        """
        from nustd.kv.interactions.extract import ViewExtract

        return ViewExtract(self)

    def _open(self, rt: Runtime, path: tuple) -> View:
        nav = _resolve_navigator(rt, self._root_shape, path)
        return nav.open_at_path(ViewPathSer(path), _resolve_storage_ctx(rt, self._root_shape, path))

    def _exists(self, rt: Runtime, nid: int) -> bool:
        """Whether the container is stored: one marker read, nothing extracted."""
        return self._open(rt, self._resolve_path(rt, nid)).exists()

    async def _aexists(self, rt: Runtime, nid: int) -> bool:
        """Async sibling of :meth:`_exists`."""
        return self._open(rt, await self._aresolve_path(rt, nid)).exists()

    # --- write / erase (whole-view store via parent decomposition) -----------

    def _fetch_parent_view(self, rt: Runtime, path: tuple) -> object:
        """Read-side parent open -- pure navigation, no side effects.

        Safe on read-only storage contexts (snapshots, RO secondaries).
        Callers that intend to WRITE via the returned view should use
        ``_fetch_and_ensure_parent_view`` instead so every ancestor along
        the path is materialized with its declared view type, each one
        created by its parent view so the parent counts or indexes it.
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
        stamped with the correct marker by its parent view (``ensure_child``
        at each level, which also runs ``_ensure_internal_layout`` on views
        like ``LogIndexedDictView`` that carry a custom sub-layout, and lets
        the parent record the new child). Only call on a write-capable
        context.
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
        - Yields NULL, hinted with the dotted path, when the parent has no
          such key or index, or storage hands back its own empty marker.
          Nothing else is caught, so real errors stay errors.
        - Raises ``NullAddressError`` when a key in the path read NULL.
        - A write materializes every ancestor along the path first, so a leaf
          can be written into storage that has nothing above it yet.
        - Erasing a leaf that is not there is a no-op.
        - A container stored under the leaf reads back extracted, as a plain
          dict or list, never as a live View.
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

    # --- read (the dual role) ------------------------------------------------

    def _read(self, rt: Runtime, path: tuple) -> object:
        nav = _resolve_navigator(rt, self._root_shape, path)
        storage_ctx = _resolve_storage_ctx(rt, self._root_shape, path)
        parent_path = path[:-1]
        key = path[-1][0]
        parent_view = (
            nav.root(storage_ctx)
            if not parent_path
            else nav.open_at_path(ViewPathSer(parent_path), storage_ctx)
        )
        if not isinstance(parent_view, Subscriptable):
            msg = f"View {parent_view.__class__.__name__} is not subscriptable"
            raise TypeError(msg)
        try:
            val = parent_view[key]
        except (KeyError, IndexError):
            return Null(self._hint(path))
        if isinstance(val, StorageEmpty):
            return Null(self._hint(path))
        return self._lift(_plain(val))

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
