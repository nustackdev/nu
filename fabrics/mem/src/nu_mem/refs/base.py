"""Dict substrate refs — navigate nested Python dicts under the v2 runtime.

``RefBase`` is the first concrete substrate against the shape Ref seam
(``_StructuredRef``): it fills the plug-points with nested-dict navigation.

A ref names one path segment - its address, held as ``children[0]`` and resolved
through the runtime like any child. The parent chain (``_parent_ref``) supplies
the segments above it; for the common shape-field case those are static slot
names, read off each parent's stored segment at compile time. The root dict is
bound in the Context under ``(dict, root_shape)`` and fetched with
``rt.ctx.get(dict, scope)``.

Read is the Ref's dual role (``compile`` returns the navigate-and-fetch thunk);
``write`` / ``erase`` resolve the address and mutate the parent container,
auto-creating intermediate dicts. Dynamic parent keys (a computed segment above
the leaf) are deferred to the FlatRef / inline-refs pass.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import EMPTY
from nu.domains.shape.refs.base import _StructuredRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.domains.shape.dsl import Shape
    from nu.lang.runtime import Runtime


__all__ = ["RefBase"]


class RefBase[T](_StructuredRef):
    """Base for all dict-substrate refs: nested-dict navigation, no backend.

    The root dict comes from the Context via ``rt.ctx.get(dict, root_shape)``.
    """

    def __init__(
        self,
        address: object,
        *,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self._segment = address  # raw static segment, for parent-chain path building

    # --- path building -------------------------------------------------------

    def _parent_path(self) -> tuple:
        """Static segments of the parent chain, root-first (excludes self)."""
        segs: list[object] = []
        ref = self._parent_ref
        while ref is not None:
            segs.append(ref._segment)  # type: ignore[attr-defined]
            ref = ref._parent_ref
        segs.reverse()
        return tuple(segs)

    def _root_data(self, rt: Runtime) -> object:
        """The root dict bound in the Context, scoped to this ref's root shape."""
        scope = self.get_root_shape()
        return rt.ctx.get(dict, scope) if scope is not None else rt.ctx.get(dict)

    # --- read (the dual role) ------------------------------------------------

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        address = children[0]
        parents = self._parent_path()

        def thunk(rt: Runtime) -> object:
            cur = self._root_data(rt)
            try:
                for k in parents:
                    cur = cur[k]  # type: ignore[index]
                cur = cur[address(rt)]  # type: ignore[index]
            except (KeyError, IndexError, TypeError):
                return EMPTY
            return self.coerce(cur)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        address = children[0]
        parents = self._parent_path()

        async def athunk(rt: Runtime) -> object:
            cur = self._root_data(rt)
            try:
                for k in parents:
                    cur = cur[k]  # type: ignore[index]
                cur = cur[await address(rt)]  # type: ignore[index]
            except (KeyError, IndexError, TypeError):
                return EMPTY
            return await self.acoerce(cur)

        return athunk

    # --- write / erase -------------------------------------------------------

    def write(self, rt: Runtime, value: object, nid: int) -> None:
        """Write ``value`` through this ref, vivifying intermediate dicts."""
        container = self._fetch_parent(rt)
        container[self.address(rt, nid)] = value  # type: ignore[index]

    async def awrite(self, rt: Runtime, value: object, nid: int) -> None:
        """Async sibling of :meth:`write`."""
        container = self._fetch_parent(rt)
        container[await self.aaddress(rt, nid)] = value  # type: ignore[index]

    def erase(self, rt: Runtime, nid: int) -> None:
        """Remove this ref's slot from its parent container, if present."""
        container = self._fetch_parent(rt)
        key = self.address(rt, nid)
        if isinstance(container, dict) and key in container:
            del container[key]

    async def aerase(self, rt: Runtime, nid: int) -> None:
        """Async sibling of :meth:`erase`."""
        container = self._fetch_parent(rt)
        key = await self.aaddress(rt, nid)
        if isinstance(container, dict) and key in container:
            del container[key]

    def _fetch_parent(self, rt: Runtime) -> object:
        """Navigate to the parent container, auto-creating intermediate dicts."""
        cur = self._root_data(rt)
        for k in self._parent_path():
            if isinstance(cur, dict) and k not in cur:
                cur[k] = {}
            cur = cur[k]  # type: ignore[index]
        return cur
