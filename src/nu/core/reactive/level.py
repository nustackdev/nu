"""Level flows: ReconcileReactive, WaitReactive, ForEachParReactive.

A level flow does not hand its body the change. The body reads the current
state and makes it right: start what should run, stop what should not, write
what is missing, or answer whether a condition holds yet. Run twice with
nothing changed in between, the second run finds nothing to do. That is the
whole contract, and it is what makes these flows robust: since a pass ignores
why it runs, the flow can run it on wakes no subscription delivered, and a
missed notification costs a delay instead of a wrong state.

Change delivery is at most once. A fresh subscription can miss writes for a
short while (writers learn about it with a delay), and a backend may drop a
message. So a level flow wakes:

- once right after its subscription is bound, so the first read follows the
  subscribe and a write made before it is always seen;
- on every notification;
- on re-checks measured from binding: one at each ``after`` offset (default
  0.1, 0.3 and 1.0 seconds, the window a fresh subscription is blind in),
  then every ``every`` seconds forever (default 30; ``None`` turns the
  standing re-check off). A missed notification is caught by the next one.

Wakes merge: whatever lands while a pass runs, one notification or a hundred,
is one more pass, which reads the state as it then is. The subscription is
held for the flow's whole life and never reopened.

Which kind to reach for: a body that reacts to what happened (a click, a
message, the key that was written) is an event body and belongs in the
``React`` family, which hands it the real key and never invents a wake. A body
that keeps something in step with state, or waits for state to reach a point,
is a level body and belongs here.

Async-only, like the whole reactive set: the sync ``_compile`` path raises.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.core._stream import aiter_any
from nu.core.flows.parallel._scheduling import _settle, _spawn_arm
from nu.engine.structure import Declared
from nu.lang import Control
from nu.lang.attributes.execution import ExecOrder

from ._wakes import DEFAULT_AFTER, DEFAULT_EVERY, Wakes, check_schedule
from .event import _adrain_body


if TYPE_CHECKING:
    import asyncio
    from collections.abc import Callable, Iterable

    from nu.lang.runtime import Runtime

__all__ = ["ForEachParReactive", "ReconcileReactive", "WaitReactive"]


def _async_only(owner: str) -> Callable:
    """The sync thunk of a level flow: refuses to run."""

    def thunk(rt: Runtime) -> None:
        msg = f"{owner} requires an async runtime; use arun"
        raise RuntimeError(msg)

    return thunk


class ReconcileReactive(Control):
    """Keep state right: run the body after subscribing, on every change, and on re-checks.

    Binds the subscription once and runs the body right after, then again
    whenever a change lands or a re-check falls due, one pass at a time.
    Never returns on its own; the caller ends it by cancelling.

    Args:
        change: the change subscription that says the state may have moved.
        body: the pass. It gets no changed key: it reads the state it keeps
            in step and makes it right, and does nothing when nothing is
            off. A tree, or a lambda taking no arguments.
        after: re-check offsets in seconds after binding, for the window a
            fresh subscription may not yet be heard in.
        every: seconds between standing re-checks once ``after`` is spent.
            ``None`` turns them off.

    Notes:
        - Changes landing while a pass runs merge into one more pass.
        - A body that writes into what ``change`` watches wakes the flow
          again. A level body settles: the next pass finds nothing to do.
        - An error raised by the body ends the flow and propagates. The
          subscription is unbound and closed on any exit.

    Yields:
        Nothing.

    Example:
        Keep an order's total in step with its quantity. Needs a real
        substrate behind the subscription, so it cannot run standalone::

            ReconcileReactive(Order.qty.on_change(), Order.total.set(Order.qty * Order.price))
    """

    _mutates = Declared(value=frozenset(), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")
    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def __init__(
        self,
        change: object,
        body: object,
        *,
        after: Iterable[float] = DEFAULT_AFTER,
        every: float | None = DEFAULT_EVERY,
    ) -> None:
        body, () = bind("ReconcileReactive", body)
        super().__init__(change, body)
        self._payload["after"], self._payload["every"] = check_schedule(
            "ReconcileReactive", after, every
        )

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return _async_only("ReconcileReactive")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        change, body = children
        after, every = self._payload["after"], self._payload["every"]

        async def athunk(rt: Runtime) -> None:
            async with Wakes(await change(rt), after, every) as wakes:
                while True:
                    await wakes.wait()
                    await _adrain_body(rt, body)

        return athunk


class WaitReactive(Control):
    """Wait until a condition holds, read after subscribing, on every change, and on re-checks.

    Binds the subscription once and evaluates ``cond`` right after, then
    again whenever a change lands or a re-check falls due. Returns on the
    first truthy read, so a condition that already holds returns at once.

    Args:
        change: the change subscription that says ``cond`` may have moved.
        cond: what to wait for. It gets no changed key: it reads the state
            and answers. A tree, or a lambda taking no arguments. EMPTY
            counts as false.
        after: re-check offsets in seconds after binding, for the window a
            fresh subscription may not yet be heard in.
        every: seconds between standing re-checks once ``after`` is spent.
            ``None`` turns them off, leaving a dropped notification to wait
            for the next change.

    Notes:
        - The first read follows the subscribe, so a write made before the
          wait began is always seen. One whose notification goes missing is
          seen on the next re-check.
        - Changes landing while ``cond`` is read merge into one more read.
        - The subscription is unbound and closed on any exit.

    Yields:
        Nothing.

    Example:
        Block until a job is marked done. Needs a real substrate behind the
        subscription, so it cannot run standalone::

            WaitReactive(Job.status.on_change(), Job.status == "done")
    """

    _mutates = Declared(value=frozenset(), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")
    _param_slots = Declared(value=frozenset({0, 1}), name="param_slots")

    def __init__(
        self,
        change: object,
        cond: object,
        *,
        after: Iterable[float] = DEFAULT_AFTER,
        every: float | None = DEFAULT_EVERY,
    ) -> None:
        cond, () = bind("WaitReactive", cond)
        super().__init__(change, cond)
        self._payload["after"], self._payload["every"] = check_schedule(
            "WaitReactive", after, every
        )

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return _async_only("WaitReactive")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        change, cond = children
        after, every = self._payload["after"], self._payload["every"]

        async def athunk(rt: Runtime) -> None:
            async with Wakes(await change(rt), after, every) as wakes:
                while True:
                    await wakes.wait()
                    if await cond(rt):
                        return

        return athunk


class ForEachParReactive(Control):
    """``ForEachParReactive(items, change, lambda x: body)`` - one arm per element, kept live against ``change``.

    The level flow over a fan-out: each pass reads ``items`` and makes the
    arm set match it. Passes run right after subscribing, on every change,
    and on re-checks, with changes during a pass merged into one more.

    Args:
        items: the elements to fan out over, read again on every pass.
            Elements must be hashable: the arm book is kept by element, and
            that is what makes a difference computable.
        change: the change subscription that says the element set may have
            moved. Bound once, before the first pass, and held for as long as
            this runs.
        body: the arm, run once per element, concurrently with the others. A
            lambda over the element, or a tree reading it with ``Attr(item)``.
        item: the name to bind that arm's element under, for a tree body.
            Optional, defaults to ``"item"``; a lambda mints its own.
        after: re-check offsets in seconds after binding, for the window a
            fresh subscription may not yet be heard in.
        every: seconds between standing re-checks once ``after`` is spent.
            ``None`` turns them off.

    Notes:
        - ``ForEachParAsync`` held open: the fan-out and the arms are the
          same, but the element list is read on every pass instead of once.
          What comes out of the comparison is births and deaths, and nothing
          else: an element with no arm gets one started, an arm whose element
          is gone is cancelled, and every other arm keeps running untouched.
          That is the whole reason to reach for this over a fan-out rebuilt
          from scratch, which restarts the innocent along with the guilty.
        - A death is a cancellation, delivered by this atom. An arm does not
          have to notice its own element leaving; it is cancelled where it
          stands, and drained before the pass that killed it returns.
        - So a delete and a re-add of the same element are a death and then a
          birth, in that order, never an overlap - but only when the two are
          seen by two different passes. A pass reconciles against the current
          answer to ``items``, it does not replay changes, so a delete and a
          re-add that both land between two passes leave the arm running and
          unaware.
        - Arms are isolated. One that raises ends alone: the error is not
          re-raised here and the siblings are not cancelled, which is the
          opposite of ``ForEachParAsync``'s first-error-wins and is what
          supervision means. Its element gets a fresh arm on the next pass,
          so a body wanting its failures reported has to report them itself.
        - Never returns on its own, even with an empty ``items``: the
          surrounding Flow ends it by cancelling. Every live arm is cancelled
          and drained on the way out.
        - A ``body`` that writes into what ``change`` watches wakes this atom
          again, and the pass that follows finds the arm set already right.

    Example:
        Following a live collection needs a real substrate behind the
        subscription, so it cannot run standalone here::

            ForEachParReactive(users.keys(), users.on_children_change(), lambda user: body)
    """

    _param_slots = Declared(value=frozenset({0, 1, 3}), name="param_slots")
    _exec_order = Declared(value=ExecOrder.PARALLEL, name="exec_order")
    _requires_async = Declared(value=True, name="requires_async")

    def __init__(
        self,
        items: object,
        change: object,
        body: object,
        item: object = None,
        *,
        after: Iterable[float] = DEFAULT_AFTER,
        every: float | None = DEFAULT_EVERY,
    ) -> None:
        body, (item,) = bind("ForEachParReactive", body, item=item)
        super().__init__(items, change, body, "item" if item is None else item)
        self._payload["after"], self._payload["every"] = check_schedule(
            "ForEachParReactive", after, every
        )

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return _async_only("ForEachParReactive")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        items, change, _body, item = children
        after, every = self._payload["after"], self._payload["every"]

        async def athunk(rt: Runtime) -> None:
            name = await item(rt)
            body_nid = rt.program.children[nid][2]
            arms: dict[object, asyncio.Task] = {}
            try:
                async with Wakes(await change(rt), after, every) as wakes:
                    while True:
                        await wakes.wait()
                        elems = [elem async for elem in aiter_any(await items(rt))]
                        await _reconcile_arms(rt, body_nid, name, arms, elems)
            finally:
                await _settle(list(arms.values()))

        return athunk


def _forget_arm(arms: dict, key: object, task: asyncio.Task) -> None:
    """Drop a finished arm from the live set and take its outcome off it.

    Both halves matter. An arm left in the dict holds its Task alive and holds
    its key's slot against a later birth, and an arm that raised would warn at
    collection time if nobody ever read the exception. Reading it is also where
    the isolation happens: one arm's failure ends that arm and goes no further.
    """
    if arms.get(key) is task:
        del arms[key]
    if not task.cancelled():
        task.exception()


async def _reconcile_arms(
    rt: Runtime,
    nid: int,
    name: str,
    arms: dict,
    elems: Iterable,
) -> None:
    """Make ``arms`` hold exactly one live arm of ``nid`` per element of ``elems``.

    An element with no arm gets one; an arm whose element is gone is cancelled
    and awaited here rather than left to unwind on its own time, so the key is
    genuinely free by the time this returns and a later birth can never overlap
    the death it followed. Every other arm is untouched, which is the point.

    Arms that already ended are swept first rather than waited on: a done
    callback lands a tick late, and a key whose arm is over should be free to
    be born again on this pass, not the one after it.
    """
    for key, task in [(k, t) for k, t in arms.items() if t.done()]:
        _forget_arm(arms, key, task)
    wanted = list(dict.fromkeys(elems))
    live = set(wanted)
    for key in [k for k in arms if k not in live]:
        await _settle([arms.pop(key)])
    for key in wanted:
        if key in arms:
            continue
        task = _spawn_arm(rt, nid, key, name)
        arms[key] = task
        task.add_done_callback(lambda t, k=key: _forget_arm(arms, k, t))
