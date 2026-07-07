"""``Fabric`` and ``FabricLifecycle``: the two protocol tiers.

Every ctx-bound service is a **Fabric** - an addressable space that resolves
its own Refs and carries out the Interactions over them. The Context fabric is
the built-in one; Ray, Virtuals, Invisibles, Nudle, Mem, and every user
service all satisfy the same base protocol.

- ``Fabric`` - empty marker Protocol. Every ctx-bound thing is a Fabric;
  ``isinstance(x, Fabric)`` is intentionally trivially true, the protocol just
  labels intent for readers and tooling.
- ``FabricLifecycle(Fabric)`` - a Fabric with optional setup / cleanup. This
  is what ``Provide`` / ``ProvideList`` / ``ProvideDict`` install into ctx:
  the bracket constructs the instance, awaits setup, binds, and tears down on
  exit. All four lifecycle methods are optional - implement whichever fit,
  the ``Provide`` machinery falls back sensibly:

    def setup(self, ctx): ...       # sync run, or async fallback
    def cleanup(self): ...
    async def asetup(self, ctx): ... # async run (preferred when defined)
    async def acleanup(self): ...

The two-tier split lets a service opt in gradually. A stateless codec bound
once is a plain ``Fabric`` - no lifecycle. A ray cluster, a rocksdb handle,
a websocket connection are ``FabricLifecycle`` - they need setup and
teardown. The distinction is documentation, not enforcement.

``setup`` receives the outer ctx - everything bound by enclosing ``Provide``
brackets is already visible. That is the dependency-injection channel: an
inner FabricLifecycle reads its deps from ctx during its own setup, which is
guaranteed to run *after* every enclosing ``Provide`` has bound.

Example::

    class Codec(Fabric):                      # no lifecycle needed
        def __init__(self, kind): self.kind = kind

    class Storage(FabricLifecycle):
        def __init__(self, path): self.path = path
        def setup(self, ctx):
            self.codec = ctx.get(Codec)       # DI happens here
            self.db = open(self.path, codec=self.codec)
        def cleanup(self):
            self.db.close()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["Fabric", "FabricLifecycle"]


@runtime_checkable
class Fabric(Protocol):
    """Empty marker Protocol - every ctx-bound service is a Fabric.

    An addressable space that hosts its own Refs and interactions. The empty
    protocol carries no methods; the type is documentation for tooling and
    readers. Subclass or extend with ``FabricLifecycle`` when the service
    needs setup / teardown.
    """


@runtime_checkable
class FabricLifecycle(Fabric, Protocol):
    """A Fabric with optional setup / cleanup, both sync and async.

    ``Provide`` / ``ProvideList`` / ``ProvideDict`` install a
    ``FabricLifecycle`` into ctx for a body's duration: construct, setup,
    bind, run body, teardown in reverse (LIFO). Each method is optional -
    async run prefers ``asetup`` / ``acleanup`` when defined and falls back
    to the sync variants otherwise.
    """

    def setup(self, ctx: Context) -> None: ...
    def cleanup(self) -> None: ...
    async def asetup(self, ctx: Context) -> None: ...
    async def acleanup(self) -> None: ...
