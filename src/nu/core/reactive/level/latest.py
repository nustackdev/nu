"""ReconcileLatest: one arm for the one id read from state, restarted when it changes."""

from __future__ import annotations

from contextlib import aclosing
from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.core._stream import aiter_any
from nu.engine.structure import Declared
from nu.lang import Control
from nu.lang.attributes.execution import ExecOrder
from nu.lang.null import is_null

from .._body import async_only
from ._wakes import DEFAULT_AFTER, DEFAULT_EVERY, schedule_terms
from .latest_each import hold_arms


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from nu.lang.runtime import Runtime

__all__ = ["ReconcileLatest"]


async def _one(owner: str, stream: object) -> object:
    """The one element a stream read yields, or ``None`` when it yields nothing.

    Raises:
        ValueError: the stream yields more than one element.
    """
    found: list = []
    async with aclosing(aiter_any(stream)) as elems:
        async for elem in elems:
            found.append(elem)
            if len(found) > 1:
                msg = f"{owner}: read must yield one id or nothing, got more than one"
                raise ValueError(msg)
    return found[0] if found else None


class ReconcileLatest(Control):
    """``ReconcileLatest(read, change, lambda x: body)`` - one arm for the id ``read`` answers, kept live against ``change``.

    ``ReconcileLatestEach`` over one id or none. Each pass reads the id and
    makes the arm match it: a new id is a death and a birth, the same id
    leaves the arm running, no id leaves no arm. Passes run right after
    subscribing, on every change, and on re-checks, with changes during a
    pass merged into one more.

    Args:
        read: the id to hold an arm for, read again on every pass. ``None``
            and the absent sentinel mean no id. Must be hashable otherwise.
            A scalar query answers the id itself; a stream query yields it,
            or yields nothing for no id, and one that yields more than one
            element is refused. A tuple answered by a scalar query is one
            id, never taken apart.
        change: the change subscription that says the id may have moved.
            Bound once, before the first pass, and held for as long as this
            runs.
        body: the arm, run for the id. A lambda over the id, or a tree
            reading it with ``Attr(item)``.
        item: the name to bind the id under, for a tree body. Optional,
            defaults to ``"item"``; a lambda mints its own.
        after: re-check offsets in seconds after binding, for the window a
            fresh subscription may not yet be heard in. A term yielding an
            iterable of floats, or a literal one.
        every: seconds between standing re-checks once ``after`` is spent.
            ``None`` turns them off. A term yielding a float or None, or a
            literal one.

    Notes:
        - The id is what is compared, never the value behind it. To restart
          the arm when a row changes, put the version in the id.
        - An arm runs once per appearance of its id. One that finishes on
          its own stays finished while the id stays; once the read answers
          another id or none and the id comes back, it is born again.
        - An arm error ends the flow: the subscription is unbound and closed
          and the error propagates. Isolate with ``TryCatch``, supervise
          with ``Retry``. A stream ``read`` that yields two or more
          elements ends it the same way, with ``ValueError``.
        - Never returns on its own, even while there is no id: the
          surrounding Flow ends it by cancelling. A live arm is cancelled
          and drained on the way out.
        - A literal schedule that cannot run is refused at build time; a
          computed one is refused when it is read, with the same message.

    Yields:
        Nothing.

    Example:
        A view that follows a selection needs a real substrate behind the
        subscription, so it cannot run standalone here::

            ReconcileLatest(Cell.selected, Cell.selected.on_change(), lambda row: show(row))
    """

    _param_slots = Declared(value=frozenset({0, 1, 3, 4, 5}), name="param_slots")
    _exec_order = Declared(value=ExecOrder.PARALLEL, name="exec_order")
    _requires_async = Declared(value=True, name="requires_async")

    def __init__(
        self,
        read: object,
        change: object,
        body: object,
        item: object = None,
        *,
        after: Iterable[float] | object = DEFAULT_AFTER,
        every: float | object | None = DEFAULT_EVERY,
    ) -> None:
        body, (item,) = bind("ReconcileLatest", body, item=item)
        super().__init__(
            read,
            change,
            body,
            "item" if item is None else item,
            *schedule_terms("ReconcileLatest", after, every),
        )

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReconcileLatest")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        read = children[0]

        async def ids(rt: Runtime) -> list:
            value = await read(rt)
            # A stream query's thunk hands back an async iterable; a scalar
            # one hands back the id itself, which may be a tuple. Only the
            # former is walked, so a tuple id is never taken apart.
            if hasattr(value.__class__, "__aiter__"):
                value = await _one("ReconcileLatest", value)
            return [] if value is None or is_null(value) else [value]

        async def athunk(rt: Runtime) -> None:
            await hold_arms("ReconcileLatest", rt, nid, children, ids)

        return athunk
