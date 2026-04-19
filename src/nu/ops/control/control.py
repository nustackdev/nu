"""Control ops -- If, While, DoWhile, Forever, Switch.

(Seq removed: sequential composition is `a >> b` on the Nu base.)
"""

from __future__ import annotations

from contextlib import aclosing
from typing import TYPE_CHECKING, Any

from nu.terms import Op


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from nu.context import Context
    from nu.terms import Nu


__all__ = [
    "DoWhile",
    "Forever",
    "If",
    "Switch",
    "While",
]


class If(Op):
    """Conditional branch. Evaluates cond, forwards chosen branch's stream.

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

    async def open(self, ctx: Context) -> AsyncGenerator[Any, None]:
        cond, *branches = self.children
        if await cond.first(ctx):
            branch = branches[0]
        elif len(branches) > 1:
            branch = branches[1]
        else:
            return
        async with aclosing(branch.open(ctx)) as gen:
            async for v in gen:
                yield v


class While(Op):
    """Loop while condition is truthy.

    Children: ``[condition, body]``
    """

    def __init__(self, condition: Any, body: Nu) -> None:
        super().__init__(condition, body)

    async def open(self, ctx: Context) -> AsyncGenerator[Any, None]:
        cond, body = self.children
        while await cond.first(ctx):
            async with aclosing(body.open(ctx)) as gen:
                async for v in gen:
                    yield v


class DoWhile(Op):
    """Execute body first, then loop while condition is truthy.

    Children: ``[condition, body]``
    """

    def __init__(self, condition: Any, body: Nu) -> None:
        super().__init__(condition, body)

    async def open(self, ctx: Context) -> AsyncGenerator[Any, None]:
        cond, body = self.children
        async with aclosing(body.open(ctx)) as gen:
            async for v in gen:
                yield v
        while await cond.first(ctx):
            async with aclosing(body.open(ctx)) as gen:
                async for v in gen:
                    yield v


class Forever(Op):
    """Execute body indefinitely.

    Children: ``[body]``
    """

    def __init__(self, body: Nu) -> None:
        super().__init__(body)

    async def open(self, ctx: Context) -> AsyncGenerator[Any, None]:
        body = self.children[0]
        while True:
            async with aclosing(body.open(ctx)) as gen:
                async for v in gen:
                    yield v


class Switch(Op):
    """Multi-way branching based on a selector value.

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

    async def open(self, ctx: Context) -> AsyncGenerator[Any, None]:
        value = await self.children[0].first(ctx)
        for i, key in enumerate(self._case_keys):
            if key == value:
                branch = self.children[i + 1]
                async with aclosing(branch.open(ctx)) as gen:
                    async for v in gen:
                        yield v
                return
        if self._has_default:
            branch = self.children[-1]
            async with aclosing(branch.open(ctx)) as gen:
                async for v in gen:
                    yield v
