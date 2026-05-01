"""Control concretes - IfDo, SwitchDo, WhileDo, ForeverDo, ForEachDo, ForRangeDo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.flow import Control
from nu.terms.types import Mode


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu.terms import Arg, IntArg, Nu, StrArg


__all__ = [
    "ForEachDo",
    "ForRangeDo",
    "ForeverDo",
    "IfDo",
    "SwitchDo",
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
    """`ForEachDo(items_q, body_c, item="item")` - run body for each item.

    Binds the current element to `ctx.attrs[item]` before running body,
    so the body can read it via `AttrRef(item)`.
    """

    body_slots: ClassVar[tuple[int, ...]] = (1,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        items: Arg[Iterable],
        body: Nu,
        *,
        item: StrArg = "item",
    ) -> None:
        super().__init__(items, body, item)

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu.terms.dispatch import ExecState, atom_dispatch

        items_q = self._children[0]
        body = self._children[1]
        item_key: str = self._children[2].eval(ctx)
        opener = getattr(items_q, "open", None)
        if opener is not None:
            for elem in opener(ctx):
                ctx.attrs[item_key] = elem
                atom_dispatch(body, ExecState.NO_LOOP)(ctx)
        else:
            seq = items_q.eval(ctx)
            for elem in seq:
                ctx.attrs[item_key] = elem
                atom_dispatch(body, ExecState.NO_LOOP)(ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu.terms.dispatch import ExecState, atom_dispatch

        items_q = self._children[0]
        body = self._children[1]
        item_key: str = await self._children[2].aeval(ctx)
        opener = getattr(items_q, "aopen", None)
        if opener is not None:
            async for elem in opener(ctx):
                ctx.attrs[item_key] = elem
                await atom_dispatch(body, ExecState.LOOP)(ctx)
        else:
            seq = await items_q.aeval(ctx)
            for elem in seq:
                ctx.attrs[item_key] = elem
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


class ForeverDo(Control):
    """Execute body indefinitely.

    Children: ``[body]``
    """

    body_slots: ClassVar[tuple[int, ...]] = (0,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, body: Nu) -> None:
        super().__init__(body)

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu import runtime

        body = self._children[0]
        while True:
            runtime.execute(body, ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu import runtime

        body = self._children[0]
        while True:
            await runtime.aexecute(body, ctx)


class ForRangeDo(Control):
    """Counted loop over ``range(start, stop, step)``.

    Children: ``[start, stop, step, body]`` or
    ``[start, stop, step, body, index_key]``. Body lives at slot 3.

    Sets ``ctx.attrs[index_key]`` to the current loop value each
    iteration when an index key is provided.
    """

    body_slots: ClassVar[tuple[int, ...]] = (3,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        start: IntArg,
        stop: IntArg,
        body: Nu,
        *,
        step: IntArg = 1,
        index: StrArg | None = None,
    ) -> None:
        self._has_index = index is not None
        children: list = [start, stop, step, body]
        if index is not None:
            children.append(index)
        super().__init__(*children)

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu import runtime

        start = self._children[0].eval(ctx)
        stop = self._children[1].eval(ctx)
        step = self._children[2].eval(ctx)
        body = self._children[3]

        index_key: str | None = None
        if self._has_index:
            index_key = self._children[4].eval(ctx)

        for i in range(start, stop, step):
            if index_key is not None:
                ctx.attrs[index_key] = i
            runtime.execute(body, ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu import runtime

        start = await self._children[0].aeval(ctx)
        stop = await self._children[1].aeval(ctx)
        step = await self._children[2].aeval(ctx)
        body = self._children[3]

        index_key: str | None = None
        if self._has_index:
            index_key = await self._children[4].aeval(ctx)

        for i in range(start, stop, step):
            if index_key is not None:
                ctx.attrs[index_key] = i
            await runtime.aexecute(body, ctx)


class SwitchDo(Control):
    """Multi-way branching based on a selector value.

    Children: ``[selector, *case_bodies, default?]``

    Selector is at slot 0 (Query). All other slots are Command bodies
    (case branches and the optional default branch).
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(
        self,
        selector: Any,  # noqa: ANN401
        cases: dict[Any, Nu],
        default: Nu | None = None,
    ) -> None:
        self._case_keys: list[Any] = list(cases.keys())
        self._has_default = default is not None

        children: list = [selector, *cases.values()]
        if default is not None:
            children.append(default)
        super().__init__(*children)

    body_slots: ClassVar[tuple[int, ...]] = tuple(range(1, 1024))

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu import runtime

        value = self._children[0].eval(ctx)
        for i, key in enumerate(self._case_keys):
            if key == value:
                runtime.execute(self._children[i + 1], ctx)
                return
        if self._has_default:
            runtime.execute(self._children[-1], ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu import runtime

        value = await self._children[0].aeval(ctx)
        for i, key in enumerate(self._case_keys):
            if key == value:
                await runtime.aexecute(self._children[i + 1], ctx)
                return
        if self._has_default:
            await runtime.aexecute(self._children[-1], ctx)
