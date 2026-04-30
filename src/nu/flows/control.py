"""Control concretes - IfDo, ForEachDo, WhileDo, While, DoWhile, Forever, SwitchDo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.flow import Control
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.terms import Nu


__all__ = [
    "DoWhile",
    "ForEachDo",
    "Forever",
    "IfDo",
    "SwitchDo",
    "While",
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


class While(Control):
    """Loop while condition is truthy.

    Children: ``[condition, body]`` -- body is the Command at slot 1.
    """

    body_slots: ClassVar[tuple[int, ...]] = (1,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, condition: Any, body: Nu) -> None:  # noqa: ANN401
        super().__init__(condition, body)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        cond_q = self._children[0]
        body = self._children[1]
        while runtime.first(cond_q, ctx):
            runtime.execute(body, ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        cond_q = self._children[0]
        body = self._children[1]
        while await runtime.afirst(cond_q, ctx):
            await runtime.aexecute(body, ctx)


class DoWhile(Control):
    """Execute body first, then loop while condition is truthy.

    Children: ``[body, condition]`` -- body is the Command at slot 0.
    """

    body_slots: ClassVar[tuple[int, ...]] = (0,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, condition: Any, body: Nu) -> None:  # noqa: ANN401
        # Body in slot 0, condition in slot 1 to satisfy body_slots invariants.
        super().__init__(body, condition)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        body = self._children[0]
        cond_q = self._children[1]
        runtime.execute(body, ctx)
        while runtime.first(cond_q, ctx):
            runtime.execute(body, ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        body = self._children[0]
        cond_q = self._children[1]
        await runtime.aexecute(body, ctx)
        while await runtime.afirst(cond_q, ctx):
            await runtime.aexecute(body, ctx)


class Forever(Control):
    """Execute body indefinitely.

    Children: ``[body]``
    """

    body_slots: ClassVar[tuple[int, ...]] = (0,)
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, body: Nu) -> None:
        super().__init__(body)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        body = self._children[0]
        while True:
            runtime.execute(body, ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        body = self._children[0]
        while True:
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

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        value = runtime.first(self._children[0], ctx)
        for i, key in enumerate(self._case_keys):
            if key == value:
                runtime.execute(self._children[i + 1], ctx)
                return
        if self._has_default:
            runtime.execute(self._children[-1], ctx)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        value = await runtime.afirst(self._children[0], ctx)
        for i, key in enumerate(self._case_keys):
            if key == value:
                await runtime.aexecute(self._children[i + 1], ctx)
                return
        if self._has_default:
            await runtime.aexecute(self._children[-1], ctx)
