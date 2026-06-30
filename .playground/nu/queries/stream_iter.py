"""Iter - lift a scalar iterable into a stream.

Inverse of Reduction. Where Reduction (Find / First / Collect / Sum)
consumes a stream and produces a scalar, Iter consumes a scalar whose
value is iterable and yields its elements as a stream.

Use Iter to feed a python iterable into a stream-shaped consumer
(`Map`, `Filter`, `TakeWhile`, `Find`, ...) explicitly. The iteration
helpers auto-wrap scalar children, so the explicit form is mostly for
readability.

    Iter([1, 2, 3])             # yields 1, 2, 3
    Iter(range(10))             # yields 0..9
    Map(Iter(range(10)), transform=...)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.query import StreamQuery
from nu.terms.types import Mode


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator


__all__ = ["Iter"]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Iter(StreamQuery):
    """Yield each element of a scalar iterable child.

    Children: `[source]`. `source` is any ScalarQuery whose value is
    iterable (list, tuple, range, generator, dict, set, etc.).
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, source: Any) -> None:  # noqa: ANN401
        super().__init__(source)

    def open(self, ctx: Any) -> Generator[Any, None, None]:  # noqa: ANN401
        from nu import runtime

        value = runtime.first(self._children[0], ctx)
        yield from value

    async def aopen(self, ctx: Any) -> AsyncGenerator[Any, None]:  # noqa: ANN401
        from nu import runtime

        value = await runtime.afirst(self._children[0], ctx)
        for v in value:
            yield v
