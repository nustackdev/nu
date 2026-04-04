"""Iteration flows -- ForRange, ForEach, Fold."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import Flow

from nu.utils import ensure_nu


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import Nu, IntArg


__all__ = [
    "Fold",
    "ForEach",
    "ForRange",
]


class ForRange(Flow):
    """Counted loop over ``range(start, stop, step)``.

    Children layout: ``[start, stop, step, body]``

    Start, stop and step are auto-wrapped via ``ensure_nu`` if literals are
    passed.  Optional ``index`` names a ``ctx.attrs`` key set with the
    current loop value at each iteration.  Read it in the body via an
    AttrRef (e.g. ``IntRef("i")``).

    If you need the index persisted to a Shape, write it in the body::

        s.my_index.store(IntRef("i"))

    Args:
        start: Start of range (inclusive), int or Nu.
        stop: End of range (exclusive), int or Nu.
        body: Nu run each iteration.
        step: Step increment, int or Nu. Default ``1``.
        index: Optional ctx.attrs key set with current value each iteration.

    Example::

        idx = IntRef("i")
        ForRange(0, 10, Print("at", idx), index="i")
    """

    def __init__(
        self,
        start: IntArg,
        stop: IntArg,
        body: Nu,
        *,
        step: IntArg = 1,
        index: str | None = None,
    ) -> None:
        """Initialize for-range loop.

        Args:
            start: Start of range (inclusive), int or Nu.
            stop: End of range (exclusive), int or Nu.
            body: Nu run each iteration.
            step: Step increment, int or Nu. Default ``1``.
            index: ctx.attrs key set with current value each iteration.
        """
        self._index_attr = index
        super().__init__(ensure_nu(start), ensure_nu(stop), ensure_nu(step), body)

    async def execute(self, ctx: Context) -> None:
        """Execute body for each value in range."""
        start = await self.children[0].execute(ctx)
        stop = await self.children[1].execute(ctx)
        step = await self.children[2].execute(ctx)
        body = self.children[3]

        for i in range(start, stop, step):
            if self._index_attr is not None:
                ctx.attrs[self._index_attr] = i
            await body.execute(ctx)


class ForEach(Flow):
    """Iterate over a sequence, executing body for each element.

    Children layout: ``[items, body]``

    The ``items`` parameter is auto-wrapped via ``ensure_nu`` if a literal is
    passed -- it can be a plain list, a ``Ref.get()``, or any Nu that
    resolves to an iterable.

    Optional ``index`` names a ``ctx.attrs`` key set with the current
    iteration count.  Read it in the body via ``IntRef("i")``.

    Items are not stored by default to preserve laziness.

    Args:
        items: Iterable (or Nu resolving to one) to iterate over.
        body: Nu run for each element.
        index: Optional ctx.attrs key set with current iteration index.

    Example::

        idx = IntRef("i")
        ForEach(tokens, process, index="i")
    """

    def __init__(
        self,
        items: Any,
        body: Nu,
        *,
        index: str | None = None,
    ) -> None:
        """Initialize for-each loop.

        Args:
            items: Iterable or Nu resolving to an iterable.
            body: Nu run for each element.
            index: ctx.attrs key set with current iteration index.
        """
        self._index_attr = index
        super().__init__(ensure_nu(items), body)

    async def execute(self, ctx: Context) -> None:
        """Execute body for each element in the resolved sequence."""
        items = await self.children[0].execute(ctx)
        body = self.children[1]

        for i, _elem in enumerate(items):
            if self._index_attr is not None:
                ctx.attrs[self._index_attr] = i
            await body.execute(ctx)


class Fold(Flow):
    """Stateful sequential reduction over an iterable.

    Children layout: ``[items, initial, body]``

    Iterates over items, setting the current element on the ``item``
    ctx.attrs key and executing ``body`` each iteration.  The ``acc``
    ctx.attrs key holds the running accumulator.  Read both in the body
    via AttrRefs.

    Args:
        items: Iterable (or Nu resolving to one) to fold over.
        acc: ctx.attrs key for the accumulator.
        initial: Initial value for the accumulator (literal or Nu).
        item: ctx.attrs key for the current element.
        body: Nu that updates acc each iteration.

    Example::

        acc = IntRef("acc")
        item = AnyRef("item")
        Fold(
            trades,
            acc="acc",
            initial=0,
            item="item",
            body=acc.store(acc + item),
        )
    """

    def __init__(
        self,
        items: Any,
        *,
        acc: str = "acc",
        initial: Any,
        item: str = "item",
        body: Nu,
    ) -> None:
        """Initialize fold.

        Args:
            items: Iterable or Nu resolving to an iterable.
            acc: ctx.attrs key for the accumulator.
            initial: Initial accumulator value (literal or Nu).
            item: ctx.attrs key for the current element.
            body: Nu updating acc each iteration.
        """
        self._acc_attr = acc
        self._item_attr = item
        super().__init__(ensure_nu(items), ensure_nu(initial), body)

    async def execute(self, ctx: Context) -> None:
        """Execute fold over items."""
        items = await self.children[0].execute(ctx)
        ctx.attrs[self._acc_attr] = await self.children[1].execute(ctx)
        body = self.children[2]

        for elem in items:
            ctx.attrs[self._item_attr] = elem
            await body.execute(ctx)
