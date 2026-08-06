"""Dict substrate refs: navigate nested Python dicts under the runtime.

``RefBase`` is the first concrete substrate against the shape Ref seam
(``StructuredRef``): it fills the plug-points with nested-dict navigation.

A ref names one path segment, its address, held as ``children[1]`` and resolved
through the runtime like any child. The parent chain lives on the tree at
``children[0]`` (walked via ``parent_ref``); for the common shape-field case
those are static slot names, read off each parent's stored segment at compile
time. The root dict is bound in the Context under ``(dict, root_shape)`` and
fetched with ``rt.ctx.get(dict, scope)``.

Read is the Ref's dual role (``compile`` returns the navigate-and-fetch thunk);
``write`` / ``erase`` resolve the address and mutate the parent container,
auto-creating intermediate dicts. Dynamic parent keys (a computed segment above
the leaf) resolve through the FlatRef / inline-refs pass.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.domains.shape.refs.base import StructuredRef
from nu.lang import EMPTY


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.domains.shape.dsl import Shape
    from nu.lang.runtime import Runtime


__all__ = ["RefBase"]


T = TypeVar("T")


class RefBase(StructuredRef, Generic[T]):
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
        # raw static segment, in payload so it rides base with_children
        self._payload["segment"] = address

    # --- path building -------------------------------------------------------

    def _parent_path(self) -> tuple:
        """Static segments of the parent chain, root-first (excludes self)."""
        segs: list[object] = []
        ref = self._parent
        while ref is not None:
            segs.append(ref._payload.get("segment"))  # type: ignore[attr-defined]
            ref = ref._parent
        segs.reverse()
        return tuple(segs)

    def _root_data(self, rt: Runtime) -> object:
        """The root dict bound in the Context, scoped to this ref's root shape."""
        scope = self._root_shape
        return rt.ctx.get(dict, scope) if scope is not None else rt.ctx.get(dict)

    def _resolve_path(self, rt: Runtime, nid: int) -> tuple:
        """Full key path, root-first, resolving every level's address at runtime.

        Walks the on-tree parent chain via ``rt.program.children`` (``[0]`` =
        structural parent, ``[1]`` = this level's address) and evaluates each
        level's address child. Because the parent lives on the tree, a *dynamic*
        parent key (a Ref or Query above the leaf) resolves here like any other
        child - no static-segment shortcut, no inline pass needed.
        """
        segs: list[object] = []
        cur = nid
        while True:
            kids = rt.program.children[cur]
            segs.append(rt.eval(kids[1]))
            parent = kids[0]
            if not isinstance(rt.program.terms[parent], StructuredRef):
                break  # parent is the ANCHOR -> chain root
            cur = parent
        segs.reverse()
        return tuple(segs)

    async def _aresolve_path(self, rt: Runtime, nid: int) -> tuple:
        """Async sibling of :meth:`_resolve_path`."""
        segs: list[object] = []
        cur = nid
        while True:
            kids = rt.program.children[cur]
            segs.append(await rt.aeval(kids[1]))
            parent = kids[0]
            if not isinstance(rt.program.terms[parent], StructuredRef):
                break
            cur = parent
        segs.reverse()
        return tuple(segs)

    # --- read (the dual role) ------------------------------------------------

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            cur = self._root_data(rt)
            try:
                for k in self._resolve_path(rt, nid):
                    cur = cur[k]  # type: ignore[index]
            except (KeyError, IndexError, TypeError):
                return EMPTY
            return self._lift(cur)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            cur = self._root_data(rt)
            try:
                for k in await self._aresolve_path(rt, nid):
                    cur = cur[k]  # type: ignore[index]
            except (KeyError, IndexError, TypeError):
                return EMPTY
            return await self._alift(cur)

        return athunk

    # --- write / erase -------------------------------------------------------

    def _write(self, rt: Runtime, value: object, nid: int) -> None:
        """Write ``value`` through this ref, vivifying intermediate dicts."""
        value = self._lower(value)
        path = self._resolve_path(rt, nid)
        cur = self._root_data(rt)
        for k in path[:-1]:
            if isinstance(cur, dict) and k not in cur:
                cur[k] = {}
            cur = cur[k]  # type: ignore[index]
        cur[path[-1]] = value  # type: ignore[index]

    async def _awrite(self, rt: Runtime, value: object, nid: int) -> None:
        """Async sibling of :meth:`write`."""
        value = await self._alower(value)
        path = await self._aresolve_path(rt, nid)
        cur = self._root_data(rt)
        for k in path[:-1]:
            if isinstance(cur, dict) and k not in cur:
                cur[k] = {}
            cur = cur[k]  # type: ignore[index]
        cur[path[-1]] = value  # type: ignore[index]

    def _erase(self, rt: Runtime, nid: int) -> None:
        """Remove this ref's slot from its parent container, if present."""
        path = self._resolve_path(rt, nid)
        cur = self._root_data(rt)
        for k in path[:-1]:
            if not (isinstance(cur, dict) and k in cur):
                return
            cur = cur[k]  # type: ignore[index]
        if isinstance(cur, dict) and path[-1] in cur:
            del cur[path[-1]]

    async def _aerase(self, rt: Runtime, nid: int) -> None:
        """Async sibling of :meth:`erase`."""
        path = await self._aresolve_path(rt, nid)
        cur = self._root_data(rt)
        for k in path[:-1]:
            if not (isinstance(cur, dict) and k in cur):
                return
            cur = cur[k]  # type: ignore[index]
        if isinstance(cur, dict) and path[-1] in cur:
            del cur[path[-1]]

    def _fetch_parent(self, rt: Runtime) -> object:
        """Navigate to the parent container, auto-creating intermediate dicts."""
        cur = self._root_data(rt)
        for k in self._parent_path():
            if isinstance(cur, dict) and k not in cur:
                cur[k] = {}
            cur = cur[k]  # type: ignore[index]
        return cur
