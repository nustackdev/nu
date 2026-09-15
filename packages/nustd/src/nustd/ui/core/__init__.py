"""nustd.ui.core -- host-independent UI fabric.

The reusable seam under nustd.ui:

- ``Ref``              -- generic UI Ref base (mount protocol, wire-path resolution)
- ``Section`` /
  ``SectionRef``       -- shape-based container primitive + substrate ref
- ``Session`` /
  ``Subscription``     -- abstract wire transport (concrete impls in host modules)
- ``Frame`` /
  ``encode/decode``    -- wire protocol envelope
- ``Write`` /
  ``Append`` /
  ``Changed``          -- interactions that flow over a Session on a Ref

Concrete hosts (``nustd.ui.nudle`` today, potentially others) build on this
core: they provide a ``Session`` implementation, a page/routing model,
and any host-specific Ref subclasses. The widget kit under
``nustd.ui.refs`` targets this core, not any specific host.
"""

from .base import Ref
from .interactions import Append, Changed, Write
from .protocol import (
    OP_ERROR,
    OP_INIT,
    OP_NOTIFY,
    OP_READ,
    OP_REMOVE,
    OP_WRITE,
    Frame,
    decode,
    encode,
)
from .section import Section, SectionRef
from .session import Session, Subscription


__all__ = [
    "OP_ERROR",
    "OP_INIT",
    "OP_NOTIFY",
    "OP_READ",
    "OP_REMOVE",
    "OP_WRITE",
    "Append",
    "Changed",
    "Frame",
    "Ref",
    "Section",
    "SectionRef",
    "Session",
    "Subscription",
    "Write",
    "decode",
    "encode",
]
