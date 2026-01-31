"""Loop flows -- While and ForRange."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from everyabc import Flow

from ._util import _ensure_term


if TYPE_CHECKING:
    from everyabc import Context, Executable

    from .var import Var


__all__ = [
    "ForRange",
    "While",
]


class While(Flow):
    """Loop while condition is truthy.

    Children layout: [condition, body]

    Condition is auto-wrapped via Const if a literal is passed.

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
        super().__init__(_ensure_term(condition), body)

    async def execute(self, ctx: Context) -> None:
        """Execute body while condition is truthy."""
        while await self.children[0].execute(ctx):
            await self.children[1].execute(ctx)


class ForRange(Flow):
    """Counted loop over range(start, stop, step).

    Children layout: [start, stop, step, body]

    Start, stop, step are auto-wrapped via Const if literals.
    Optional index Var is written at each iteration.

    Example::

        i = Var(0)
        ForRange(0, 10, body, index=i)
        # i.get() == 9 after execution
    """

    def __init__(
        self,
        start: Any,
        stop: Any,
        body: Executable,
        *,
        step: Any = 1,
        index: Var[int] | None = None,
    ) -> None:
        """Initialize for-range loop.

        Args:
            start: Start of range (inclusive), int or Term.
            stop: End of range (exclusive), int or Term.
            body: Executed each iteration.
            step: Step increment, int or Term. Default 1.
            index: Optional Var written with current index each iteration.
        """
        super().__init__(
            _ensure_term(start),
            _ensure_term(stop),
            _ensure_term(step),
            body,
        )
        self._index = index

    async def execute(self, ctx: Context) -> None:
        """Execute body for each value in range."""
        start = await self.children[0].execute(ctx)
        stop = await self.children[1].execute(ctx)
        step = await self.children[2].execute(ctx)
        body = self.children[3]

        for i in range(start, stop, step):
            if self._index is not None:
                self._index.set(i)
            await body.execute(ctx)
