"""Iteration flows -- ForRange, ForEach, ForEachParallel."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from everybase import Flow

from ..utils import ensure_term
from .control import Seq


if TYPE_CHECKING:
    from everybase import Context, Executable, IntArg, Ref


__all__ = [
    "ForEach",
    "ForRange",
]


class ForRange(Flow):
    """Counted loop over ``range(start, stop, step)``.

    Children layout (no index): ``[start, stop, step, body]``
    Children layout (with index): ``[start, stop, step, init, body]``

    Start, stop and step are auto-wrapped via ``ensure_term`` if literals are
    passed.  Optional ``index`` Ref is set with the current loop value
    at each iteration.

    When ``index`` is provided, the body is meta-adjusted at construction
    time: ``body = Seq(body, index.set(index + step))``, and an init node
    ``index.set(start)`` is prepended as a child.  This makes the index
    setter a tree-visible child, so meta-transforms (auto_atomic, etc.)
    can see and wrap it.

    Args:
        start: Start of range (inclusive), int or Term.
        stop: End of range (exclusive), int or Term.
        body: Executable run each iteration.
        step: Step increment, int or Term. Default ``1``.
        index: Optional Ref[int] set with current value each iteration.

    Example::

        i = Var(0)
        ForRange(0, 10, body, index=i)
        # after execution i holds the last iterated value (9)
    """

    def __init__(
        self,
        start: IntArg,
        stop: IntArg,
        body: Executable,
        *,
        step: IntArg = 1,
        index: Ref[int] | None = None,
    ) -> None:
        """Initialize for-range loop.

        Args:
            start: Start of range (inclusive), int or Term.
            stop: End of range (exclusive), int or Term.
            body: Executable run each iteration.
            step: Step increment, int or Term. Default ``1``.
            index: Optional Ref[int] set with current value each iteration.
        """
        start_t = ensure_term(start)
        stop_t = ensure_term(stop)
        step_t = ensure_term(step)

        self._has_index = index is not None

        if index is not None:
            init = index.set(ensure_term(start))
            body = Seq(body, index.set(index + ensure_term(step)))
            super().__init__(start_t, stop_t, step_t, init, body)
        else:
            super().__init__(start_t, stop_t, step_t, body)

    async def execute(self, ctx: Context) -> None:
        """Execute body for each value in range."""
        start = await self.children[0].execute(ctx)
        stop = await self.children[1].execute(ctx)
        step = await self.children[2].execute(ctx)

        if self._has_index:
            await self.children[3].execute(ctx)  # init index
            body = self.children[4]
        else:
            body = self.children[3]

        for _i in range(start, stop, step):
            await body.execute(ctx)


class ForEach(Flow):
    """Iterate over a sequence, executing body for each item.

    Children layout (no index): ``[items, body]``
    Children layout (with index): ``[items, init, body]``

    The ``items`` parameter is auto-wrapped via ``ensure_term`` if a literal is
    passed -- it can be a plain list, a ``Ref.get()``, or any Term that
    resolves to an iterable.  Optional ``index`` Ref is set with the
    current iteration index.

    When ``index`` is provided, the body is meta-adjusted:
    ``body = Seq(body, index.set(index + 1))``, init ``index.set(0)``.

    Args:
        items: Iterable (or Term resolving to one) to iterate over.
        body: Executable run for each item.
        index: Optional Ref[int] set with current iteration index.

    Example::

        idx = Var(0)
        ForEach([1, 2, 3], process_item, index=idx)
    """

    def __init__(
        self,
        items: Any,
        body: Executable,
        *,
        index: Ref[int] | None = None,
    ) -> None:
        """Initialize for-each loop.

        Args:
            items: Iterable or Term resolving to an iterable.
            body: Executable run for each item.
            index: Optional Ref[int] set with current iteration index.
        """
        self._has_index = index is not None

        if index is not None:
            init = index.set(0)
            body = Seq(body, index.set(index + 1))
            super().__init__(ensure_term(items), init, body)
        else:
            super().__init__(ensure_term(items), body)

    async def execute(self, ctx: Context) -> None:
        """Execute body for each item in the resolved sequence."""
        items = await self.children[0].execute(ctx)

        if self._has_index:
            await self.children[1].execute(ctx)  # init index
            body = self.children[2]
        else:
            body = self.children[1]

        for _i, _item in enumerate(items):
            await body.execute(ctx)
