"""Base class for nudle Refs.

A nudle Ref is a Nu Ref whose storage is a ws connection to a browser
tab. The class name is the wire identifier the browser uses to pick a
renderer; the methods a Ref exposes (`store`, `append`, `changed`, ...)
decide which interactions it accepts.

Display Refs (server -> tab) override `store` / `append`. Input Refs
(tab -> server) also override `acompile` to fetch the live value through
`session.aread` (via `_aread`), and `changed` to register a Subscription.

Built on `StructuredRef`, the storage-agnostic shape-fabric Ref seam:
it supplies the parent chain (`_parent_ref`), `owner_shape`, and
`get_root_shape`; nudle fills the substrate plug-point `aresolve_address`
(the wire path) and the async read path. nudle is async-only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from nu.domains.shape import Slot
from nu.domains.shape.refs.base import StructuredRef
from nu.engine.structure import Declared


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.domains.shape.dsl import Shape
    from nu.lang.runtime import Runtime


__all__ = ["NudleRef"]


class NudleRef(StructuredRef):
    """Base for Refs that live in a browser tab over ws. Async-only."""

    _requires_async = Declared(value=True, name="requires_async")

    def __init__(
        self,
        address: object,
        *,
        parent_ref: NudleRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        # State lives in ``payload`` (part of the Term identity) so the base
        # ``Term._with_children`` carries it across a tree rewrite — no override.
        self._payload["segment"] = address

    # --- wire-path resolution ------------------------------------------------

    async def _aresolve_address(self, rt: Runtime, nid: int) -> str:
        """Wire path for this Ref.

        Resolves every level's address AT RUNTIME by walking the on-tree parent
        chain (``rt.program.children``: ``[0]`` = structural parent, ``[1]`` =
        address), so a dynamic parent key resolves like any other child. Then:
        - root is an Index: join segments alone ("title", "nav").
        - root is a Page: prefix "<PageShapeName>." and join.
        - root is a Section: look up the Section's mount point on a Page
          via `Section._nudle_mount` and prefix
          "<PageShapeName>.<section_slot_path>." then join segments.
        """
        segments: list[str] = []
        cur = nid
        while True:
            kids = rt.program.children[cur]
            segments.append(str(await rt.aeval(kids[1])))
            parent = kids[0]
            if not isinstance(rt.program.terms[parent], StructuredRef):
                break  # parent is the ANCHOR -> chain root
            cur = parent
        segments.reverse()

        root = self._root_shape
        if root is not None and getattr(root, "_is_nudle_page", False):
            return ".".join([root.__name__, *segments])
        if root is not None and getattr(root, "_is_nudle_section", False):
            mount = getattr(root, "_nudle_mount", None)
            if mount is None:
                raise RuntimeError(
                    f"Section {root.__name__} has no mount point. "
                    "Did you forget to declare it on a Page slot?",
                )
            page_cls, slot_path = mount
            return ".".join([page_cls.__name__, *slot_path, *segments])
        return ".".join(segments)

    # --- execution (async-only) ----------------------------------------------

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> Any:
            raise RuntimeError("nudle is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            raise NotImplementedError(
                f"{type(self).__name__} is display-only; reading is not supported",
            )

        return athunk

    async def _aread(self, rt: Runtime, nid: int) -> Any:
        """Round-trip read of the live browser value (input Refs override acompile)."""
        from nu.ui.nudle.py.session import NudleSession

        session = rt.ctx.get(NudleSession)
        path = await self._aresolve_address(rt, nid)
        return self._lift(await session.aread(path))

    # --- mount ---------------------------------------------------------------

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        """Class-level defaults to ship in the mount field entry.

        Override on Refs whose slice should be seeded without an explicit
        `write`. Empty by default; non-empty results are included under the
        optional `props` key on the mount field entry.
        """
        return {}

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]
