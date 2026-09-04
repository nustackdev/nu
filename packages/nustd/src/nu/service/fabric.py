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
    """Holds a single Python object whose attributes back a Service's endpoints.

    Bound on the context by ``nu.service.bind``, tagged with the Service class,
    so the interactions can find it from the owning Service named in their Ref.

    Notes:
        - Any attribute on ``target`` can be an endpoint. The fabric does the
          getattr and hands the result back; the interaction calls it.
        - Nothing is opened or closed. Setup and cleanup exist only to satisfy
          the ``Provide`` lifecycle and do nothing, so the object's lifetime is
          the caller's.
        - One target per fabric. Two targets means two Services, two binds.
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
        """Fetch the attribute an endpoint dispatches to off the target.

        Notes:
            - Nothing is cached, so an attribute replaced on the target between
              calls takes effect on the next call.
            - A missing attribute raises AttributeError at run. Endpoint names
              are never checked when the Service class is declared.
        """
        return getattr(self.target, name)
