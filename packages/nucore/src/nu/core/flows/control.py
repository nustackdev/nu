"""Control flows: Command-composing atoms steered by Query parameters.

Nu's Control sub-shape - the Flows that run their bodies under Query
parameters (a condition, an iterable, a count). A Control owns no effects and
yields nothing (VOID): the param slots feed the orchestration, the body slots
carry the writes. ``param_slots`` declares which slot indices are parameters;
the rest are bodies. The ``control_param_is_yielder`` law holds every param to
a yielding child (Ref / Query / Action) and ``flow_body_is_mutator`` holds
every body to a mutating child (Command / Action / Flow).

Loop variables ride the attrs side-channel: ``ForEachDo`` / ``ForRangeDo`` bind
the current element under a name (itself a child, so it can be a Literal or a
computed Ref) before each body run, read back via ``AttrRef`` - the same
designated channel ``Map`` / ``Filter`` use, not a tracked fabric write.
``ForEachParAsync`` is ``ForEachDo``'s fan-out twin: same three args, same
binding, but every element gets its own arm on the loop at once, each on its own
Context branch so the arms cannot stomp each other's loop variable. It lives
here, with the ForEach it mirrors, and borrows the scheduling from ``parallel``.

Each atom emits a thunk via ``compile`` / ``acompile`` and stays immutable -
construction config that must survive ``with_children`` lives in ``payload``
(``SwitchDo``'s match keys), never as mutable per-run state.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from nu.core._stream import aiter_any, sync_iter
from nu.engine.structure import Declared
from nu.lang import Control
from nu.lang.attributes.execution import ExecOrder


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from nu.engine import Term
    from nu.lang.runtime import Runtime

__all__ = [
    "Delay",
    "DelayedDo",
    "ForEachDo",
    "ForEachParAsync",
    "ForRangeDo",
    "ForeverDo",
    "IfDo",
    "SwitchDo",
    "WhileDo",
]


class IfDo(Control):
    """``IfDo(cond, then, else_=None)`` - runs ``then`` or ``else_`` based on ``cond``.

    Args:
        cond: the condition to test.
        then: the body to run when ``cond`` is truthy.
        else_: the body to run when ``cond`` is falsy. Optional: leave it out
            to run nothing on a falsy ``cond``.

    Notes:
        - ``cond`` is evaluated exactly once per run, unlike ``WhileDo`` which
          re-checks it every turn.
        - A falsy ``cond`` with no ``else_`` runs nothing at all.

    Example:
        >>> _, ctx = nu.run(
        ...     nu.IfDo(
        ...         nu.Literal(True),
        ...         nu.SetCmd(nu.AttrRef("a"), nu.Literal(1)),
        ...         nu.SetCmd(nu.AttrRef("a"), nu.Literal(2)),
        ...     )
        ... )
        >>> ctx.attrs["a"]
        1
    """

    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def __init__(self, cond: object, then: object, else_: object = None) -> None:
        if else_ is not None:
            super().__init__(cond, then, else_)
        else:
            super().__init__(cond, then)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        cond = children[0]

        def thunk(rt: Runtime) -> None:
            if cond(rt):
                children[1](rt)
            elif len(children) > 2:
                children[2](rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        cond = children[0]

        async def athunk(rt: Runtime) -> None:
            if await cond(rt):
                await children[1](rt)
            elif len(children) > 2:
                await children[2](rt)

        return athunk


class WhileDo(Control):
    """``WhileDo(cond, body)`` - runs ``body`` on loop while ``cond`` stays truthy.

    Args:
        cond: the condition, checked before each turn.
        body: the loop body.

    Notes:
        - ``cond`` is re-evaluated before every turn, including the first, so
          a falsy ``cond`` at the start runs ``body`` zero times.
        - No built-in turn cap: a ``cond`` that never turns falsy loops
          forever.

    Example:
        >>> ctx = nu.Context()
        >>> ctx.attrs["i"] = 0
        >>> _, ctx = nu.run(
        ...     nu.WhileDo(
        ...         nu.Lt(nu.AttrRef("i"), nu.Literal(3)),
        ...         nu.SetCmd(nu.AttrRef("i"), nu.Add(nu.AttrRef("i"), nu.Literal(1))),
        ...     ),
        ...     ctx,
        ... )
        >>> ctx.attrs["i"]
        3
    """

    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        cond, body = children

        def thunk(rt: Runtime) -> None:
            while cond(rt):
                body(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        cond, body = children

        async def athunk(rt: Runtime) -> None:
            while await cond(rt):
                await body(rt)

        return athunk


class ForeverDo(Control):
    """``ForeverDo(body)`` - runs ``body`` on loop forever.

    Args:
        body: the loop body, re-run with no condition to stop it.

    Notes:
        - No parameter slot at all: the only child is a body, so
          ``param_slots`` keeps the empty default.
        - Used for standing ticks (a reactive loop, a periodic
          ``Delay`` + action) that end only when the surrounding process is
          stopped or errors, not from anything inside the atom itself.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (body,) = children

        def thunk(rt: Runtime) -> None:
            while True:
                body(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (body,) = children

        async def athunk(rt: Runtime) -> None:
            while True:
                await body(rt)

        return athunk


class ForEachDo(Control):
    """``ForEachDo(items, body, item="item")`` - runs ``body`` once per element of ``items``.

    Args:
        items: the iterable to walk.
        body: the loop body, run once per element.
        item: the name to bind the current element under. Optional, defaults
            to ``"item"``.

    Notes:
        - The current element is bound into ``rt.ctx.attrs`` under ``item``
          before each body run, the same attrs side-channel ``Map`` /
          ``Filter`` use, not a tracked fabric write. ``body`` reads it back
          via ``AttrRef(item)``.
        - ``item`` is itself evaluated once, before the loop starts, so it can
          be a computed Ref and not just a literal name.
        - Rebinding overwrites whatever ``item`` held before, in ``attrs``.

    Example:
        >>> ctx = nu.Context()
        >>> ctx.attrs["sum"] = 0
        >>> _, ctx = nu.run(
        ...     nu.ForEachDo(
        ...         nu.Iter(nu.Literal([1, 2, 3])),
        ...         nu.SetCmd(nu.AttrRef("sum"), nu.Add(nu.AttrRef("sum"), nu.AttrRef("item"))),
        ...     ),
        ...     ctx,
        ... )
        >>> ctx.attrs["sum"]
        6
    """

    _param_slots = Declared(value=frozenset({0, 2}), name="param_slots")

    def __init__(self, items: object, body: object, item: object = "item") -> None:
        super().__init__(items, body, item)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        items_t, body, key_t = children

        def thunk(rt: Runtime) -> None:
            name = key_t(rt)
            for elem in sync_iter(items_t(rt)):
                rt.ctx.attrs[name] = elem
                body(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        items_t, body, key_t = children

        async def athunk(rt: Runtime) -> None:
            name = await key_t(rt)
            async for elem in aiter_any(await items_t(rt)):
                rt.ctx.attrs[name] = elem
                await body(rt)

        return athunk


class ForEachParAsync(Control):
    """``ForEachParAsync(items, body, item="item")`` - runs ``body`` once per element of ``items``, every arm on the loop at once.

    Args:
        items: the iterable to fan out over, evaluated once before any arm
            starts.
        body: the arm, run once per element, concurrently with the others.
        item: the name to bind that arm's element under. Optional, defaults
            to ``"item"``.

    Notes:
        - Same three args and the same ``item`` binding as ``ForEachDo``,
          which is why it sits here rather than in ``parallel/``; the
          scheduling itself is ``parallel._scheduling.aeval_foreach_par``.
        - Joins on all, like ``Parallel``, but over a runtime-sized list:
          ``Parallel`` / ``Gather`` fan out to children fixed at
          construction, this one to whatever ``items`` yields at run time.
        - Async-only, and named for it the way ``ParallelAsync`` is: every
          arm is an asyncio.Task on the loop, no threaded placement and no
          sync path at all. Sync ``run`` refuses the subtree up front via
          ``requires_async``.
        - It does not take from the concurrency budget. A parked coroutine
          costs no worker, and these arms are meant never to return, so there
          is nothing to ration - ``max_parallel`` bounds threads, and this
          atom uses none.
        - Each arm runs against its own Context branch, so ``item`` is that
          arm's element and nothing else. The branch shares attr values by
          reference (``Attributes.copy_shallow``), so a live handle in attrs
          crosses fine, but an arm's own writes stay in its arm.
        - Arms that never return are the point: a standing ``ForeverDo`` per
          element joins only when the surrounding Flow is cancelled. An empty
          ``items`` completes immediately.
        - Cancellation propagates: under ``Race``, cancelling this Flow
          cancels every arm. First error wins like ``Parallel``, and the
          remaining arms are cancelled on the way out, since a headless
          never-returning arm would outlive the Flow that spawned it.

    Example:
        >>> import asyncio
        >>> _, ctx = asyncio.run(
        ...     nu.arun(
        ...         nu.ForEachParAsync(
        ...             nu.Iter(nu.Literal([1, 2, 3])),
        ...             nu.SetCmd(nu.AttrRef("seen"), nu.AttrRef("item")),
        ...         )
        ...     )
        ... )
        >>> "seen" in ctx.attrs
        False
    """

    _param_slots = Declared(value=frozenset({0, 2}), name="param_slots")
    _exec_order = Declared(value=ExecOrder.PARALLEL, name="exec_order")
    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, items: object, body: object, item: object = "item") -> None:
        super().__init__(items, body, item)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "ForEachParAsync requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        from .parallel import _scheduling

        items_t, _body, key_t = children

        async def athunk(rt: Runtime) -> None:
            name = await key_t(rt)
            elems = [elem async for elem in aiter_any(await items_t(rt))]
            body_nid = rt.program.children[nid][1]
            await _scheduling.aeval_foreach_par(rt, body_nid, elems, name)

        return athunk


class ForRangeDo(Control):
    """``ForRangeDo(start, stop, body, *, step=1, index="index")`` - runs ``body`` once per value of ``range(start, stop, step)``.

    Args:
        start: the range's start.
        stop: the range's exclusive end.
        body: the loop body, run once per value.
        index: the name to bind the current value under. Optional, defaults
            to ``"index"``.
        step: the range's step. Optional, defaults to 1.

    Notes:
        - ``start``, ``stop``, ``step`` and ``index`` are each evaluated once,
          before the loop starts.
        - The current value is bound into ``rt.ctx.attrs`` under ``index``
          before each body run, read back via ``AttrRef(index)``. Same
          side-channel ``ForEachDo`` uses.
        - Follows Python's ``range`` rules: a ``step`` that never reaches
          ``stop`` from ``start`` runs the body zero times rather than
          looping forever.

    Example:
        >>> ctx = nu.Context()
        >>> ctx.attrs["sum"] = 0
        >>> _, ctx = nu.run(
        ...     nu.ForRangeDo(
        ...         0, 4, nu.SetCmd(nu.AttrRef("sum"), nu.Add(nu.AttrRef("sum"), nu.AttrRef("index")))
        ...     ),
        ...     ctx,
        ... )
        >>> ctx.attrs["sum"]
        6
    """

    _param_slots = Declared(value=frozenset({0, 1, 2, 4}), name="param_slots")

    def __init__(
        self,
        start: object,
        stop: object,
        body: object,
        *,
        step: object = 1,
        index: object = "index",
    ) -> None:
        super().__init__(start, stop, step, body, index)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        start_t, stop_t, step_t, body, index_t = children

        def thunk(rt: Runtime) -> None:
            name = index_t(rt)
            for i in range(start_t(rt), stop_t(rt), step_t(rt)):
                rt.ctx.attrs[name] = i
                body(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        start_t, stop_t, step_t, body, index_t = children

        async def athunk(rt: Runtime) -> None:
            name = await index_t(rt)
            for i in range(await start_t(rt), await stop_t(rt), await step_t(rt)):
                rt.ctx.attrs[name] = i
                await body(rt)

        return athunk


class Delay(Control):
    """``Delay(seconds)`` - sleeps ``seconds``, then continues. No body.

    Args:
        seconds: how long to sleep.

    Notes:
        - Sync execution blocks on ``time.sleep``; async execution suspends
          on ``asyncio.sleep``, so it never blocks an event loop.
        - No body: for "wait, then run something" use ``DelayedDo``, or
          chain ``Delay(seconds) >> body``.

    Example:
        >>> nu.run(nu.Delay(nu.Literal(0.0)))[0] is None
        True
    """

    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (delay_t,) = children

        def thunk(rt: Runtime) -> None:
            time.sleep(delay_t(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (delay_t,) = children

        async def athunk(rt: Runtime) -> None:
            await asyncio.sleep(await delay_t(rt))

        return athunk


class DelayedDo(Control):
    """``DelayedDo(delay, body)`` - sleeps ``delay`` seconds, then runs ``body``.

    Args:
        delay: how long to sleep before ``body`` runs.
        body: the body to run once the sleep is over.

    Notes:
        - Sugar for ``Delay(delay) >> body``; for a bare wait with no body,
          use ``Delay`` on its own.
        - Sync execution blocks on ``time.sleep``; async execution suspends
          on ``asyncio.sleep``.

    Example:
        >>> _, ctx = nu.run(nu.DelayedDo(nu.Literal(0.0), nu.SetCmd(nu.AttrRef("a"), nu.Literal(1))))
        >>> ctx.attrs["a"]
        1
    """

    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        delay_t, body = children

        def thunk(rt: Runtime) -> None:
            time.sleep(delay_t(rt))
            body(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        delay_t, body = children

        async def athunk(rt: Runtime) -> None:
            await asyncio.sleep(await delay_t(rt))
            await body(rt)

        return athunk


class SwitchDo(Control):
    """``SwitchDo(selector, cases, default=None)`` - runs the case body keyed by ``selector``'s value.

    Args:
        selector: the value to match against the case keys.
        cases: a mapping from match key to case body, checked in order.
        default: the body to run when no key matches. Optional: leave it out
            to run nothing on a miss.

    Notes:
        - The case keys are intrinsic constants of the switch, not children:
          they live in ``payload`` so they survive ``with_children``, and are
          paired by position with the case bodies.
        - Keys are checked in the order ``cases`` was given, first equal match
          wins; a later duplicate key is unreachable.
        - ``selector`` is evaluated once per run, before any key comparison.

    Example:
        >>> _, ctx = nu.run(
        ...     nu.SwitchDo(
        ...         nu.Literal("b"),
        ...         {
        ...             "a": nu.SetCmd(nu.AttrRef("x"), nu.Literal(1)),
        ...             "b": nu.SetCmd(nu.AttrRef("x"), nu.Literal(2)),
        ...         },
        ...     )
        ... )
        >>> ctx.attrs["x"]
        2
    """

    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def __init__(
        self,
        selector: object,
        cases: Mapping[object, Term],
        default: object = None,
    ) -> None:
        bodies = list(cases.values())
        if default is not None:
            bodies.append(default)
        super().__init__(selector, *bodies)
        self._payload["keys"] = tuple(cases.keys())
        self._payload["has_default"] = default is not None

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        selector = children[0]
        bodies = children[1:]
        keys = self._payload["keys"]
        has_default = self._payload["has_default"]

        def thunk(rt: Runtime) -> None:
            value = selector(rt)
            for i, key in enumerate(keys):
                if key == value:
                    bodies[i](rt)
                    return
            if has_default:
                bodies[-1](rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        selector = children[0]
        bodies = children[1:]
        keys = self._payload["keys"]
        has_default = self._payload["has_default"]

        async def athunk(rt: Runtime) -> None:
            value = await selector(rt)
            for i, key in enumerate(keys):
                if key == value:
                    await bodies[i](rt)
                    return
            if has_default:
                await bodies[-1](rt)

        return athunk
