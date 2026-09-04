"""Generic UI Ref -- host-independent base for the widget kit.

A Ref is a Nu Ref whose storage is a client rendering surface (a browser
tab, in nudle's case). The class name is the wire identifier the client
uses to pick a renderer; the methods a Ref exposes (`store`, `append`,
`changed`, ...) decide which interactions it accepts.

Built on `StructuredRef` (parent chain, `_root_shape`). Address
resolution walks the on-tree parent chain and joins segments; hosts
that need a prefix (Page name, section slot path, ...) declare a
`_wire_prefix` classmethod on the root shape and this class picks it up.
Async-only: nu.ui is a browser fabric.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from nu.domains.shape import Slot
from nu.domains.shape.refs.base import StructuredRef
from nu.engine.structure import Declared


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.domains.shape.dsl import Shape
    from nu.lang.runtime import Runtime


__all__ = ["Ref"]


class Ref(StructuredRef):
    """Base for Refs backed by a client rendering surface. Async-only."""

    _requires_async = Declared(value=True, name="requires_async")

    def __init__(
        self,
        address: object,
        *,
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        # State lives in ``payload`` (part of the Term identity) so the base
        # ``Term._with_children`` carries it across a tree rewrite -- no override.
        self._payload["segment"] = address

    # --- wire-path resolution ------------------------------------------------

    async def _aresolve_address(self, rt: Runtime, nid: int) -> str:
        """Wire path for this Ref.

        Walks the on-tree parent chain (``rt.program.children``: ``[0]`` =
        structural parent, ``[1]`` = address) collecting segments, then asks
        the root shape for a prefix via `_wire_prefix()` (hosts opt in). The
        default -- no root prefix -- joins segments alone.
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
        if root is not None:
            prefix = getattr(root, "_wire_prefix", None)
            if prefix is not None:
                return ".".join([*prefix(), *segments])
        return ".".join(segments)

    # --- execution (async-only) ----------------------------------------------

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> Any:
            raise RuntimeError("nu.ui is async-only; use nu.arun")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            raise NotImplementedError(
                f"{type(self).__name__} is display-only; reading is not supported",
            )

        return athunk

    async def _aread(self, rt: Runtime, nid: int) -> Any:
        """Round-trip read of the live client value (input Refs override _acompile)."""
        from .session import Session

        session = rt.ctx.get(Session)
        path = await self._aresolve_address(rt, nid)
        return self._lift(await session.aread(path))

    # --- mount ---------------------------------------------------------------

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        """Class-level defaults shipped in the mount field entry.

        Override on Refs whose slice should be seeded without an explicit
        `write`. Empty by default; non-empty results are included under the
        optional `props` key on the mount field entry.
        """
        return {}

    @classmethod
    def slot(cls, **props: object) -> Self:
        return Slot(cls, props=props)  # type: ignore[return-value]
