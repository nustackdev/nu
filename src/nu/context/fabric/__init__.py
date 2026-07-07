"""The fabric axis of the Context: bindings, existence, and lifecycle.

- ``Fabric`` - empty marker protocol. Every ctx-bound thing is a Fabric.
- ``FabricLifecycle(Fabric)`` - a Fabric with optional setup / cleanup
  (sync + async, all optional). What ``Provide`` installs into ctx.
- ``FabricRef`` - Ref that self-yields a Fabric bound on the Context, or
  ``EMPTY`` when nothing is bound. Subclass and set ``fabric = SomeFabric``
  to name a typed binding; add ``method_query`` / ``method_action`` /
  ``method_command`` descriptors for in-tree dispatch.
- ``FabricExistsQuery`` - explicit existence check, since a bound ``EMPTY``
  aliases "unbound" under the dual-role read.
- ``Provide`` / ``ProvideList`` / ``ProvideDict`` - Brackets that construct
  a fabric on entry, bind it on ctx, and tear down in reverse on exit.

Both sync and async lifecycles are supported natively - the async runtime
prefers ``asetup`` / ``acleanup`` when defined and falls back to sync
``setup`` / ``cleanup``. The Nu tree is the DI system: an inner fabric
reads its deps from ctx during its own setup.
"""

from __future__ import annotations

from .lifecycle import Provide, ProvideDict, ProvideList
from .protocol import Fabric, FabricLifecycle
from .queries import FabricExistsQuery
from .refs import FabricRef


__all__ = [
    "Fabric",
    "FabricExistsQuery",
    "FabricLifecycle",
    "FabricRef",
    "Provide",
    "ProvideDict",
    "ProvideList",
]
