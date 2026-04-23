"""FlatRef — flat, pre-resolved ref for dict substrate execution.

Replaces the Ref parent-chain (O(depth) resolve per operation) with a single
node holding a pre-computed path tuple (O(1) resolve). All existing morphisms
(ItemLoadOp, ItemStoreCmd, etc.) work unchanged — they call fetch_parent() and
resolve_address(), which FlatRef provides.

Not user-facing. Created only by the inline_refs() deformation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import EMPTY, Nu, Sentinel
from nu.terms import Mode


if TYPE_CHECKING:
    from nu import Context


__all__ = [
    "FlatRef",
]


class FlatRef(Nu):
    """Flat, pre-resolved ref for dict substrate.

    For all-static paths (the common case), this is just a tuple lookup.
    For mixed static/dynamic paths, only the dynamic Nu segments are executed.

    Attributes:
        _static_path: Full path tuple. Dynamic positions hold None placeholders.
        _root_shape: Shape class for context lookup.
        _dynamic_segments: tuple of (index, Nu) for dynamic positions, or None.
        _last_address: Pre-extracted last path segment (for resolve_address fast path).
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *,
        static_path: tuple[str | int | None, ...],
        root_shape: type,
        dynamic_segments: tuple[tuple[int, Nu], ...] | None = None,
    ) -> None:
        # Tree children: only dynamic Nu segments (for traversal / further deformations)
        if dynamic_segments:
            super().__init__(*(seg[1] for seg in dynamic_segments))
        else:
            super().__init__()
        self._static_path = static_path
        self._root_shape = root_shape
        self._dynamic_segments = dynamic_segments
        # Pre-extract last address for the all-static fast path
        self._last_address: object = static_path[-1] if static_path else None
        self._is_last_dynamic = dynamic_segments is not None and any(
            idx == len(static_path) - 1 for idx, _ in dynamic_segments
        )

    # =========================================================================
    # Ref interface — what morphisms call
    # =========================================================================

    async def aresolve_address(self, ctx: Context) -> object:
        """Return this ref's address (last path segment). O(1) for static."""
        if not self._is_last_dynamic:
            return self._last_address
        # Dynamic last segment — resolve it
        path = await self._build_path(ctx)
        return path[-1]

    async def afetch_parent(self, ctx: Context) -> object:
        """Navigate to parent container. O(path_length) dict lookups."""
        path = await self._build_path(ctx) if self._dynamic_segments else self._static_path
        data = self._get_root_data(ctx, path)
        current = data
        for key in path[:-1]:
            if isinstance(current, dict) and key not in current:
                current[key] = {}
                current = current[key]
            else:
                current = current[key]  # type: ignore[index]
        return current

    async def afetch(self, ctx: Context) -> object | Sentinel:
        """Fetch value at this path. O(path_length) dict lookups."""
        path = await self._build_path(ctx) if self._dynamic_segments else self._static_path
        data = self._get_root_data(ctx, path)
        try:
            current = data
            for key in path:
                current = current[key]  # type: ignore[index]
            return current
        except (KeyError, IndexError):
            return EMPTY

    async def aresolve(self, ctx: Context) -> tuple:
        """Return full resolved path."""
        if self._dynamic_segments is None:
            return self._static_path
        return await self._build_path(ctx)

    async def aexecute(self, ctx: Context) -> object | Sentinel:
        """Nu interface — delegates to fetch."""
        return await self.afetch(ctx)

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

    def _get_root_data(self, ctx: Context, path: tuple | None = None) -> object:
        """Get root data from context."""
        if path is not None:
            return ctx.get(dict, self._root_shape, site=path)
        return ctx[dict, self._root_shape]

    async def _build_path(self, ctx: Context) -> tuple:
        """Build full path, resolving dynamic segments."""
        if self._dynamic_segments is None:
            return self._static_path
        path = list(self._static_path)
        for idx, term in self._dynamic_segments:
            path[idx] = await term.aexecute(ctx)
        return tuple(path)

    def __repr__(self) -> str:
        if self._dynamic_segments:
            return f"FlatRef(path={self._static_path}, dynamic={len(self._dynamic_segments)})"
        return f"FlatRef(path={self._static_path})"
