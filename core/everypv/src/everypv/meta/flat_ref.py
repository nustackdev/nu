"""FlatRef — flat, pre-resolved ref for PV substrate execution.

Replaces the Ref parent-chain with a single node holding a pre-computed
PV path tuple. PV paths are tuples of (address, type_marker) segments
where type_marker is a View subclass (for containers) or a Python type
(for primitives). Navigation uses pv.loc.path.navigate_view() / navigate_value().

Not user-facing. Created only by the inline_refs() deformation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import EMPTY, Sentinel, Term


if TYPE_CHECKING:
    from everybase import Context


__all__ = [
    "FlatRef",
]


class FlatRef(Term):
    """Flat, pre-resolved ref for PV substrate.

    Attributes:
        _static_path: PV path tuple ((addr, marker), ...). Dynamic positions
            hold (None, marker) placeholders.
        _root_shape: Shape class for context lookup.
        _dynamic_segments: tuple of (index, Term) for dynamic positions, or None.
        _last_address: Pre-extracted last address for resolve_address fast path.
        _is_primitive: True if leaf ref is a PrimitiveRef (not a ViewRef).
    """

    def __init__(
        self,
        *,
        static_path: tuple[tuple[object, type], ...],
        root_shape: type,
        is_primitive: bool,
        dynamic_segments: tuple[tuple[int, Term], ...] | None = None,
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
    # Ref interface — what morphisms call
    # =========================================================================

    async def resolve_address(self, ctx: Context) -> object:
        """Return this ref's address (last path segment). O(1) for static."""
        if not self._is_last_dynamic:
            return self._last_address
        pv_path = await self._build_path(ctx)
        return pv_path[-1][0]

    async def fetch_parent(self, ctx: Context) -> object:
        """Navigate to parent view in PV hierarchy."""
        from pv.loc import path as pv_path_mod
        from pv.view import View

        root_view = ctx.get(View, scope=self._root_shape)
        pv_path = await self._build_path(ctx) if self._dynamic_segments else self._static_path

        if self._is_primitive:
            # PrimitiveRef: navigate_value returns (parent_view, key)
            parent_view, _key = pv_path_mod.navigate_value(root_view, pv_path)
            return parent_view
        else:
            # ViewRef: parent is the view at path[:-1]
            if len(pv_path) <= 1:
                return root_view
            parent_path = pv_path[:-1]
            return pv_path_mod.navigate_view(root_view, parent_path)

    async def fetch(self, ctx: Context) -> object | Sentinel:
        """Fetch value/view from PV storage."""
        import pv.traits as view_traits
        from pv import Empty as PVEmpty
        from pv.loc import path as pv_path_mod
        from pv.view import View

        root_view = ctx.get(View, scope=self._root_shape)
        pv_path = await self._build_path(ctx) if self._dynamic_segments else self._static_path

        if not self._is_primitive:
            # ViewRef: navigate to the view
            if not pv_path:
                return root_view
            return pv_path_mod.navigate_view(root_view, pv_path)

        # PrimitiveRef: navigate to parent, subscript for value
        try:
            parent_view, key = pv_path_mod.navigate_value(root_view, pv_path)
            if isinstance(parent_view, view_traits.Subscriptable):
                val = parent_view[key]
                return val if not isinstance(val, PVEmpty) else EMPTY
            raise TypeError(f"View {parent_view.__class__.__name__} is not subscriptable")
        except (KeyError, IndexError):
            return EMPTY

    async def resolve(self, ctx: Context) -> tuple:
        """Return full resolved PV path."""
        if self._dynamic_segments is None:
            return self._static_path
        return await self._build_path(ctx)

    async def execute(self, ctx: Context) -> object | Sentinel:
        """Term interface — delegates to fetch."""
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

    async def _build_path(self, ctx: Context) -> tuple:
        """Build full PV path, resolving dynamic segments."""
        if self._dynamic_segments is None:
            return self._static_path
        path_list = list(self._static_path)
        for idx, term in self._dynamic_segments:
            addr = await term.execute(ctx)
            # Replace address but keep the type marker
            _old_addr, marker = path_list[idx]
            path_list[idx] = (addr, marker)
        return tuple(path_list)

    def __repr__(self) -> str:
        addrs = tuple(a for a, _m in self._static_path)
        if self._dynamic_segments:
            return f"FlatRef(path={addrs}, dynamic={len(self._dynamic_segments)})"
        return f"FlatRef(path={addrs})"
