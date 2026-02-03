"""Iteration flows.

This module provides flows for iterating over data:
- ForRange: Iterate over a numeric range
- ForEach: Iterate sequentially over a collection
- ForEachParallel: Iterate in parallel over a collection
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import attrs

from everybase import Flow, Runtime, Term


if TYPE_CHECKING:
    from collections.abc import Sequence as PySequence

    from everybase.abc import SequenceRef


__all__ = [
    "ForEach",
    "ForEachParallel",
    "ForRange",
]


@attrs.define
class _ForRange[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute child for each value in a numeric range.

    Iterates from start to stop (exclusive) by step, executing
    the child flow for each value.

    Flow Building Pattern:
        The current index is available via runtime.attributes as "index".
        This is useful for simple counted loops without needing a collection.

    Example:
            ForRange(0, 10, ProcessIndex())  # 0, 1, 2, ..., 9
            ForRange(0, 10, step=2, child=ProcessIndex())  # 0, 2, 4, 6, 8
    """

    start: Term | int = attrs.field(default=0)
    stop: Term | int = attrs.field(default=0)
    step: Term | int = attrs.field(default=1)
    child: Flow | Term | None = attrs.field(default=None)
    name: str | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child for each value in range."""
        if not self.child:
            raise ValueError("No child is provided")

        # Resolve values
        start = self._resolve_int(runtime, self.start)
        stop = self._resolve_int(runtime, self.stop)
        step = self._resolve_int(runtime, self.step)

        if step == 0:
            raise ValueError("Step cannot be zero")

        for i in range(start, stop, step):
            runtime.cancellation.terminate_cancelled(runtime.path)

            child_runtime = runtime.child(i)

            # Set attributes for child
            child_runtime.attributes.set(
                child_runtime.path,
                "index",
                i,
                step_name=self.name,
            )

            await self.execute_child(self.child, i, child_runtime)

    def _resolve_int(self, runtime: RuntimeT, value: Term | int) -> int:
        """Resolve Term or int to int."""
        if isinstance(value, Term):
            result = runtime.terms.execute_term(value)
            if not isinstance(result, int):
                raise ValueError(f"Expected int, got {type(result)}")
            return result
        return value


# =============================================================================
# Wrapper Functions
# =============================================================================


def ForRange(  # noqa: N802
    start: Term | int,
    stop: Term | int,
    child: Flow | Term,
    step: Term | int = 1,
) -> _ForRange:
    """Execute child for each value in a numeric range.

    Current index available via runtime.attributes as "index".

    Args:
        start: Starting value (inclusive)
        stop: Stopping value (exclusive)
        child: Child flow to execute for each value
        step: Step size (default: 1)

    Returns:
        ForRange flow

    Example:
        >>> ForRange(0, 10, ProcessIndex())  # 0 through 9
        >>> ForRange(0, 10, ProcessIndex(), step=2)  # 0, 2, 4, 6, 8
    """
    return _ForRange(start=start, stop=stop, step=step, child=child)


@attrs.define
class _ForEach[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute child sequentially for each item in a sequence.

    Sets runtime.attributes["index"] for each iteration.
    Child flows can read these to know which item they're processing.

    Args:
        seq_ref: Sequence of items to iterate over
        child: Flow to execute for each item
        index_attr: Attribute name for current index (default: "index")
    """

    seq_ref: SequenceRef | PySequence | None = attrs.field()
    child: Flow | Term = attrs.field()
    index_attr: str = attrs.field(default="index")
    name: str | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        if self.seq_ref is None:
            raise ValueError("seq_ref is not set")

        if isinstance(self.seq_ref, Term):
            length = runtime.terms.execute_term(self.seq_ref.length())
        else:
            length = len(self.seq_ref)
        if not isinstance(length, int) or length == 0:
            return

        for i in range(length):
            runtime.cancellation.terminate_cancelled(runtime.path)

            child_runtime = runtime.child(i)

            # Set attributes for child
            child_runtime.attributes.set(
                child_runtime.path,
                self.index_attr,
                i,
                step_name=self.name,
            )

            await self.execute_child(self.child, i, child_runtime)


def ForEach(  # noqa: N802
    seq_ref: SequenceRef | PySequence | None,
    child: Flow | Term,
    index_attr: str = "index",
    name: str | None = None,
) -> _ForEach:
    """Execute child sequentially for each item in a sequence.

    Sets runtime.attributes["index"] for each iteration.
    Child flows can read these to know which item they're processing.

    Args:
        seq_ref: Sequence of items to iterate over
        child: Child flow to execute for each item
        index_attr: Attribute name for current index (default: "index")
        name: Additional attribute name for attrs dict

    Returns:
        ForEach flow
    """
    return _ForEach(
        seq_ref=seq_ref,
        child=child,
        index_attr=index_attr,
        name=name,
    )


@attrs.define
class _ForEachParallel[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute child in parallel for each item in a sequence.

    Sets runtime.attributes["index"] for each iteration.
    Child flows can read these to know which item they're processing.

    Args:
        items_ref: Sequence of items to iterate over
        child: Flow to execute for each item
        index_attr: Attribute name for current index (default: "index")
        max_parallel: Maximum number of concurrent executions (default: 10)
    """

    seq_ref: SequenceRef | PySequence | None = attrs.field()
    child: Flow | Term = attrs.field()
    index_attr: str = attrs.field(default="index")
    name: str | None = attrs.field(default=None)
    max_parallel: int = attrs.field(default=10)

    async def run(self, runtime: RuntimeT) -> None:
        if self.seq_ref is None:
            raise ValueError("seq_ref is not set")

        if isinstance(self.seq_ref, Term):
            length = runtime.terms.execute_term(self.seq_ref.length())
        else:
            length = len(self.seq_ref)
        if not isinstance(length, int) or length == 0:
            return

        semaphore = asyncio.Semaphore(self.max_parallel)

        async def process_item(i: int) -> None:
            async with semaphore:
                child_runtime = runtime.child(i)

                # Set attributes for child
                child_runtime.attributes.set(
                    child_runtime.path,
                    self.index_attr,
                    i,
                    step_name=self.name,
                )

                await self.execute_child(self.child, i, child_runtime)

        # Execute all in parallel (limited by semaphore)
        tasks = [process_item(i) for i in range(length)]
        await asyncio.gather(*tasks, return_exceptions=True)


def ForEachParallel(  # noqa: N802
    seq_ref: SequenceRef | PySequence | None,
    child: Flow | Term,
    index_attr: str = "index",
    name: str | None = None,
    max_parallel: int = 10,
) -> _ForEachParallel:
    """Execute child in parallel for each item in a sequence.

    Sets runtime.attributes["index"] for each iteration.
    Child flows can read these to know which item they're processing.

    Args:
        seq_ref: Sequence of items to iterate over
        child: Flow to execute for each item
        index_attr: Attribute name for current index (default: "index")
        name: Additional attribute name for attrs dict
        max_parallel: Maximum number of concurrent executions (default: 10)
    """
    return _ForEachParallel(
        seq_ref=seq_ref,
        child=child,
        index_attr=index_attr,
        name=name,
        max_parallel=max_parallel,
    )
