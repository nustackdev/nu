"""The fabric axis of the Context: bindings, existence, and lifecycle.

- ``Fabric`` - the base class of every provided fabric: setup / cleanup
  (sync + async) with no-op defaults, and the ``async_only`` flag. What
  ``Provide`` installs into ctx must subclass it.
- ``FabricRef`` - Ref that self-yields a Fabric bound on the Context, or
  ``NULL`` when nothing is bound. Subclass and set ``fabric = SomeFabric``
  to name a typed binding.
- ``FabricExists`` - explicit existence check, since a bound ``NULL``
  aliases "unbound" under the dual-role read.
- ``Provide`` / ``ProvideList`` / ``ProvideDict`` - Brackets that construct
  a fabric on entry, bind it on ctx, and tear down in reverse on exit.

Both sync and async lifecycles are supported natively - the async runtime
calls ``asetup`` / ``acleanup``, which default to the sync ``setup`` /
``cleanup``. The Nu tree is the DI system: an inner fabric
reads its deps from ctx during its own setup.
"""

from __future__ import annotations

from .base import Fabric
from .lifecycle import Provide, ProvideDict, ProvideList, With
from .queries import FabricExists
from .refs import FabricRef


__all__ = [
    "Fabric",
    "FabricExists",
    "FabricRef",
    "Provide",
    "ProvideDict",
    "ProvideList",
    "With",
]
