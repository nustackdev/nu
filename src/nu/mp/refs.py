"""``MpWorkerRef``: fabric ref that resolves an ``MpWorker`` by tag on ctx.

Mirrors ``RayServiceRef``. Tag is a single arbitrary hashable positional -
matches the shape ``Provide`` / ``ProvideList`` / ``ProvideDict`` used to
bind (no tag for singleton, int for ProvideList index, str/tuple for
ProvideDict key).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context import FabricRef
from nu.lang.sentinels import EMPTY, UNSET

from .resources import MpWorker


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = ["MpWorkerRef"]


class MpWorkerRef(FabricRef):
    """The ``MpWorker`` bound at ``tag`` on ctx.

    Examples::

        MpWorkerRef()                # -> ctx.get(MpWorker)
        MpWorkerRef(0)               # -> ctx.get(MpWorker, 0)
        MpWorkerRef("indexer-main")  # -> ctx.get(MpWorker, "indexer-main")
        MpWorkerRef(("shard", 0))    # -> ctx.get(MpWorker, ("shard", 0))
    """

    fabric = MpWorker

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
