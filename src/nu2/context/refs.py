"""AttrRef: the Context-fabric Ref.

The simplest Ref shape - a name-keyed slot in ``ctx.attrs``, no Shape, no
parent chain. The Context fabric's own Ref: it reads its value from
``ctx.attrs`` (the dual-role self-yield) and writes it there when a Command
holds it in a mutation slot. Short-lived primitives live here: loop counters,
accumulators, markers.

Every fabric owns its Ref this way. There is no fabric-less Ref; the abstract
``Ref`` kind in ``nu2.lang`` carries only sort and cardinality, and concrete
Refs like this one supply the read / write against their fabric.

v1 reference: ``src/nu/context/attr_refs.py`` (AttrRef).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import Ref
from nu2.lang.sentinels import EMPTY


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = ["AttrRef"]


class AttrRef(Ref):
    """A name-keyed Ref into the ``ctx.attrs`` store.

    Reads yield the bound value (EMPTY when unbound). Writes and erases go
    through this Ref - the fabric owns the mechanism, so a Command never
    touches ``ctx.attrs`` itself, only ``ref.write`` / ``ref.erase``.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        name = self.payload["name"]

        def thunk(rt: Runtime) -> object:
            return rt.ctx.attrs.get(name, EMPTY)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        name = self.payload["name"]

        async def athunk(rt: Runtime) -> object:
            return rt.ctx.attrs.get(name, EMPTY)

        return athunk

    def write(self, rt: Runtime, value: object) -> None:
        """Write ``value`` to this Ref's slot in the attrs fabric."""
        rt.ctx.attrs[self.payload["name"]] = value

    def erase(self, rt: Runtime) -> None:
        """Remove this Ref's slot from the attrs fabric, if present."""
        name = self.payload["name"]
        if name in rt.ctx.attrs:
            del rt.ctx.attrs[name]
