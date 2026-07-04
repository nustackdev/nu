"""FlatRef — flat, pre-resolved ref for virtuals substrate execution.

Replaces a Ref parent-chain (O(depth) resolve per op) with a single node holding
a pre-computed path tuple of ``(address, type_marker)`` segments, where
type_marker is a View subclass (containers) or a Python type (primitives).
Created only by the ``inline_refs()`` deformation, never user-facing.

The path is ``_static_path`` with ``(None, marker)`` placeholders at dynamic
positions; ``_dynamic_segments`` pairs each placeholder index with the Nu that
fills it. The dynamic Nus are this node's tree children (slot order =
``_dynamic_segments`` order), resolved through the runtime like any child thunk.

``is_primitive`` selects the read mode: a leaf (navigate to parent View +
subscript) or a container (open the View at the full path, faceted lazy/eager
is dropped at this flat layer — extract handles materialization).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import EMPTY, Nu, Ref
from nu.virtuals.paths import ViewPathSer
from virtuals import Empty as StorageEmpty
from virtuals import Navigator
from virtuals.collections import Subscriptable
from virtuals.tkv.storage import SnapshotProtocol, TransactionProtocol


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "FlatRef",
]


class FlatRef(Ref):
    """Flat, pre-resolved ref for the virtuals substrate."""

    def __init__(
        self,
        *,
        static_path: tuple[tuple[object, type], ...],
        root_shape: type | None,
        is_primitive: bool,
        dynamic_segments: tuple[tuple[int, Nu], ...] | None = None,
    ) -> None:
        # Tree children: the dynamic Nu segments, in slot order.
        if dynamic_segments:
            super().__init__(*(seg[1] for seg in dynamic_segments))
        else:
            super().__init__()
        self._static_path = static_path
        self._root_shape = root_shape
        self._is_primitive = is_primitive
        self._dynamic_segments = dynamic_segments

    def with_children(self, *children: object):  # type: ignore[override]
        """Rebuild with new children while preserving flat-path metadata.

        The base :class:`Term.with_children` copies only ``children`` and
        ``payload``. FlatRef carries the static path, root shape, primitive
        flag, and dynamic-segment mapping as instance attrs, so we copy the
        full ``__dict__`` and then override ``children``. The tree rewriter
        always routes through this method, so the dynamic address children
        can still be rewritten while the substrate state survives.
        """
        variant = object.__new__(type(self))
        variant.__dict__.update(self.__dict__)
        variant.children = children
        return variant

    def get_root_shape(self) -> type | None:
        """Return the root shape for context lookup."""
        return self._root_shape

    # --- path building -------------------------------------------------------

    def _apply_segments(self, segment_values: tuple) -> tuple[tuple[object, type], ...]:
        """Fill the static path's dynamic placeholders with resolved values."""
        if self._dynamic_segments is None:
            return self._static_path
        path = list(self._static_path)
        for (idx, _), value in zip(self._dynamic_segments, segment_values, strict=True):
            _old_addr, marker = path[idx]
            path[idx] = (value, marker)
        return tuple(path)

    def _resolve_path(self, rt: Runtime, nid: int) -> tuple[tuple[object, type], ...]:
        """Substrate protocol: fully-resolved path at runtime for FlatRef's own nid.

        Mirrors ``_VirtualsRefBase._resolve_path(rt, nid)`` so op interactions
        that hold a ref child (``ItemPrimitiveStoreCmd``, ``ItemPrimitiveGetUnsafe``,
        etc.) route through this after ``inline_refs`` flattens their ref.
        """
        return self._apply_segments(self._segment_values(rt, nid))

    async def _aresolve_path(self, rt: Runtime, nid: int) -> tuple[tuple[object, type], ...]:
        """Async sibling of :meth:`_resolve_path`."""
        return self._apply_segments(await self._asegment_values(rt, nid))

    def address(self, rt: Runtime, nid: int) -> object:
        """Substrate protocol: this ref's leaf address (the last path segment)."""
        return self._resolve_path(rt, nid)[-1][0]

    async def aaddress(self, rt: Runtime, nid: int) -> object:
        """Async sibling of :meth:`address`."""
        return (await self._aresolve_path(rt, nid))[-1][0]

    def _resolve_navigator(self, rt: Runtime, path: tuple) -> Navigator:
        scope = self._root_shape
        if not path:
            return rt.ctx.get(Navigator, scope) if scope is not None else rt.ctx.get(Navigator)
        site = tuple(addr for addr, _ in path)
        if scope is not None:
            return rt.ctx.get(Navigator, scope, site=site, path=path)
        return rt.ctx.get(Navigator, site=site, path=path)

    def _resolve_storage_ctx(self, rt: Runtime, path: tuple) -> object:
        scope = self._root_shape
        tags = (scope,) if scope is not None else ()
        if not path:
            try:
                return rt.ctx.get(TransactionProtocol, *tags)
            except (KeyError, LookupError):
                return rt.ctx.get(SnapshotProtocol, *tags)
        site = tuple(addr for addr, _ in path)
        try:
            return rt.ctx.get(TransactionProtocol, *tags, site=site, path=path)
        except (KeyError, LookupError):
            return rt.ctx.get(SnapshotProtocol, *tags, site=site, path=path)

    # --- read (the dual role) ------------------------------------------------

    def _read(self, rt: Runtime, path: tuple) -> object:
        nav = self._resolve_navigator(rt, path)
        storage_ctx = self._resolve_storage_ctx(rt, path)
        if not self._is_primitive:
            if not path:
                return nav.root(storage_ctx)
            return nav.open_at_path(ViewPathSer(path), storage_ctx)
        parent_path = path[:-1]
        key = path[-1][0]
        try:
            parent_view = nav.root(storage_ctx) if not parent_path else nav.open_at_path(
                ViewPathSer(parent_path), storage_ctx
            )
            if isinstance(parent_view, Subscriptable):
                val = parent_view[key]
                return EMPTY if isinstance(val, StorageEmpty) else val
            msg = f"View {parent_view.__class__.__name__} is not subscriptable"
            raise TypeError(msg)
        except (KeyError, IndexError):
            return EMPTY

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            path = self._apply_segments(tuple(c(rt) for c in children))
            return self._read(rt, path)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            path = self._apply_segments(tuple([await c(rt) for c in children]))
            return self._read(rt, path)

        return athunk

    # --- write / erase -------------------------------------------------------

    def _fetch_parent_view(self, rt: Runtime, path: tuple) -> object:
        """Substrate protocol: parent View for a fully-resolved path."""
        nav = self._resolve_navigator(rt, path)
        storage_ctx = self._resolve_storage_ctx(rt, path)
        parent_path = path[:-1]
        if not parent_path:
            return nav.root(storage_ctx)
        return nav.open_at_path(ViewPathSer(parent_path), storage_ctx)

    def _segment_values(self, rt: Runtime, nid: int) -> tuple:
        if self._dynamic_segments is None:
            return ()
        child_nids = rt.program.children[nid]
        return tuple(rt.eval(cn) for cn in child_nids)

    async def _asegment_values(self, rt: Runtime, nid: int) -> tuple:
        if self._dynamic_segments is None:
            return ()
        child_nids = rt.program.children[nid]
        return tuple([await rt.aeval(cn) for cn in child_nids])

    def write(self, rt: Runtime, value: object, nid: int) -> None:
        """Write ``value`` at this ref's path through the parent View."""
        path = self._resolve_path(rt, nid)
        parent = self._fetch_parent_view(rt, path)
        parent[path[-1][0]] = value  # type: ignore[index]

    async def awrite(self, rt: Runtime, value: object, nid: int) -> None:
        """Async sibling of :meth:`write`."""
        path = await self._aresolve_path(rt, nid)
        parent = self._fetch_parent_view(rt, path)
        parent[path[-1][0]] = value  # type: ignore[index]

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

    def __repr__(self) -> str:
        addrs = tuple(a for a, _m in self._static_path)
        if self._dynamic_segments:
            return f"FlatRef(path={addrs}, dynamic={len(self._dynamic_segments)})"
        return f"FlatRef(path={addrs})"
