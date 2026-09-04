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


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from nu.engine import Term
    from nu.lang.runtime import Runtime

__all__ = [
    "Delay",
    "DelayedDo",
    "ForEachDo",
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
