"""Control concretes - IfDo, ForEachDo, WhileDo."""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.flow import Control
from nu.terms.types import Mode


__all__ = [
    "ForEachDo",
    "IfDo",
    "WhileDo",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class IfDo(Control):
    """`IfDo(cond_q, body_c [, else_c])` - run body if cond is truthy."""

    body_slots: ClassVar[tuple[int, ...]] = (1,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu.terms.dispatch import ExecState, atom_dispatch
        from nu.terms.realization import four_method_pick

        cond_q = self._children[0]
        cond = four_method_pick(cond_q, ExecState.NO_LOOP)(ctx)
        body_idx = 1 if cond else 2
        if body_idx < len(self._children):
            body = self._children[body_idx]
            atom_dispatch(body, ExecState.NO_LOOP)(ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu.terms.dispatch import ExecState, atom_dispatch
        from nu.terms.realization import four_method_pick

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
        from nu.terms.dispatch import ExecState, atom_dispatch

        items_q = self._children[0]
        body = self._children[1]
        opener = getattr(items_q, "open", None)
        if opener is not None:
            for _ in opener(ctx):
                atom_dispatch(body, ExecState.NO_LOOP)(ctx)
        else:
            seq = items_q.eval(ctx)
            for _ in seq:
                atom_dispatch(body, ExecState.NO_LOOP)(ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu.terms.dispatch import ExecState, atom_dispatch

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
        from nu.terms.dispatch import ExecState, atom_dispatch
        from nu.terms.realization import four_method_pick

        cond_q = self._children[0]
        body = self._children[1]
        while four_method_pick(cond_q, ExecState.NO_LOOP)(ctx):
            atom_dispatch(body, ExecState.NO_LOOP)(ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu.terms.dispatch import ExecState, atom_dispatch
        from nu.terms.realization import four_method_pick

        cond_q = self._children[0]
        body = self._children[1]
        while await four_method_pick(cond_q, ExecState.LOOP)(ctx):
            await atom_dispatch(body, ExecState.LOOP)(ctx)
