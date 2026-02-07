"""Iteration flows -- ForRange, ForEach, ForEachParallel."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from everybase import Flow
from everybase.abc import ensure_term


if TYPE_CHECKING:
    from everybase import Context, Executable, IntArg, Ref


__all__ = [
    "ForEach",
    "ForEachParallel",
    "ForRange",
]


class ForRange(Flow):
    """Counted loop over ``range(start, stop, step)``.

    Children layout: ``[start, stop, step, body]``

    Start, stop and step are auto-wrapped via ``ensure_term`` if literals are
    passed.  Optional ``index`` Ref is set with the current loop value
    at each iteration.

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
        super().__init__(
            ensure_term(start),
            ensure_term(stop),
            ensure_term(step),
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
                await self._index.set(i).execute(ctx)  # type: ignore[union-attr]
            await body.execute(ctx)


class ForEach(Flow):
    """Iterate over a sequence, executing body for each item.

    Children layout: ``[items, body]``

    The ``items`` parameter is auto-wrapped via ``ensure_term`` if a literal is
    passed -- it can be a plain list, a ``Ref.get()``, or any Term that
    resolves to an iterable.  Optional ``index`` Ref is set with the
    current iteration index.

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
        super().__init__(ensure_term(items), body)
        self._index = index

    async def execute(self, ctx: Context) -> None:
        """Execute body for each item in the resolved sequence."""
        items = await self.children[0].execute(ctx)
        body = self.children[1]

        for i, _item in enumerate(items):
            if self._index is not None:
                await self._index.set(i).execute(ctx)  # type: ignore[union-attr]
            await body.execute(ctx)


class ForEachParallel(Flow):
    """Parallel iteration over a sequence with concurrency limit.

    Children layout: ``[items, body]``

    The ``items`` parameter is auto-wrapped via ``ensure_term`` if a literal is
    passed.  Body is executed concurrently for each item, limited by a
    semaphore of size ``max_parallel``.

    The optional ``index`` Ref is set with the current iteration index.
    Note: concurrent writes to ``index`` are a known limitation -- the
    value is non-deterministic when multiple workers run simultaneously.

    Args:
        items: Iterable (or Term resolving to one) to iterate over.
        body: Executable run for each item.
        index: Optional Ref[int] set with current iteration index.
        max_parallel: Maximum number of concurrent workers. Default ``10``.

    Example::

        ForEachParallel(urls, fetch_url, max_parallel=5)
    """

    def __init__(
        self,
        items: Any,
        body: Executable,
        *,
        index: Ref[int] | None = None,
        max_parallel: int = 10,
    ) -> None:
        """Initialize parallel for-each loop.

        Args:
            items: Iterable or Term resolving to an iterable.
            body: Executable run for each item.
            index: Optional Ref[int] set with current iteration index.
            max_parallel: Maximum concurrent workers. Default ``10``.
        """
        super().__init__(ensure_term(items), body)
        self._index = index
        self._max_parallel = max_parallel

    async def execute(self, ctx: Context) -> None:
        """Execute body concurrently for each item with semaphore limit."""
        items = await self.children[0].execute(ctx)
        body = self.children[1]
        sem = asyncio.Semaphore(self._max_parallel)

        async def worker(idx: int) -> None:
            async with sem:
                if self._index is not None:
                    await self._index.set(idx).execute(ctx)  # type: ignore[union-attr]
                await body.execute(ctx)

        await asyncio.gather(*(worker(i) for i in range(len(items))))
