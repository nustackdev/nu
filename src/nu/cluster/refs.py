"""Refs into the ray fabric: ``RayClusterRef`` and ``RayServiceRef``.

Ray is a compute fabric: locations are actor processes, addresses are tags,
interactions are ``Teleport`` (execute a tree there). Both refs subclass
``FabricRef`` so ``ctx.get`` is the resolution mechanism.

- ``RayClusterRef`` reads the bound ``RayCluster`` on the Context. Singleton;
  no tag.
- ``RayServiceRef(*tag)`` reads the ``RayService`` bound at that tag. Tags
  are arbitrary hashable positional args - a plain string for a singleton
  (``RayServiceRef("ledger-main")``), a tuple for a keyed fleet
  (``RayServiceRef(("ledger", 0))``), etc. The tag is stored in payload and
  forwarded verbatim to ``ctx.get(RayService, *tag)``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context import FabricRef
from nu.lang.sentinels import EMPTY, UNSET

from .resources import RayCluster, RayService


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["RayClusterRef", "RayServiceRef"]


class RayClusterRef(FabricRef):
    """The bound ``RayCluster`` on ctx. Singleton."""

    fabric = RayCluster


class RayServiceRef(FabricRef):
    """A ``RayService`` bound at an arbitrary tag on ctx.

    ``tag`` is passed verbatim as a single positional to ``ctx.get`` -
    matches the shape ``Provide`` / ``ProvideList`` / ``ProvideDict`` used to
    bind (int index for ``ProvideList``, dict key for ``ProvideDict``). Pass
    no tag for the untagged singleton bound by a bare ``Provide``.

    Examples::

        RayServiceRef()                 # -> ctx.get(RayService)
        RayServiceRef(0)                # -> ctx.get(RayService, 0)
        RayServiceRef("ledger-main")    # -> ctx.get(RayService, "ledger-main")
        RayServiceRef(("ledger", 0))    # -> ctx.get(RayService, ("ledger", 0))
    """

    fabric = RayService

    def __init__(self, tag: object = UNSET) -> None:
        super().__init__()
        self._payload["tag"] = tag

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        service = children[0]
        raw = self._payload["tag"]
        tag: tuple[object, ...] = () if raw is UNSET else (raw,)

        def thunk(rt: Runtime) -> object:
            svc = service(rt)
            return rt.ctx.get(svc, *tag) if rt.ctx.has(svc, *tag) else EMPTY

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        service = children[0]
        raw = self._payload["tag"]
        tag: tuple[object, ...] = () if raw is UNSET else (raw,)

        async def athunk(rt: Runtime) -> object:
            svc = await service(rt)
            return rt.ctx.get(svc, *tag) if rt.ctx.has(svc, *tag) else EMPTY

        return athunk
