"""Control flows: Command-composing atoms steered by Query parameters.

Nu's Control sub-shape - the Flows that run their bodies under Query
parameters (a condition, an iterable, a count). A Control owns no effects and
yields nothing (VOID): the param slots feed the orchestration, the body slots
carry the writes. ``param_slots`` declares which slot indices are parameters;
the rest are bodies. The ``control_param_is_yielder`` law holds every param to
a yielding child (Ref / Query / Action) and ``flow_body_is_mutator`` holds
every body to a mutating child (Command / Action / Flow).

Loop variables are dynamic bindings (``nu.lang.binding``): the body is a
lambda over the element, called once at construction with a mem ref, and the
loop pushes a frame holding the element for each body run - the same binding
``Map`` / ``Filter`` use, not a tracked fabric write. A body given as a plain tree reads no element.
``ForEachParAsync`` is ``ForEachDo``'s fan-out twin: same two args, same
binding, but every element gets its own arm on the loop at once, each arm
pushing a frame of its own so the arms never see each other's element. It
lives here, with the ForEach it mirrors, and borrows the scheduling from
``parallel``.
Its reactive twin, ``ReconcileLatestEach``, keeps the fan-out open against a
change subscription and lives with the other reactive flows in
``nu.core.reactive``.

Each atom emits a thunk via ``compile`` / ``acompile`` and stays immutable.
Fields hold only what is known before the program runs (``SwitchDo``'s case
count); everything a run reads, its match keys included, is a child.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from nu.core._cases import case_labels, checked_labels
from nu.engine.structure import Declared
from nu.lang import Control
from nu.lang._stream import aiter_any, sync_iter
from nu.lang.attributes.execution import ExecOrder
from nu.lang.binding import Binding


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
    "Park",
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
        >>> _ = nu.run(nu.IfDo(nu.Literal(True), nu.print("yes"), nu.print("no")))
        yes
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
        >>> count = lambda i: nu.WhileDo(i < 3, i.set(i + 1)) >> nu.print(i)
        >>> _ = nu.run(nu.let(count, i=0))
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
    """``ForEachDo(items, lambda x: body)`` - runs ``body`` once per element of ``items``.

    Args:
        items: the iterable to walk.
        body: the loop body, run once per element: a lambda over the
            element, or a tree that reads none.

    Notes:
        - The lambda runs once, at construction, and gets a mem ref, not a
          value: it builds the body and never branches on the element in
          Python.
        - The ref's Shape belongs to the lambda's code, so nested lambdas
          each get their own and an inner body still reads the outer
          element. One lambda used again inside its own body shares its
          Shape, and the inner loop shadows the outer, as with ``nu.let``.
        - Each body run gets a frame of its own holding its element, so
          work it detaches (a delayed or spawned task) reads that element.
          The frames never reach the caller.

    Example:
        >>> _ = nu.run(nu.ForEachDo(nu.Iter([1, 2]), lambda x: nu.print(x)))
        1
        2

        Nested, each body reading its own element:

        >>> rows = nu.Iter([["a", "b"]])
        >>> _ = nu.run(nu.ForEachDo(rows, lambda row: nu.ForEachDo(row, lambda c: nu.print(c))))
        a
        b
    """

    _param_slots = Declared(value=frozenset({0}), name="param_slots")

    def __init__(self, items: object, body: object) -> None:
        body, self._binding = Binding.of_lambda("ForEachDo", body, 1)
        super().__init__(items, body)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        items_t, body = children
        binding = self._binding

        def thunk(rt: Runtime) -> None:
            for elem in sync_iter(items_t(rt)):
                body(rt.on(binding.push(rt.ctx, elem)))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        items_t, body = children
        binding = self._binding

        async def athunk(rt: Runtime) -> None:
            async for elem in aiter_any(await items_t(rt)):
                await body(rt.on(binding.push(rt.ctx, elem)))

        return athunk


class ForEachParAsync(Control):
    """``ForEachParAsync(items, lambda x: body)`` - runs ``body`` once per element of ``items``, every arm on the loop at once.

    Args:
        items: the iterable to fan out over, evaluated once before any arm
            starts.
        body: the arm, run once per element, concurrently with the others: a
            lambda over the element, or a tree that reads none.

    Notes:
        - Same two args, the same lambda form and the same binding as
          ``ForEachDo``, which is why it sits here rather than in ``parallel/``; the
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
        - Each arm pushes a frame of its own on the loop's frames, so its
          element is that arm's and nothing else. What is bound above the
          loop is shared by every arm, by reference, so a live handle
          crosses fine, but a frame an arm pushes stays in its arm.
        - Arms that never return are the point: a standing ``ForeverDo`` per
          element joins only when the surrounding Flow is cancelled. An empty
          ``items`` completes immediately.
        - Cancellation propagates: under ``Race``, cancelling this Flow
          cancels every arm. First error wins like ``Parallel``, and the
          remaining arms are cancelled on the way out, since a headless
          never-returning arm would outlive the Flow that spawned it.

    Example:
        >>> import asyncio
        >>> arms = nu.ForEachParAsync(nu.Iter([7]), lambda x: nu.print(x))
        >>> _ = asyncio.run(nu.arun(arms))
        7
    """

    _param_slots = Declared(value=frozenset({0}), name="param_slots")
    _exec_order = Declared(value=ExecOrder.PARALLEL, name="exec_order")
    _requires_async = Declared(value=True, name="requires_async")

    def __init__(self, items: object, body: object) -> None:
        body, self._binding = Binding.of_lambda("ForEachParAsync", body, 1)
        super().__init__(items, body)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "ForEachParAsync requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        from .parallel import _scheduling

        items_t = children[0]
        binding = self._binding

        async def athunk(rt: Runtime) -> None:
            elems = [elem async for elem in aiter_any(await items_t(rt))]
            body_nid = rt.program.children[nid][1]
            arms = [rt.on(binding.push(rt.ctx, elem)) for elem in elems]
            await _scheduling.aeval_foreach_par(arms, body_nid)

        return athunk


class ForRangeDo(Control):
    """``ForRangeDo(start, stop, lambda i: body, *, step=1)`` - runs ``body`` once per value of ``range(start, stop, step)``.

    Args:
        start: the range's start.
        stop: the range's exclusive end.
        body: the loop body, run once per value: a lambda over the value, or
            a tree that reads none.
        step: the range's step. Optional, defaults to 1.

    Notes:
        - ``start``, ``stop`` and ``step`` are each evaluated once, before
          the loop starts.
        - Each body run gets a frame of its own holding its value. Same
          binding, and the same lambda form, as ``ForEachDo``.
        - Follows Python's ``range`` rules: a ``step`` that never reaches
          ``stop`` from ``start`` runs the body zero times rather than
          looping forever.

    Example:
        >>> _ = nu.run(nu.ForRangeDo(0, 2, lambda i: nu.print(i)))
        0
        1
    """

    _param_slots = Declared(value=frozenset({0, 1, 2}), name="param_slots")

    def __init__(self, start: object, stop: object, body: object, *, step: object = 1) -> None:
        body, self._binding = Binding.of_lambda("ForRangeDo", body, 1)
        super().__init__(start, stop, step, body)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        start_t, stop_t, step_t, body = children
        binding = self._binding

        def thunk(rt: Runtime) -> None:
            for i in range(start_t(rt), stop_t(rt), step_t(rt)):
                body(rt.on(binding.push(rt.ctx, i)))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        start_t, stop_t, step_t, body = children
        binding = self._binding

        async def athunk(rt: Runtime) -> None:
            for i in range(await start_t(rt), await stop_t(rt), await step_t(rt)):
                await body(rt.on(binding.push(rt.ctx, i)))

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
        >>> _ = nu.run(nu.DelayedDo(nu.Literal(0.0), nu.print("done")))
        done
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
        - Children: ``[selector, labels, *bodies, default?]``. ``labels`` is
          one param child yielding the case keys in order, so a key can be a
          computed term (a ref, a kv read), evaluated on every run after the
          selector. The case count is a field: it splits the children into
          bodies and the default before the program runs.
        - Keys are checked in the order ``cases`` was given, first equal match
          wins; a later duplicate key is unreachable.
        - ``selector`` is evaluated once per run, before any key comparison.

    Example:
        >>> _ = nu.run(nu.SwitchDo(nu.Literal("b"), {"a": nu.print(1), "b": nu.print(2)}))
        2
    """

    _param_slots = Declared(value=frozenset({0, 1}), name="param_slots")

    def __init__(
        self,
        selector: object,
        cases: Mapping[object, Term],
        default: object = None,
    ) -> None:
        bodies = list(cases.values())
        if default is not None:
            bodies.append(default)
        super().__init__(selector, case_labels(cases), *bodies)
        self.n_cases = len(cases)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        selector, labels_t = children[0], children[1]
        bodies = children[2:]
        n_cases = self.n_cases
        has_default = len(bodies) > n_cases

        def thunk(rt: Runtime) -> None:
            value = selector(rt)
            labels = checked_labels(labels_t(rt), n_cases, "SwitchDo")
            for i, key in enumerate(labels):
                if key == value:
                    bodies[i](rt)
                    return
            if has_default:
                bodies[-1](rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        selector, labels_t = children[0], children[1]
        bodies = children[2:]
        n_cases = self.n_cases
        has_default = len(bodies) > n_cases

        async def athunk(rt: Runtime) -> None:
            value = await selector(rt)
            labels = checked_labels(await labels_t(rt), n_cases, "SwitchDo")
            for i, key in enumerate(labels):
                if key == value:
                    await bodies[i](rt)
                    return
            if has_default:
                await bodies[-1](rt)

        return athunk


class Park(Control):
    """``Park()`` - never finishes; cancellation ends it.

    The identity of ``Race``: ``Race(x, Park())`` behaves as ``x``, since
    ``Park`` never wins and is cancelled when ``x`` finishes. Also the way to
    hold a branch open on purpose, next to work that ends it by cancelling.

    Notes:
        - No children and no state: it waits on a future nothing resolves.
        - Cancellation is the only way out, and it propagates as
          ``CancelledError`` like any cancelled flow.
        - Async only: the sync path raises ``RuntimeError``, since blocking a
          thread forever has no caller that could end it.

    Yields:
        Nothing. It never returns.

    Example:
        >>> import asyncio
        >>> _ = asyncio.run(nu.arun(nu.Race(nu.print("done"), nu.Park())))
        done
    """

    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "Park requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> None:
            await asyncio.get_running_loop().create_future()

        return athunk
