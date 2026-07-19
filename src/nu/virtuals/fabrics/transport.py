"""``InMemoryTransport`` Nu fabric.

The in-process pub/sub bus that connects an ``InMemoryPublisher`` to one
or more ``InMemoryObserver``s. Trivial lifecycle -- construction is all
the setup needed; teardown is a no-op.

Bind it once at the actor / process scope; every ``InMemoryPublisher``
and ``InMemoryObserver`` provisioned inside that scope will pick the
same shared bus off ctx.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from virtuals.tkv.transport import InMemoryTransport as _InMemoryTransport


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["InMemoryTransport"]


class InMemoryTransport(_InMemoryTransport):
    """FabricLifecycle wrapper over ``virtuals.tkv.transport.InMemoryTransport``.

    Construction takes no ctx deps. ``setup`` / ``cleanup`` are no-ops --
    the transport is a plain data structure with thread-safe register /
    unregister / publish, no external resources to acquire or release.
    """

    def __init__(self) -> None:
        super().__init__()

    def setup(self, ctx: Context) -> None:
        """No-op: construction did all the work."""
        del ctx

    def cleanup(self) -> None:
        """No-op: nothing to release."""

    async def asetup(self, ctx: Context) -> None:
        """Async shim: setup is a no-op."""
        del ctx

    async def acleanup(self) -> None:
        """Async shim: cleanup is a no-op."""
