"""Control flow primitives -- Seq, If, While, DoWhile, Forever, Switch."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from everybase import Flow

from ..utils import ensure_term


if TYPE_CHECKING:
    from everybase import Context, Executable


__all__ = [
    "DoWhile",
    "Forever",
    "If",
    "Seq",
    "Switch",
    "While",
]


class Seq(Flow):
    """Execute children sequentially.

    Inherits Flow's default execute() which already runs
    children in order. This class exists for explicit naming.

    Children layout: [*children]

    Example::

        Seq(step_a, step_b, step_c)
    """

    def __init__(self, *children: Executable) -> None:
        """Initialize sequential flow.

        Args:
            *children: Executables to run in order.
        """
        super().__init__(*children)


class If(Flow):
    """Conditional execution.

    Children layout: [condition, then_branch, else_branch?]

    Condition is auto-wrapped via ``ensure_term`` if a literal is passed.
    All computation parameters are children -- fully transparent
    to tree transforms.

    Example::

        If(x > 0, handle_positive, handle_non_positive)
        If(True, always_runs)
    """

    def __init__(
        self,
        condition: Any,
        then_branch: Executable,
        else_branch: Executable | None = None,
    ) -> None:
        """Initialize conditional flow.

        Args:
            condition: Term or literal evaluated as boolean.
            then_branch: Executed when condition is truthy.
            else_branch: Executed when condition is falsy (optional).
        """
        condition = ensure_term(condition)
        if else_branch is not None:
            super().__init__(condition, then_branch, else_branch)
        else:
            super().__init__(condition, then_branch)

    async def execute(self, ctx: Context) -> None:
        """Evaluate condition and execute the appropriate branch."""
        if await self.children[0].execute(ctx):
            await self.children[1].execute(ctx)
        elif self.child_count > 2:
            await self.children[2].execute(ctx)


class While(Flow):
    """Loop while condition is truthy.

    Children layout: [condition, body]

    Condition is auto-wrapped via ``ensure_term`` if a literal is passed.

    Example::

        counter = Var(0)
        While(counter < 10, increment_body)
    """

    def __init__(self, condition: Any, body: Executable) -> None:
        """Initialize while loop.

        Args:
            condition: Term or literal evaluated as boolean each iteration.
            body: Executed while condition is truthy.
        """
        super().__init__(ensure_term(condition), body)

    async def execute(self, ctx: Context) -> None:
        """Execute body while condition is truthy."""
        while await self.children[0].execute(ctx):
            await self.children[1].execute(ctx)


class DoWhile(Flow):
    """Loop that executes body first, then checks condition.

    Children layout: [condition, body]

    Body is always executed at least once. Condition is evaluated
    after each iteration; loop continues while condition is truthy.
    Condition is auto-wrapped via ``ensure_term`` if a literal is passed.

    Example::

        counter = Var(0)
        DoWhile(counter < 10, process_and_increment)
    """

    def __init__(self, condition: Any, body: Executable) -> None:
        """Initialize do-while loop.

        Args:
            condition: Term or literal evaluated as boolean after each iteration.
            body: Executed at least once, then repeated while condition is truthy.
        """
        super().__init__(ensure_term(condition), body)

    async def execute(self, ctx: Context) -> None:
        """Execute body, then repeat while condition is truthy."""
        await self.children[1].execute(ctx)
        while await self.children[0].execute(ctx):
            await self.children[1].execute(ctx)


class Forever(Flow):
    """Loop that executes body indefinitely.

    Children layout: [body]

    Runs body in an infinite loop. Termination must come from
    an external mechanism (e.g. exception, cancellation).

    Example::

        Forever(poll_and_process)
    """

    def __init__(self, body: Executable) -> None:
        """Initialize infinite loop.

        Args:
            body: Executed repeatedly without end.
        """
        super().__init__(body)

    async def execute(self, ctx: Context) -> None:
        """Execute body in an infinite loop."""
        while True:
            await self.children[0].execute(ctx)


class Switch(Flow):
    """Multi-way branching based on a selector value.

    Children layout: [selector, *case_values, default?]

    Selector is auto-wrapped via ``ensure_term`` if a literal is passed.
    Case values are children, making them visible to tree transforms.
    The internal ``_case_keys`` list maps child index offsets (after
    the selector at index 0) to their corresponding case keys.

    Example::

        Switch(
            mode_var,
            cases={
                "fast": fast_handler,
                "slow": slow_handler,
                "debug": debug_handler,
            },
            default=fallback_handler,
        )
    """

    def __init__(
        self,
        selector: Any,
        cases: dict[Any, Executable],
        default: Executable | None = None,
    ) -> None:
        """Initialize switch flow.

        Args:
            selector: Term or literal whose value selects a branch.
            cases: Mapping from case keys to executables. Each value
                becomes a child node in the tree.
            default: Executed when no case key matches (optional).
        """
        self._case_keys: list[Any] = list(cases.keys())
        self._has_default = default is not None

        children: list[Executable] = [ensure_term(selector)]
        children.extend(cases.values())
        if default is not None:
            children.append(default)
        super().__init__(*children)

    async def execute(self, ctx: Context) -> None:
        """Evaluate selector and execute the matching case branch."""
        value = await self.children[0].execute(ctx)
        for i, key in enumerate(self._case_keys):
            if key == value:
                await self.children[i + 1].execute(ctx)
                return
        if self._has_default:
            await self.children[-1].execute(ctx)
