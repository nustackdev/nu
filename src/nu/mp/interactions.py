"""``Teleport``: ship the body to an ``MpWorker`` child process for execution.

Same shape as ``nu.cluster.Teleport`` but targets ``MpWorker`` and works on
both sync and async runtimes - the parent-side pipe read/write is blocking
either way (async wraps it in ``asyncio.to_thread``).

Policy: captures the body term (slot 0), resolves an ``MpWorker`` from ctx
by tag, and calls ``worker.execute(body_term)`` on it.

``target`` is a single hashable used verbatim as the tag; omit (``UNSET``)
for the untagged singleton. ``target=None`` is a legitimate tag.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Attr, Cardinality, Policy
from nu.lang.sentinels import UNSET

from .resources import MpWorker


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterator

    from nu.lang import Nu
    from nu.lang.runtime import Runtime


__all__ = ["Teleport"]


def _one_sync(value: object) -> Iterator:
    if value is not None:
        yield value


async def _one_async(value: object) -> AsyncIterator:
    if value is not None:
        yield value


class Teleport(Policy):
    """Ship the body to an ``MpWorker`` for execution in that child process.

    Args:
        body: The Nu to execute in the worker. Captured as a term.
        target: Tag identifying the ``MpWorker`` on ctx.
        carry: If True, copy the parent's ``ctx.attrs`` to the worker's
            Context before executing there.
    """

    def __init__(self, body: Nu, *, target: object = UNSET, carry: bool = False) -> None:
        super().__init__(body)
        self._payload["target"] = target
        self._payload["carry"] = carry

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body_term = self._children[0]
        target = self._payload["target"]
        carry = self._payload["carry"]
        tag: tuple[object, ...] = () if target is UNSET else (target,)

        def thunk(rt: Runtime) -> object:
            worker = rt.ctx.get(MpWorker, *tag)
            attrs = dict(rt.ctx.attrs) if carry and rt.ctx.attrs else None
            result = worker.execute(body_term, attrs=attrs)
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _one_sync(result)
            return result

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body_term = self._children[0]
        target = self._payload["target"]
        carry = self._payload["carry"]
        tag: tuple[object, ...] = () if target is UNSET else (target,)

        async def athunk(rt: Runtime) -> object:
            worker = rt.ctx.get(MpWorker, *tag)
            attrs = dict(rt.ctx.attrs) if carry and rt.ctx.attrs else None
            result = await worker.aexecute(body_term, attrs=attrs)
            if rt.program.attrs[Attr.CHILD_CARDINALITY][nid] is Cardinality.STREAM:
                return _one_async(result)
            return result

        return athunk
