"""Base class for nudle Refs.

A nudle Ref is a Nu Ref whose storage is a ws connection to a browser
tab. The class name is the wire identifier the browser uses to pick a
renderer; the methods a Ref exposes (`store`, `append`, `fetch`,
`changed`, ...) decide which interactions it accepts.

Display Refs (server -> tab) override `store` / `append`. Input Refs
(tab -> server) also override `aeval` to fetch the live value through
session.aread, and `changed` to register a Subscription.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Self

from nu import Nu
from nu.shapes.refs import Ref
from nu.shapes.shape.slot import Slot
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu import Context


__all__ = ["NudleRef"]


class NudleRef(Ref[Any]):
    """Base for Refs that live in a browser tab over ws."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    async def afetch_parent(self, ctx: Context) -> object:
        raise NotImplementedError("nudle refs do not expose a parent view")

    async def aresolve(self, ctx: Context) -> str:
        return await self.aresolve_address(ctx)

    async def aresolve_address(self, ctx: Context) -> str:
        """Wire path for this Ref.

        - root is an Index: slot name alone (structural Refs at top).
        - root is a Page: "<PageShapeName>.<slot>" (namespaced per page).
        """
        from nu import runtime

        addr = self.address
        if isinstance(addr, Nu):
            addr = await runtime.afirst(addr, ctx)
        root = self.get_root_shape()
        if root is not None and getattr(root, "_is_nudle_page", False):
            return f"{root.__name__}.{addr}"
        return str(addr)

    def eval(self, ctx: Context) -> Any:
        raise RuntimeError("nudle is async-only; use aexecute")

    async def aeval(self, ctx: Context) -> Any:
        raise NotImplementedError(
            f"{type(self).__name__} is display-only; reading is not supported",
        )

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        """Class-level defaults to ship in the mount field entry.

        Override on Refs whose slice should be seeded without an explicit
        `write`. Empty by default; non-empty results are included under the
        optional `props` key on the mount field entry.
        """
        return {}

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]
