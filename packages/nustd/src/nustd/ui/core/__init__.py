"""nustd.ui.core -- host-independent UI fabric.

The reusable seam under nustd.ui:

- ``Ref``              -- generic UI Ref base (mount protocol, wire-path resolution)
- ``Section`` /
  ``SectionRef``       -- shape-based container primitive + substrate ref
- ``Session`` /
  ``Subscription``     -- abstract wire transport (the seam hosts target)
- ``WsSession`` /
  ``WsSubscription``   -- that transport over a websocket, shared by ws hosts
- ``Chain`` /
  ``boot_chains``      -- a Shape's slots as the init frames that seed a tree
- ``Frame`` /
  ``encode/decode``    -- wire protocol envelope
- ``Write`` /
  ``Append`` /
  ``Remove`` /
  ``Changed``          -- interactions that flow over a Session on a Ref

Concrete hosts (``nustd.ui.nudle`` today, potentially others) build on this
core: they bind a ``Session``, declare a page/routing model, and add any
host-specific Ref subclasses. The widget kit under ``nustd.ui.refs`` targets
this core, not any specific host.
"""

from .base import Ref
from .chains import Chain, boot_chains
from .interactions import Append, Changed, Remove, Write
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
from .session import Session, Subscription, WsSession, WsSubscription


__all__ = [
    "OP_ERROR",
    "OP_INIT",
    "OP_NOTIFY",
    "OP_READ",
    "OP_REMOVE",
    "OP_WRITE",
    "Append",
    "Chain",
    "Changed",
    "Frame",
    "Ref",
    "Remove",
    "Section",
    "SectionRef",
    "Session",
    "Subscription",
    "Write",
    "WsSession",
    "WsSubscription",
    "boot_chains",
    "decode",
    "encode",
]
