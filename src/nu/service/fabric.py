"""ServiceFabric: holds one Python target instance for a Service.

Bound on ctx via Provide, tagged by the Service class. Setup/cleanup are
no-ops (nothing to open); the fabric only owns the reference to `target`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["ServiceFabric"]


class ServiceFabric:
    """Holds a single Python object whose attributes back a Service's methods.

    Any bound method / attribute on `target` may be exposed as an endpoint
    on the Service; the fabric just does the getattr and calls it.
    """

    def __init__(self, *, target: object) -> None:
        self.target = target

    def setup(self, ctx: Context) -> None:
        """No-op: the fabric owns nothing beyond `target`."""
        return None

    def cleanup(self) -> None:
        """No-op sibling of `setup`."""
        return None

    async def asetup(self, ctx: Context) -> None:
        """No-op async sibling of `setup`."""
        return None

    async def acleanup(self) -> None:
        """No-op async sibling of `cleanup`."""
        return None

    def resolve(self, name: str) -> object:
        """Return `getattr(target, name)` — the bound method / attribute to dispatch."""
        return getattr(self.target, name)
