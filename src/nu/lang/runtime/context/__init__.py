"""Nu context - the environment one task runs against.

Two stores, each owning its own scoping:

- ``ctx.attrs`` - flat name store; interactions bind here, ``Attr`` reads.
- ``ctx.fabrics`` - typed fabric bindings with scope tags and optional
  predicate guards; execution resources live here.

Typed Refs (Attr, FabricRef and their Form-mixed variants) and their
ScalarQuery ops are deferred until the Form layer lands in nu.
"""

from .attributes import Attributes
from .context import Context
from .fabrics import Fabrics


__all__ = ["Attributes", "Context", "Fabrics"]
