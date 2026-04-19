"""Control ops -- If, While, DoWhile, Forever, Switch.

(Seq removed: sequential composition is `a > b` on the Nu base.)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nu.terms import Op


if TYPE_CHECKING:
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
    """Conditional execution.

    Children: ``[condition, then_branch, else_branch?]``
    """

    def __init__(
        self,
        condition: Any,
        then_branch: Nu,
        else_branch: Nu | None = None,
    ) -> None:
        if else_branch is not None:
            super().__init__(condition, then_branch, else_branch)
        else:
            super().__init__(condition, then_branch)

    async def execute(self, ctx: Context) -> None:
        if await self.children[0].execute(ctx):
            await self.children[1].execute(ctx)
        elif self._child_count > 2:
            await self.children[2].execute(ctx)


class While(Op):
    """Loop while condition is truthy.

    Children: ``[condition, body]``
    """

    def __init__(self, condition: Any, body: Nu) -> None:
        super().__init__(condition, body)

    async def execute(self, ctx: Context) -> None:
        while await self.children[0].execute(ctx):
            await self.children[1].execute(ctx)


class DoWhile(Op):
    """Execute body first, then loop while condition is truthy.

    Children: ``[condition, body]``
    """

    def __init__(self, condition: Any, body: Nu) -> None:
        super().__init__(condition, body)

    async def execute(self, ctx: Context) -> None:
        await self.children[1].execute(ctx)
        while await self.children[0].execute(ctx):
            await self.children[1].execute(ctx)


class Forever(Op):
    """Execute body indefinitely.

    Children: ``[body]``
    """

    def __init__(self, body: Nu) -> None:
        super().__init__(body)

    async def execute(self, ctx: Context) -> None:
        while True:
            await self.children[0].execute(ctx)


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

    async def execute(self, ctx: Context) -> None:
        value = await self.children[0].execute(ctx)
        for i, key in enumerate(self._case_keys):
            if key == value:
                await self.children[i + 1].execute(ctx)
                return
        if self._has_default:
            await self.children[-1].execute(ctx)
