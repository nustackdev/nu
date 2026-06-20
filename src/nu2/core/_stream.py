"""Shared stream-iteration helpers for the core atoms.

A stream atom's thunk returns an iterator. Sources build one, lenses (Map /
Filter) wrap one, folds (Sum / Collect) drain one. These helpers bridge the
two shapes a child thunk can hand back - a sync iterable or an async one - and
treat a sentinel (EMPTY / INVALID) as an empty stream, so every stream atom
iterates the same way.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

__all__ = ["aiter_any", "sync_iter"]


def sync_iter(value: object) -> Iterator:
    """Yield from a sync iterable; a sentinel value yields nothing."""
    if value is EMPTY or value is INVALID:
        return
    yield from value  # type: ignore[misc]


async def aiter_any(value: object) -> AsyncIterator:
    """Yield from a sync or async iterable; a sentinel value yields nothing.

    A stream child's async thunk may resolve to an async iterable (another
    stream atom) or a plain sync iterable (a scalar list). This normalizes
    both to one async walk.
    """
    if value is EMPTY or value is INVALID:
        return
    if hasattr(value, "__aiter__"):
        async for x in value:  # type: ignore[union-attr]
            yield x
    else:
        for x in value:  # type: ignore[union-attr]
            yield x
