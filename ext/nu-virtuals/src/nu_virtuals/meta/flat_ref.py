"""FlatRef — flat, pre-resolved ref for virtuals substrate execution.

Replaces the Ref parent-chain with a single node holding a pre-computed
path tuple. Paths are tuples of (address, type_marker) segments where
type_marker is a View subclass (for containers) or a Python type
(for primitives). Navigation uses virtuals.loc.path.navigate_view() / navigate_value().

Not user-facing. Created only by the inline_refs() deformation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu_virtuals.paths import ViewPathSer
from nu import EMPTY, Sentinel, Nu


if TYPE_CHECKING:
    from nu import Context


__all__ = [
    "FlatRef",
]


class FlatRef(Nu):
    """Flat, pre-resolved ref for virtuals substrate.

    Attributes:
        _static_path: Path tuple ((addr, marker), ...). Dynamic positions
            hold (None, marker) placeholders.
        _root_shape: Shape class for context lookup.
        _dynamic_segments: tuple of (index, Nu) for dynamic positions, or None.
        _last_address: Pre-extracted last address for resolve_address fast path.
        _is_primitive: True if leaf ref is a PrimitiveRef (not a ViewRef).
    """

    def __init__(
        self,
        *,
        static_path: tuple[tuple[object, type], ...],
        root_shape: type,
        is_primitive: bool,
        dynamic_segments: tuple[tuple[int, Nu], ...] | None = None,
    ) -> None:
        if dynamic_segments:
            super().__init__(*(seg[1] for seg in dynamic_segments))
        else:
            super().__init__()
        self._static_path = static_path
        self._root_shape = root_shape
        self._is_primitive = is_primitive
        self._dynamic_segments = dynamic_segments
        self._last_address: object = static_path[-1][0] if static_path else None
        self._is_last_dynamic = dynamic_segments is not None and any(
            idx == len(static_path) - 1 for idx, _ in dynamic_segments
        )

    # =========================================================================
    # Ref interface — what ops call
    # =========================================================================

    async def resolve_address(self, ctx: Context) -> object:
        """Return this ref's address (last path segment). O(1) for static."""
        if not self._is_last_dynamic:
            return self._last_address
        resolved = await self._build_path(ctx)
        return resolved[-1][0]

    async def fetch_parent(self, ctx: Context) -> object:
        """Navigate to parent view via Navigator."""
        resolved = await self._build_path(ctx) if self._dynamic_segments else self._static_path
        nav = self._resolve_navigator(ctx, resolved)
        storage_ctx = self._resolve_storage_ctx(ctx, resolved)

        if self._is_primitive:
            parent_path = resolved[:-1]
            if not parent_path:
                return nav.root(storage_ctx)
            return nav.open_at_path(ViewPathSer(parent_path), storage_ctx)
        else:
            if len(resolved) <= 1:
                return nav.root(storage_ctx)
            parent_path = resolved[:-1]
            return nav.open_at_path(ViewPathSer(parent_path), storage_ctx)

    async def fetch(self, ctx: Context) -> object | Sentinel:
        """Fetch value/view via Navigator."""
        from virtuals import Empty as StorageEmpty
        from virtuals.collections import Subscriptable

        resolved = await self._build_path(ctx) if self._dynamic_segments else self._static_path
        nav = self._resolve_navigator(ctx, resolved)
        storage_ctx = self._resolve_storage_ctx(ctx, resolved)

        if not self._is_primitive:
            if not resolved:
                return nav.root(storage_ctx)
            return nav.open_at_path(ViewPathSer(resolved), storage_ctx)

        parent_path = resolved[:-1]
        key = resolved[-1][0]

        try:
            if not parent_path:
                parent_view = nav.root(storage_ctx)
            else:
                parent_view = nav.open_at_path(ViewPathSer(parent_path), storage_ctx)
            if isinstance(parent_view, Subscriptable):
                val = parent_view[key]
                return val if not isinstance(val, StorageEmpty) else EMPTY
            raise TypeError(f"View {parent_view.__class__.__name__} is not subscriptable")
        except (KeyError, IndexError):
            return EMPTY

    async def resolve(self, ctx: Context) -> tuple:
        """Return full resolved path."""
        if self._dynamic_segments is None:
            return self._static_path
        return await self._build_path(ctx)

    async def execute(self, ctx: Context) -> object | Sentinel:
        """Nu interface — delegates to fetch."""
        return await self.fetch(ctx)

    def get_root_shape(self) -> type:
        """Return root shape for context lookup."""
        return self._root_shape

    @property
    def is_self_pure(self) -> bool:
        """Reads are always pure."""
        return True

    # =========================================================================
    # Internal
    # =========================================================================

    def _resolve_navigator(self, ctx: Context, resolved_path: tuple) -> object:
        """Resolve Navigator, passing site and path for predicate routing."""
        from virtuals import Navigator

        if not resolved_path:
            return ctx.get(Navigator, self._root_shape)
        site = tuple(addr for addr, _ in resolved_path)
        return ctx.get(Navigator, self._root_shape, site=site, path=resolved_path)

    def _resolve_storage_ctx(self, ctx: Context, resolved_path: tuple) -> object:
        """Resolve storage context (transaction/snapshot) for predicate routing."""
        from virtuals.tkv.storage import SnapshotProtocol, TransactionProtocol

        if not resolved_path:
            try:
                return ctx.get(TransactionProtocol, self._root_shape)
            except (KeyError, LookupError):
                return ctx.get(SnapshotProtocol, self._root_shape)
        site = tuple(addr for addr, _ in resolved_path)
        try:
            return ctx.get(TransactionProtocol, self._root_shape, site=site, path=resolved_path)
        except (KeyError, LookupError):
            return ctx.get(SnapshotProtocol, self._root_shape, site=site, path=resolved_path)

    async def _build_path(self, ctx: Context) -> tuple:
        """Build full path, resolving dynamic segments."""
        if self._dynamic_segments is None:
            return self._static_path
        path_list = list(self._static_path)
        for idx, term in self._dynamic_segments:
            addr = await term.execute(ctx)
            _old_addr, marker = path_list[idx]
            path_list[idx] = (addr, marker)
        return tuple(path_list)

    def __repr__(self) -> str:
        addrs = tuple(a for a, _m in self._static_path)
        if self._dynamic_segments:
            return f"FlatRef(path={addrs}, dynamic={len(self._dynamic_segments)})"
        return f"FlatRef(path={addrs})"
