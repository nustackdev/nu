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

    ``_address`` / ``_aaddress`` evaluate the address child given the Ref's own
    node id, the same resolution the dual-role read uses. Exposed so write ops
    can resolve the target through the Ref rather than reaching past it.
    """

    def _address(self, rt: Runtime, nid: int) -> object:
        """Resolve this Ref's address; ``nid`` is the Ref's own node id."""
        return rt.eval(rt.program.children[nid][0])

    async def _aaddress(self, rt: Runtime, nid: int) -> object:
        """Async sibling of :meth:`_address`."""
        return await rt.aeval(rt.program.children[nid][0])
