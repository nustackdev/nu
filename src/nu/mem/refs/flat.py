"""FlatRef — flat, pre-resolved ref for dict substrate execution.

Replaces a Ref parent-chain (O(depth) resolve per op) with a single node holding
a pre-computed path tuple (O(1) for all-static paths). Created only by the
``inline_refs()`` deformation, never user-facing.

The path is ``_static_path`` with ``None`` placeholders at dynamic positions;
``_dynamic_segments`` pairs each placeholder index with the Nu that fills it. The
dynamic Nus are this node's tree children (slot order = ``_dynamic_segments``
order), resolved through the runtime like any child thunk.

Note: this rides the v2 substrate seam (``compile`` read thunk, ``write`` /
``erase`` (rt, nid)) but is wired only once ``tree/inline_refs`` is ported.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import EMPTY, Nu, Ref


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "FlatRef",
]


class FlatRef(Ref):
    """Flat, pre-resolved ref for the dict substrate.

    For all-static paths (the common case) this is a plain tuple lookup; for
    mixed paths only the dynamic Nu segments are executed.
    """

    def __init__(
        self,
        *,
        static_path: tuple[str | int | None, ...],
        root_shape: type,
        dynamic_segments: tuple[tuple[int, Nu], ...] | None = None,
        lift: Callable[[object], object] | None = None,
    ) -> None:
        # Tree children: the dynamic Nu segments, in slot order.
        if dynamic_segments:
            super().__init__(*(seg[1] for seg in dynamic_segments))
        else:
            super().__init__()
        self._static_path = static_path
        self._root_shape = root_shape
        self._dynamic_segments = dynamic_segments
        # The flattened leaf's value boundary; guaranteed on the read path so a
        # flattened typed ref (DateRef, ...) still returns its domain type.
        self._lift = lift if lift is not None else (lambda raw: raw)

    def with_children(self, *children: object):  # type: ignore[override]
        """Rebuild with new children while preserving flat-path metadata.

        The base :class:`Term.with_children` copies only ``children`` and
        ``payload``. FlatRef carries the static path, root shape, and
        dynamic-segment mapping as instance attrs, so we copy the full
        ``__dict__`` and then override ``children``. The tree rewriter
        always routes through this method, so the dynamic address children
        can still be rewritten while the substrate state survives.
        """
        variant = object.__new__(type(self))
        variant.__dict__.update(self.__dict__)
        variant.children = children
        return variant

    def get_root_shape(self) -> type:
        """Return the root shape for context lookup."""
        return self._root_shape

    # --- path building -------------------------------------------------------

    def _root_data(self, rt: Runtime) -> object:
        """The root dict bound in the Context, scoped to this ref's root shape."""
        return rt.ctx.get(dict, self._root_shape)

    def _resolve_path(self, segment_values: tuple) -> tuple:
        """Fill the static path's dynamic placeholders with resolved values."""
        if self._dynamic_segments is None:
            return self._static_path
        path = list(self._static_path)
        for (idx, _), value in zip(self._dynamic_segments, segment_values, strict=True):
            path[idx] = value
        return tuple(path)

    # --- read (the dual role) ------------------------------------------------

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            path = self._resolve_path(tuple(c(rt) for c in children))
            cur = self._root_data(rt)
            try:
                for k in path:
                    cur = cur[k]  # type: ignore[index]
            except (KeyError, IndexError, TypeError):
                return EMPTY
            return self._lift(cur)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            path = self._resolve_path(tuple([await c(rt) for c in children]))
            cur = self._root_data(rt)
            try:
                for k in path:
                    cur = cur[k]  # type: ignore[index]
            except (KeyError, IndexError, TypeError):
                return EMPTY
            return self._lift(cur)

        return athunk

    # --- write / erase -------------------------------------------------------

    def _write(self, rt: Runtime, value: object, nid: int) -> None:
        """Write ``value`` at this ref's path, vivifying intermediate dicts."""
        path = self._resolve_path(self._segment_values(rt, nid))
        container = self._vivify_parent(rt, path)
        container[path[-1]] = value  # type: ignore[index]

    async def _awrite(self, rt: Runtime, value: object, nid: int) -> None:
        """Async sibling of :meth:`write`."""
        path = self._resolve_path(await self._asegment_values(rt, nid))
        container = self._vivify_parent(rt, path)
        container[path[-1]] = value  # type: ignore[index]

    def _erase(self, rt: Runtime, nid: int) -> None:
        """Remove this ref's slot from its parent container, if present."""
        path = self._resolve_path(self._segment_values(rt, nid))
        container = self._vivify_parent(rt, path)
        key = path[-1]
        if isinstance(container, dict) and key in container:
            del container[key]

    async def _aerase(self, rt: Runtime, nid: int) -> None:
        """Async sibling of :meth:`erase`."""
        path = self._resolve_path(await self._asegment_values(rt, nid))
        container = self._vivify_parent(rt, path)
        key = path[-1]
        if isinstance(container, dict) and key in container:
            del container[key]

    def _segment_values(self, rt: Runtime, nid: int) -> tuple:
        """Resolve the dynamic segment children by their own node ids."""
        if self._dynamic_segments is None:
            return ()
        child_nids = rt.program.children[nid]
        return tuple(rt.eval(cn) for cn in child_nids)

    async def _asegment_values(self, rt: Runtime, nid: int) -> tuple:
        """Async sibling of :meth:`_segment_values`."""
        if self._dynamic_segments is None:
            return ()
        child_nids = rt.program.children[nid]
        return tuple([await rt.aeval(cn) for cn in child_nids])

    def _vivify_parent(self, rt: Runtime, path: tuple) -> object:
        """Navigate to the parent container, auto-creating intermediate dicts."""
        cur = self._root_data(rt)
        for k in path[:-1]:
            if isinstance(cur, dict) and k not in cur:
                cur[k] = {}
            cur = cur[k]  # type: ignore[index]
        return cur

    def __repr__(self) -> str:
        if self._dynamic_segments:
            return f"FlatRef(path={self._static_path}, dynamic={len(self._dynamic_segments)})"
        return f"FlatRef(path={self._static_path})"
