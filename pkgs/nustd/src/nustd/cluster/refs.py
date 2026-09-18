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
    """The ``RayCluster`` bound on the Context.

    Notes:
        - Singleton. A cluster handle is bound untagged, so there is no
          address to give.
        - Reading is a lookup and nothing else. Connecting to ray, or
          starting it, is the ``RayCluster`` resource's own setup when it is
          provided.

    Yields:
        The bound ``RayCluster``. EMPTY when no cluster is bound.

    Example:
        Provide(RayCluster, {"address": "auto"},
            RayClusterRef().exists(),
        )
    """

    fabric = RayCluster


class RayServiceRef(FabricRef):
    """The ``RayService`` bound at ``tag`` on the Context.

    Args:
        tag: the address the service was bound under. Omit for the untagged
            singleton.

    Notes:
        - The tag is forwarded verbatim as a single positional to
          ``ctx.get``, so it mirrors whatever bound the service: nothing for
          a bare ``Provide``, the index for ``ProvideList``, the key for
          ``ProvideDict``.
        - ``None`` is a usable tag, distinct from omitting the tag.
        - Reading is a lookup and nothing else. No actor is spawned, and the
          actor of an already-provided service is not contacted.
        - The lookup runs against whichever Context is in force where the
          ref sits, so inside a ``Teleport`` body it reads the actor's own
          Context rather than the driver's.

    Yields:
        The bound ``RayService``. EMPTY when nothing is bound at ``tag``.

    Example:
        RayServiceRef()               # the untagged singleton
        RayServiceRef(0)              # a ProvideList index
        RayServiceRef("ledger-main")  # a ProvideDict key
        RayServiceRef(("ledger", 0))  # a ProvideDict tuple key
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
