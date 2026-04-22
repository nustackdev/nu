"""Control Flow Commands -- IfDo, While, DoWhile, Forever, SwitchDo.

These dispatch the chosen branch as an imperative mutation. For Query-form
(single-yield, returns the chosen branch's value), see
``nu.interactions.query.scalar.control``.
"""

from __future__ import annotations

from contextlib import aclosing, closing
from typing import TYPE_CHECKING, Any

from nu.terms import Flow


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from nu.context import Context
    from nu.terms import Nu


__all__ = [
    "DoWhile",
    "Forever",
    "IfDo",
    "SwitchDo",
    "While",
]


class IfDo(Flow):
    """Conditional branch (Command). Evaluates cond, runs chosen branch's stream.

    Children: [condition, then_branch, else_branch?]
    """

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


class While(Flow):
    """Loop while condition is truthy.

    Children: ``[condition, body]``
    """

    def __init__(self, condition: Any, body: Nu) -> None:
        super().__init__(condition, body)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        cond, body = self.children
        while await cond.afirst(ctx):
            async with aclosing(body.aopen(ctx)) as gen:
                async for v in gen:
                    yield v

    def open(self, ctx: Context) -> Generator[Any, None, None]:
        cond, body = self.children
        while cond.first(ctx):
            with closing(body.open(ctx)) as gen:
                yield from gen


class DoWhile(Flow):
    """Execute body first, then loop while condition is truthy.

    Children: ``[condition, body]``
    """

    def __init__(self, condition: Any, body: Nu) -> None:
        super().__init__(condition, body)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        cond, body = self.children
        async with aclosing(body.aopen(ctx)) as gen:
            async for v in gen:
                yield v
        while await cond.afirst(ctx):
            async with aclosing(body.aopen(ctx)) as gen:
                async for v in gen:
                    yield v

    def open(self, ctx: Context) -> Generator[Any, None, None]:
        cond, body = self.children
        with closing(body.open(ctx)) as gen:
            yield from gen
        while cond.first(ctx):
            with closing(body.open(ctx)) as gen:
                yield from gen


class Forever(Flow):
    """Execute body indefinitely.

    Children: ``[body]``
    """

    def __init__(self, body: Nu) -> None:
        super().__init__(body)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        body = self.children[0]
        while True:
            async with aclosing(body.aopen(ctx)) as gen:
                async for v in gen:
                    yield v

    def open(self, ctx: Context) -> Generator[Any, None, None]:
        body = self.children[0]
        while True:
            with closing(body.open(ctx)) as gen:
                yield from gen


class SwitchDo(Flow):
    """Multi-way branching Command based on a selector value.

    Children: ``[selector, *case_values, default?]``
    """

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
