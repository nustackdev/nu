"""Shared base for Context-fabric Refs.

Both ``AttrRef`` and ``FabricRef`` are Refs whose sole child *is* their
address: it is resolved through the runtime like any other child, and the read
is the dual role. This base spells that pattern once. The concrete subclasses
plug in what the address means (attr key / fabric type) and how the fabric
answers a read.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Ref


if TYPE_CHECKING:
    from nu.lang.runtime import Runtime


__all__ = ["_ContextRef"]


class _ContextRef(Ref):
    """A Context Ref whose address is its sole child, resolved through the runtime.

    The shared base under ``AttrRef`` and ``FabricRef``. Both are Refs whose
    one child *is* the address, which means the address is an ordinary Nu
    expression and can be computed rather than fixed at write time. This base
    spells that pattern once; a subclass decides what the address means (a
    key in ``ctx.attrs``, a fabric type) and how a read is answered.

    Notes:
        - Address resolution is given the Ref's own node id, so it is the
          same resolution the dual-role read performs. Write ops go through
          it rather than reaching past the Ref, which is what keeps the write
          mechanism with the fabric.
    """

    def _address(self, rt: Runtime, nid: int) -> object:
        """Resolve this Ref's address; ``nid`` is the Ref's own node id."""
        return rt.eval(rt.program.children[nid][0])

    async def _aaddress(self, rt: Runtime, nid: int) -> object:
        """Async sibling of :meth:`_address`."""
        return await rt.aeval(rt.program.children[nid][0])
