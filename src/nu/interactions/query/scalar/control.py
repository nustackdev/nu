"""Query-form branches -- If, Switch.

Single-yield Scalar Queries that evaluate a selector and return the
chosen branch's first value. For the imperative Command variants that
dispatch the branch's full stream, see
``nu.interactions.command.flow.control`` (IfDo, SwitchDo).
"""

from __future__ import annotations

from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms import Mode, Query


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from nu.context import Context
    from nu.terms import Nu


__all__ = [
    "If",
    "Switch",
]


class If(Query):
    """Conditional Query. Evaluates cond, yields chosen branch's first value.

    Children: [condition, then_branch, else_branch?]
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.BOTH

    def __init__(
        self,
        condition: Any,
        then_branch: Nu,
        else_branch: Nu | None = None,
    ) -> None:
        if else_branch is None:
            super().__init__(condition, then_branch)
        else:
            super().__init__(condition, then_branch, else_branch)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        cond, *branches = self.children
        if await cond.afirst(ctx):
            branch = branches[0]
        elif len(branches) > 1:
            branch = branches[1]
        else:
            return
        async with aclosing(branch.aopen(ctx)) as gen:
            async for v in gen:
                yield v

    def open(self, ctx: Context) -> Generator[Any, None, None]:
        cond, *branches = self.children
        if cond.first(ctx):
            branch = branches[0]
        elif len(branches) > 1:
            branch = branches[1]
        else:
            return
        with closing(branch.open(ctx)) as gen:
            yield from gen


class Switch(Query):
    """Multi-way Query branching based on a selector value.

    Children: ``[selector, *case_values, default?]``
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.BOTH

    def __init__(
        self,
        selector: Any,
        cases: dict[Any, Nu],
        default: Nu | None = None,
    ) -> None:
        self._case_keys: list[Any] = list(cases.keys())
        self._has_default = default is not None

        children: list = [selector, *cases.values()]
        if default is not None:
            children.append(default)
        super().__init__(*children)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        value = await self.children[0].afirst(ctx)
        for i, key in enumerate(self._case_keys):
            if key == value:
                branch = self.children[i + 1]
                async with aclosing(branch.aopen(ctx)) as gen:
                    async for v in gen:
                        yield v
                return
        if self._has_default:
            branch = self.children[-1]
            async with aclosing(branch.aopen(ctx)) as gen:
                async for v in gen:
                    yield v

    def open(self, ctx: Context) -> Generator[Any, None, None]:
        value = self.children[0].first(ctx)
        for i, key in enumerate(self._case_keys):
            if key == value:
                branch = self.children[i + 1]
                with closing(branch.open(ctx)) as gen:
                    yield from gen
                return
        if self._has_default:
            branch = self.children[-1]
            with closing(branch.open(ctx)) as gen:
                yield from gen
