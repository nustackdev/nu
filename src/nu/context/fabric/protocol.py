"""``Fabric``: a marker Protocol for resources that host refs + interactions.

A Fabric is an addressable space: it resolves Refs and carries out
Interactions over them. Ray, Virtuals, Invisibles, Nudle, Mem - all are
Fabrics. The Context fabric is the built-in one, its Refs are ``AttrRef`` /
``ServiceRef``, its interactions are ``SetCommand`` / ``DeleteCommand`` /
``Provide`` / method dispatch.

Structurally a Fabric is a ``Resource`` (setup / cleanup) - Fabrics get
provisioned into a Context by a ``Provide`` bracket like any other resource.
The ``Fabric`` marker exists to say "this Resource is a fabric", so tooling
and readers can distinguish a fabric (Ray cluster, invisibles transport) from
a plain resource (codec, observer).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["Fabric"]


@runtime_checkable
class Fabric(Protocol):
    """A resource that acts as an addressable space for its own Refs.

    Same shape as ``Resource`` - the split is semantic. A Fabric hosts one or
    more concrete Ref classes and one or more Interactions over them; a plain
    Resource does not. Both sync and async lifecycle methods are optional.
    """

    def setup(self, ctx: Context) -> None: ...
    def cleanup(self) -> None: ...
    async def asetup(self, ctx: Context) -> None: ...
    async def acleanup(self) -> None: ...
