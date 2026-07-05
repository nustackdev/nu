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
    """``IfDo(cond, then [, else_])`` - run ``then`` if ``cond`` is truthy, else ``else_``.

    Children: ``[cond, then]`` or ``[cond, then, else_]``. Slot 0 is the
    condition parameter; the body slots hold mutating children.
    """

    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def __init__(self, cond: object, then: object, else_: object = None) -> None:
        if else_ is not None:
            super().__init__(cond, then, else_)
        else:
            super().__init__(cond, then)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        cond = children[0]

        def thunk(rt: Runtime) -> None:
            if cond(rt):
                children[1](rt)
            elif len(children) > 2:
                children[2](rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        cond = children[0]

        async def athunk(rt: Runtime) -> None:
            if await cond(rt):
                await children[1](rt)
            elif len(children) > 2:
                await children[2](rt)

        return athunk


class WhileDo(Control):
    """``WhileDo(cond, body)`` - run ``body`` while ``cond`` is truthy.

    Children: ``[cond, body]``. Slot 0 is the condition parameter, re-evaluated
    each turn; slot 1 is the body.
    """

    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        cond, body = children

        def thunk(rt: Runtime) -> None:
            while cond(rt):
                body(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        cond, body = children

        async def athunk(rt: Runtime) -> None:
            while await cond(rt):
                await body(rt)

        return athunk


class ForeverDo(Control):
    """``ForeverDo(body)`` - run ``body`` endlessly. No parameters.

    Children: ``[body]``. Every slot is a body, so ``param_slots`` keeps the
    empty default.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (body,) = children

        def thunk(rt: Runtime) -> None:
            while True:
                body(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (body,) = children

        async def athunk(rt: Runtime) -> None:
            while True:
                await body(rt)

        return athunk


class ForEachDo(Control):
    """``ForEachDo(items, body, item="item")`` - run ``body`` for each element.

    Children: ``[items, body, item_name]``. Binds the current element under the
    name ``item_name`` yields (the attrs side-channel) before each body run, so
    the body reads it via ``AttrRef(<name>)``. Slots 0 (items) and 2 (the name)
    are parameters; slot 1 is the body.
    """

    _param_slots = Declared(value=frozenset({0, 2}), name="param_slots")

    def __init__(self, items: object, body: object, item: object = "item") -> None:
        super().__init__(items, body, item)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        items_t, body, key_t = children

        def thunk(rt: Runtime) -> None:
            name = key_t(rt)
            for elem in sync_iter(items_t(rt)):
                rt.ctx.attrs[name] = elem
                body(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        items_t, body, key_t = children

        async def athunk(rt: Runtime) -> None:
            name = await key_t(rt)
            async for elem in aiter_any(await items_t(rt)):
                rt.ctx.attrs[name] = elem
                await body(rt)

        return athunk


class ForRangeDo(Control):
    """``ForRangeDo(start, stop, body, *, step=1, index="index")`` - counted loop.

    Children: ``[start, stop, step, body, index_name]``. Iterates
    ``range(start, stop, step)``, binding each value under the name
    ``index_name`` yields before each body run. Slots 0, 1, 2 and 4 are
    parameters; slot 3 is the body.
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

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        start_t, stop_t, step_t, body, index_t = children

        def thunk(rt: Runtime) -> None:
            name = index_t(rt)
            for i in range(start_t(rt), stop_t(rt), step_t(rt)):
                rt.ctx.attrs[name] = i
                body(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        start_t, stop_t, step_t, body, index_t = children

        async def athunk(rt: Runtime) -> None:
            name = await index_t(rt)
            for i in range(await start_t(rt), await stop_t(rt), await step_t(rt)):
                rt.ctx.attrs[name] = i
                await body(rt)

        return athunk


class Delay(Control):
    """``Delay(seconds)`` - sleep ``seconds``, then continue; no body.

    A childless delay: slot 0 is the delay parameter, there is no body. Runs
    anywhere - the sync path uses ``time.sleep``, the async path
    ``asyncio.sleep`` - so it picks the right primitive per execution mode.
    For "wait, then run something", use ``DelayedDo`` or ``Delay(s) >> body``.
    """

    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (delay_t,) = children

        def thunk(rt: Runtime) -> None:
            time.sleep(delay_t(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (delay_t,) = children

        async def athunk(rt: Runtime) -> None:
            await asyncio.sleep(await delay_t(rt))

        return athunk


class DelayedDo(Control):
    """``DelayedDo(delay, body)`` - sleep ``delay`` seconds, then run ``body``.

    Children: ``[delay, body]``. Slot 0 is the delay parameter; slot 1 the
    body. Sync path uses ``time.sleep``, async path ``asyncio.sleep``. This is
    sugar for ``Delay(delay) >> body``; for a bare wait, use ``Delay``.
    """

    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        delay_t, body = children

        def thunk(rt: Runtime) -> None:
            time.sleep(delay_t(rt))
            body(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        delay_t, body = children

        async def athunk(rt: Runtime) -> None:
            await asyncio.sleep(await delay_t(rt))
            await body(rt)

        return athunk


class SwitchDo(Control):
    """``SwitchDo(selector, cases, default=None)`` - branch on a selector value.

    Children: ``[selector, *case_bodies, default?]``. Slot 0 is the selector
    parameter; the rest are bodies. The match keys are intrinsic constants of
    the switch, kept in ``payload`` (so they survive ``with_children``), paired
    by position with the case bodies. The first key equal to the selector value
    runs its body; failing any match, the optional default runs.
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

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
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
