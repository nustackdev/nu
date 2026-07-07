"""The fabric axis of the Context: lifecycle interactions for provisioning.

- ``Fabric`` - empty marker protocol. Every ctx-bound service is a Fabric.
- ``FabricLifecycle(Fabric)`` - a Fabric with optional setup / cleanup
  (sync + async, all optional). What ``Provide`` installs into ctx.
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


__all__ = ["Fabric", "FabricLifecycle", "Provide", "ProvideDict", "ProvideList"]
