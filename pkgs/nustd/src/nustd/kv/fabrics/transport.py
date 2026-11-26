"""``InMemoryTransport`` Nu fabric.

The in-process pub/sub bus that connects an ``InMemoryPublisher`` to one
or more ``InMemoryObserver``s. Trivial lifecycle -- construction is all
the setup needed; teardown is a no-op.

Bind it once at the actor / process scope; every ``InMemoryPublisher``
and ``InMemoryObserver`` provisioned inside that scope will pick the
same shared bus off ctx.
"""

from __future__ import annotations

from nu.context import Fabric
from virtuals.tkv.transport import InMemoryTransport as _InMemoryTransport


__all__ = ["InMemoryTransport"]


class InMemoryTransport(_InMemoryTransport, Fabric):
    """Fabric wrapper over ``virtuals.tkv.transport.InMemoryTransport``.

    Construction takes no ctx deps. ``setup`` / ``cleanup`` are no-ops --
    the transport is a plain data structure with thread-safe register /
    unregister / publish, no external resources to acquire or release.
    """

    def __init__(self) -> None:
        super().__init__()
