"""nustd.ui.core -- host-independent UI fabric.

The reusable seam under nustd.ui:

- ``Ref``              -- generic UI Ref base (wire-path resolution, node lifecycle)
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
- ``Send`` /
  ``Write`` /
  ``Append`` /
  ``Remove`` /
  ``Clear`` /
  ``Init`` /
  ``Hide`` /
  ``Display`` /
  ``Changed``          -- interactions that flow over a Session on a Ref

A host builds on this core: it binds a ``Session`` and may add its own Ref
subclasses. What is on screen and which part of it shows is the program's,
drawn with ``nustd.ui.boot`` / ``route`` / ``Ref.showing``. The widget kit
under ``nustd.ui.refs`` targets this core, not any specific host.
"""

from .base import Ref
from .chains import Chain, boot_chains
from .interactions import (
    EVENT,
    Append,
    Changed,
    Clear,
    Display,
    Hide,
    Init,
    Remove,
    Send,
    Write,
)
from .protocol import (
    OP_DISPLAY,
    OP_ERROR,
    OP_HIDE,
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
    "EVENT",
    "OP_DISPLAY",
    "OP_ERROR",
    "OP_HIDE",
    "OP_INIT",
    "OP_NOTIFY",
    "OP_READ",
    "OP_REMOVE",
    "OP_WRITE",
    "Append",
    "Chain",
    "Changed",
    "Clear",
    "Display",
    "Frame",
    "Hide",
    "Init",
    "Ref",
    "Remove",
    "Section",
    "SectionRef",
    "Send",
    "Session",
    "Subscription",
    "Write",
    "WsSession",
    "WsSubscription",
    "boot_chains",
    "decode",
    "encode",
]
