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
    """The ``MpWorker`` bound at ``tag`` on the Context.

    Args:
        tag: the address the worker was bound under. Omit for the untagged
            singleton.

    Notes:
        - The tag is forwarded verbatim as a single positional to
          ``ctx.get``, so it mirrors whatever bound the worker: nothing for a
          bare ``Provide``, the index for ``ProvideList``, the key for
          ``ProvideDict``.
        - ``None`` is a usable tag, distinct from omitting the tag.
        - Reading is a lookup and nothing else. No process is spawned, and
          the child of an already-provided worker is not contacted.
        - The lookup runs against whichever Context is in force where the
          ref sits, so inside a ``Teleport`` body it reads the worker
          process's own Context rather than the parent's.

    Yields:
        The bound ``MpWorker``. EMPTY when nothing is bound at ``tag``.

    Example:
        MpWorkerRef()                # the untagged singleton
        MpWorkerRef(0)               # a ProvideList index
        MpWorkerRef("indexer-main")  # a ProvideDict key
        MpWorkerRef(("shard", 0))    # a ProvideDict tuple key
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
