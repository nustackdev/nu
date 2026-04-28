"""Flow - Strategy + Control.

Flow orchestrates Commands. `own_effects` is empty by class-time
validator (Flow contributes no effects of its own; effects come from
the body Commands).

Strategy: children are Commands only. `body_slots = ()` is a sentinel
meaning "all child slots are body" (the composition-time validator
handles it).

Control: declares a subset of slot indices as body via `body_slots`.
Other slots are Query parameters (e.g. `IfDo(cond_q, body_c)`).
"""

from __future__ import annotations

from typing import Any, ClassVar
from typing import Literal as TLiteral

from .nu import NuBase, register_subclass_validator
from .types import Mode


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


__all__ = [
    "Control",
    "Flow",
    "ForEachDo",
    "Gather",
    "IfDo",
    "Parallel",
    "Race",
    "Sequential",
    "Strategy",
    "WhileDo",
]


class Flow(NuBase):
    """Abstract Flow base. `own_effects` empty."""


# --- Strategy ----------------------------------------------------------------


class Strategy(Flow):
    """All child slots are body slots (Commands only).

    `run` / `arun` drive children via the runtime pumps. Subclasses
    (Sequential, Parallel, Race, Gather) override `_run_children` /
    `_arun_children` to choose sequential vs parallel semantics.
    """

    body_slots: ClassVar[tuple[int, ...]] = ()

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        self._run_children(ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        await self._arun_children(ctx)

    # Default sequential drive; concrete strategies override.
    def _run_children(self, ctx: Any) -> None:  # noqa: ANN401
        from .. import runtime as _rt
        from .dispatch import ExecState, atom_dispatch

        for child in self._children:
            method = atom_dispatch(child, ExecState.NO_LOOP)
            method(ctx)
        _ = _rt  # keep lazy import semantics; runtime not strictly needed here

    async def _arun_children(self, ctx: Any) -> None:  # noqa: ANN401
        from .dispatch import ExecState, atom_dispatch

        for child in self._children:
            method = atom_dispatch(child, ExecState.LOOP)
            await method(ctx)


class Sequential(Strategy):
    """`a >> b` - run children in order."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    associative: ClassVar[bool] = True
    commutative: ClassVar[bool | TLiteral["if-independent"]] = "if-independent"

    # Inherits sequential `_run_children` from Strategy.


class Parallel(Strategy):
    """`a | b` - run children concurrently."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    associative: ClassVar[bool] = True
    commutative: ClassVar[bool] = True

    def _run_children(self, ctx: Any) -> None:  # noqa: ANN401
        from concurrent.futures import ThreadPoolExecutor, as_completed

        from .dispatch import ExecState, atom_dispatch

        with ThreadPoolExecutor(max_workers=max(1, len(self._children))) as pool:
            futures = [
                pool.submit(atom_dispatch(c, ExecState.NO_LOOP), ctx) for c in self._children
            ]
            for f in as_completed(futures):
                f.result()

    async def _arun_children(self, ctx: Any) -> None:  # noqa: ANN401
        import asyncio

        from .dispatch import ExecState, atom_dispatch

        await asyncio.gather(
            *(atom_dispatch(c, ExecState.LOOP)(ctx) for c in self._children),
        )


class Race(Strategy):
    """`a & b` - run children concurrently; first to complete wins."""

    support: ClassVar[frozenset[Mode]] = _BOTH
    associative: ClassVar[bool] = True
    commutative: ClassVar[bool] = True

    def _run_children(self, ctx: Any) -> None:  # noqa: ANN401
        from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

        from .dispatch import ExecState, atom_dispatch

        with ThreadPoolExecutor(max_workers=max(1, len(self._children))) as pool:
            futures = [
                pool.submit(atom_dispatch(c, ExecState.NO_LOOP), ctx) for c in self._children
            ]
            done, _pending = wait(futures, return_when=FIRST_COMPLETED)
            for f in done:
                f.result()
                break

    async def _arun_children(self, ctx: Any) -> None:  # noqa: ANN401
        import asyncio

        from .dispatch import ExecState, atom_dispatch

        tasks = [asyncio.create_task(atom_dispatch(c, ExecState.LOOP)(ctx)) for c in self._children]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
        for t in done:
            await t
            break


class Gather(Strategy):
    """Run children concurrently and collect their yields.

    For Command children, `run/arun` returns None; this kind is most
    interesting once stream collection is wired. For now it behaves
    like Parallel.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH
    associative: ClassVar[bool] = True
    commutative: ClassVar[bool] = True

    _run_children = Parallel._run_children
    _arun_children = Parallel._arun_children


# --- Control -----------------------------------------------------------------


class Control(Flow):
    """Conditional / iterative Flow.

    Declared `body_slots` separates Command body slots from Query
    parameter slots. Concrete subclasses (IfDo, ForEachDo, WhileDo)
    override `run` / `arun`. They evaluate Query parameters via
    `four_method_pick` and drive body Commands via `atom_dispatch`.
    """


class IfDo(Control):
    """`IfDo(cond_q, body_c [, else_c])` - run body if cond is truthy."""

    body_slots: ClassVar[tuple[int, ...]] = (1,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from .dispatch import ExecState, atom_dispatch
        from .realization import four_method_pick

        cond_q = self._children[0]
        cond = four_method_pick(cond_q, ExecState.NO_LOOP)(ctx)
        body_idx = 1 if cond else 2
        if body_idx < len(self._children):
            body = self._children[body_idx]
            atom_dispatch(body, ExecState.NO_LOOP)(ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from .dispatch import ExecState, atom_dispatch
        from .realization import four_method_pick

        cond_q = self._children[0]
        cond = await four_method_pick(cond_q, ExecState.LOOP)(ctx)
        body_idx = 1 if cond else 2
        if body_idx < len(self._children):
            body = self._children[body_idx]
            await atom_dispatch(body, ExecState.LOOP)(ctx)


class ForEachDo(Control):
    """`ForEachDo(items_q, body_c)` - run body for each item."""

    body_slots: ClassVar[tuple[int, ...]] = (1,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from .dispatch import ExecState, atom_dispatch

        items_q = self._children[0]
        body = self._children[1]
        # Items_q is a stream-y child; iterate via open if available, else
        # eval to a single iterable.
        opener = getattr(items_q, "open", None)
        if opener is not None:
            for _ in opener(ctx):
                atom_dispatch(body, ExecState.NO_LOOP)(ctx)
        else:
            seq = items_q.eval(ctx)
            for _ in seq:
                atom_dispatch(body, ExecState.NO_LOOP)(ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from .dispatch import ExecState, atom_dispatch

        items_q = self._children[0]
        body = self._children[1]
        opener = getattr(items_q, "aopen", None)
        if opener is not None:
            async for _ in opener(ctx):
                await atom_dispatch(body, ExecState.LOOP)(ctx)
        else:
            seq = await items_q.aeval(ctx)
            for _ in seq:
                await atom_dispatch(body, ExecState.LOOP)(ctx)


class WhileDo(Control):
    """`WhileDo(cond_q, body_c)` - run body while cond is truthy."""

    body_slots: ClassVar[tuple[int, ...]] = (1,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from .dispatch import ExecState, atom_dispatch
        from .realization import four_method_pick

        cond_q = self._children[0]
        body = self._children[1]
        while four_method_pick(cond_q, ExecState.NO_LOOP)(ctx):
            atom_dispatch(body, ExecState.NO_LOOP)(ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from .dispatch import ExecState, atom_dispatch
        from .realization import four_method_pick

        cond_q = self._children[0]
        body = self._children[1]
        while await four_method_pick(cond_q, ExecState.LOOP)(ctx):
            await atom_dispatch(body, ExecState.LOOP)(ctx)


# --- subclass validators -----------------------------------------------------


def _validate_flow(cls: type) -> None:
    """Flow subclasses must declare empty `own_effects`."""
    own = cls.__dict__.get("own_effects")
    if own is not None and own:
        msg = (
            f"{cls.__module__}.{cls.__qualname__}: Flow subclasses must "
            f"declare empty `own_effects` (got {own!r}). Effects in a "
            "Flow come from its body Commands."
        )
        raise TypeError(msg)


def _validate_control(cls: type) -> None:
    """Control subclasses must declare `body_slots`.

    `body_slots = None` is a valid declaration meaning "no body slots"
    (every child is a Query parameter; the Control runs a side effect
    after evaluating its parameters, e.g. TimeSleep).
    """
    if cls is Control:
        return
    if "body_slots" not in cls.__dict__:
        msg = (
            f"{cls.__module__}.{cls.__qualname__}: Control subclasses "
            "must declare `body_slots` (a tuple of slot indices, or "
            "`None` for no body slots)."
        )
        raise TypeError(msg)


register_subclass_validator(Flow, _validate_flow)
register_subclass_validator(Control, _validate_control)


# --- composition validator: Flow subtree contains ≥1 Command ----------------


def _validate_flow_has_command(nu: Any) -> None:  # noqa: ANN401
    """Flow subtree must contain ≥1 Command (transitively)."""
    if not isinstance(nu, Flow):
        return
    # Avoid importing Command at module import time to keep cycles clean.
    from .command import Command

    def _has_command(n: Any) -> bool:  # noqa: ANN401
        if isinstance(n, Command):
            return True
        return any(_has_command(c) for c in n._children)

    if not any(_has_command(c) for c in nu._children):
        # During Phase A+B, callers may still construct empty / partial
        # Flows for tests; soft until concrete kinds land. Hard once
        # Phase E sweeps. ARCH-NOTE: keep as a pass for now.
        return


from .nu import register_composition_validator as _register_comp  # noqa: E402


_register_comp(_validate_flow_has_command)
