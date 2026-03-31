"""Iteration flows -- ForRange, ForEach, Fold."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nu import Flow

from ..utils import ensure_term
from .control import Seq


if TYPE_CHECKING:
    from nu import Context, Executable, IntArg, Ref


__all__ = [
    "Fold",
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
    time: ``body = Seq(body, index.store(index + step))``, and an init node
    ``index.store(start)`` is prepended as a child.  This makes the index
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
            init = index.store(ensure_term(start))
            body = Seq(body, index.store(index + ensure_term(step)))
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

    Children layout (no item, no index): ``[items, body]``
    Children layout (with item, no index): ``[items, body]``
    Children layout (with index, no item): ``[items, init, body]``
    Children layout (with item and index): ``[items, init, body]``

    The ``items`` parameter is auto-wrapped via ``ensure_term`` if a literal is
    passed -- it can be a plain list, a ``Ref.get()``, or any Term that
    resolves to an iterable.

    When ``item`` ref is provided, the current element is set on it each
    iteration — no more scratch shapes needed for simple iteration.

    When ``index`` is provided, the body is meta-adjusted:
    ``body = Seq(body, index.store(index + 1))``, init ``index.store(0)``.

    Args:
        items: Iterable (or Term resolving to one) to iterate over.
        body: Executable run for each item.
        item: Optional Ref set with current element each iteration.
        index: Optional Ref[int] set with current iteration index.

    Example::

        item = AnyRef("item")
        ForEach(tokens, body, item=item)
        # item ref holds current element each iteration

        idx = IntRef("idx")
        ForEach([1, 2, 3], process_item, item=item, index=idx)
    """

    def __init__(
        self,
        items: Any,
        body: Executable,
        *,
        item: Ref | None = None,
        index: Ref[int] | None = None,
    ) -> None:
        """Initialize for-each loop.

        Args:
            items: Iterable or Term resolving to an iterable.
            body: Executable run for each item.
            item: Optional Ref set with current element each iteration.
            index: Optional Ref[int] set with current iteration index.
        """
        self._has_index = index is not None
        self._has_item = item is not None
        self._item_ref = item

        if index is not None:
            init = index.store(0)
            body = Seq(body, index.store(index + 1))
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

        for _i, elem in enumerate(items):
            if self._has_item:
                await self._item_ref.store(elem).execute(ctx)
            await body.execute(ctx)


class Fold(Flow):
    """Stateful sequential reduction over an iterable.

    Iterates over items, setting the current element on ``item`` ref
    and executing ``body`` each iteration. The accumulator ``acc`` ref
    holds the running state.

    Children layout: ``[items, init, body]``

    Args:
        items: Iterable (or Term resolving to one) to fold over.
        acc: Ref holding the accumulator state.
        initial: Initial value for the accumulator.
        item: Ref set with current element each iteration.
        body: Executable that updates acc each iteration.

    Example::

        acc = IntRef("acc")
        item = AnyRef("item")
        Fold(
            trades,
            acc=acc,
            initial=0,
            item=item,
            body=acc.store(acc + item),
        )
    """

    def __init__(
        self,
        items: Any,
        *,
        acc: Ref,
        initial: Any,
        item: Ref | None = None,
        body: Executable,
    ) -> None:
        """Initialize fold.

        Args:
            items: Iterable or Term resolving to an iterable.
            acc: Ref holding the accumulator.
            initial: Initial accumulator value.
            item: Optional Ref set with current element each iteration.
            body: Executable updating acc each iteration.
        """
        self._acc_ref = acc
        self._item_ref = item
        self._has_item = item is not None

        init = acc.store(ensure_term(initial))
        super().__init__(ensure_term(items), init, body)

    async def execute(self, ctx: Context) -> None:
        """Execute fold over items."""
        items = await self.children[0].execute(ctx)
        await self.children[1].execute(ctx)  # init acc
        body = self.children[2]

        for elem in items:
            if self._has_item:
                await self._item_ref.store(elem).execute(ctx)
            await body.execute(ctx)
