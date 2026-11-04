"""Reduction atoms: Python's stream-to-scalar builtins.

Maps Python's builtins that fold an iterable down to one value onto Nu
Reductions (a ScalarQuery with a stream child - they bridge the REFUSED cell of
the cardinality matrix by naming the fold). Pure compute over the source.

Builtins covered (Python -> Nu):

- ``sum`` -> ``Sum``, ``min`` -> ``Min``, ``max`` -> ``Max``
- ``any`` -> ``AnyOf``, ``all`` -> ``AllOf``
- ``len`` over a stream -> ``Count``

Plus the structural folds Python reaches for without a single builtin name -
``First`` / ``Last`` / ``Collect`` - the native ways to take the head, the tail,
or the whole drain of a stream.

``functools.reduce`` is stdlib, not a bare builtin, so a generic ``Reduce`` is
core-adjacent (borderline). It is deferred to ``nustd``, not declared here:
core stays the 1:1 map of native builtins.

Every atom is EVALUABLE: each ``Reduction`` defines ``compile`` (sync) and
``acompile`` (async) returning a thunk that drains its stream child to a scalar,
with no NULL handling of its own.

Sorts: all ScalarQuery / Reduction (Q-scalar over Q-stream).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Reduction
from nu.lang.sentinels import UNSET

from ._stream import aiter_any, sync_iter


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = [
    "AllOf",
    "AnyOf",
    "Collect",
    "Count",
    "First",
    "Last",
    "Max",
    "Min",
    "Sum",
]


class Sum(Reduction):
    """The sum of every item in its stream child (``sum``).

    Args:
        stream: the stream to fold.

    Notes:
        - Folds from 0, the additive identity, so an empty stream yields 0.

    Yields:
        The sum.

    Example:
        >>> nu.run(nu.Sum(nu.Iter([1, 2, 3])))[0]
        6
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            total: object = 0
            for v in sync_iter(stream(rt)):
                total = total + v
            return total

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            total: object = 0
            async for v in aiter_any(await stream(rt)):
                total = total + v
            return total

        return athunk


class Min(Reduction):
    """The smallest item in its stream child (``min``).

    Args:
        stream: the stream to fold.

    Notes:
        - Buffers every item before comparing, since finding a minimum
          needs the whole set; nothing shortcuts.
        - An empty stream raises ValueError, like Python's ``min``.

    Yields:
        The smallest item.

    Example:
        >>> nu.run(nu.Min(nu.Iter([3, 1, 2])))[0]
        1
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            items = []
            for v in sync_iter(stream(rt)):
                items.append(v)
            return min(items)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            items = []
            async for v in aiter_any(await stream(rt)):
                items.append(v)
            return min(items)

        return athunk


class Max(Reduction):
    """The largest item in its stream child (``max``).

    Args:
        stream: the stream to fold.

    Notes:
        - Buffers every item before comparing, since finding a maximum
          needs the whole set; nothing shortcuts.
        - An empty stream raises ValueError, like Python's ``max``.

    Yields:
        The largest item.

    Example:
        >>> nu.run(nu.Max(nu.Iter([3, 1, 2])))[0]
        3
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            items = []
            for v in sync_iter(stream(rt)):
                items.append(v)
            return max(items)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            items = []
            async for v in aiter_any(await stream(rt)):
                items.append(v)
            return max(items)

        return athunk


class AnyOf(Reduction):
    """True if any item in its stream child is truthy (``any``).

    Args:
        stream: the stream to fold.

    Notes:
        - Short-circuits on the first truthy item; the rest of the stream
          is never drained.
        - An empty stream yields False, Python's ``any`` rule for no items.

    Yields:
        True or False.

    Example:
        >>> nu.run(nu.AnyOf(nu.Iter([0, 0, 1])))[0]
        True
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            for v in sync_iter(stream(rt)):
                if v:
                    return True
            return False

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            async for v in aiter_any(await stream(rt)):
                if v:
                    return True
            return False

        return athunk


class AllOf(Reduction):
    """True if every item in its stream child is truthy (``all``).

    Args:
        stream: the stream to fold.

    Notes:
        - Short-circuits on the first falsy item; the rest of the stream
          is never drained.
        - An empty stream yields True, Python's ``all`` rule for no items.

    Yields:
        True or False.

    Example:
        >>> nu.run(nu.AllOf(nu.Iter([1, 1, 1])))[0]
        True
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            for v in sync_iter(stream(rt)):
                if not v:
                    return False
            return True

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            async for v in aiter_any(await stream(rt)):
                if not v:
                    return False
            return True

        return athunk


class Count(Reduction):
    """The number of items in its stream child (``len`` over a stream).

    Args:
        stream: the stream to fold.

    Notes:
        - Drains the whole stream to count it; there is no shortcut.

    Yields:
        The count. 0 for an empty stream.

    Example:
        >>> nu.run(nu.Count(nu.Iter([1, 2, 3])))[0]
        3
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            n = 0
            for _ in sync_iter(stream(rt)):
                n += 1
            return n

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            n = 0
            async for _ in aiter_any(await stream(rt)):
                n += 1
            return n

        return athunk


class First(Reduction):
    """The first item of its stream child.

    Args:
        stream: the stream to fold.
        default: yielded when the stream is empty. Optional: leave it out to
            raise ValueError instead, like ``next()`` without a default.

    Notes:
        - Pulls exactly one item and stops; the rest of the stream is
          never touched.
        - ``default`` is evaluated only when the stream is empty.

    Yields:
        The first item, or ``default`` for an empty stream.

    Example:
        >>> nu.run(nu.First(nu.Iter([1, 2, 3])))[0]
        1
    """

    def __init__(self, stream: object, default: object = UNSET) -> None:
        if default is UNSET:
            super().__init__(stream)
        else:
            super().__init__(stream, default)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        stream = children[0]
        default = children[1] if len(children) > 1 else None

        def thunk(rt: Runtime) -> object:
            for v in sync_iter(stream(rt)):
                return v
            if default is None:
                raise ValueError("First() of an empty stream")
            return default(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        stream = children[0]
        default = children[1] if len(children) > 1 else None

        async def athunk(rt: Runtime) -> object:
            async for v in aiter_any(await stream(rt)):
                return v
            if default is None:
                raise ValueError("First() of an empty stream")
            return await default(rt)

        return athunk


class Last(Reduction):
    """The last item of its stream child.

    Args:
        stream: the stream to fold.
        default: yielded when the stream is empty. Optional: leave it out to
            raise ValueError instead.

    Notes:
        - Drains the whole stream to find the last item; there is no
          shortcut from the tail.

    Yields:
        The last item, or ``default`` for an empty stream.

    Example:
        >>> nu.run(nu.Last(nu.Iter([1, 2, 3])))[0]
        3
    """

    def __init__(self, stream: object, default: object = UNSET) -> None:
        if default is UNSET:
            super().__init__(stream)
        else:
            super().__init__(stream, default)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        stream = children[0]
        default = children[1] if len(children) > 1 else None

        def thunk(rt: Runtime) -> object:
            last: object = UNSET
            for v in sync_iter(stream(rt)):
                last = v
            if last is not UNSET:
                return last
            if default is None:
                raise ValueError("Last() of an empty stream")
            return default(rt)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        stream = children[0]
        default = children[1] if len(children) > 1 else None

        async def athunk(rt: Runtime) -> object:
            last: object = UNSET
            async for v in aiter_any(await stream(rt)):
                last = v
            if last is not UNSET:
                return last
            if default is None:
                raise ValueError("Last() of an empty stream")
            return await default(rt)

        return athunk


class Collect(Reduction):
    """Drains its stream child into one list value.

    Args:
        stream: the stream to fold.

    Notes:
        - The one reduction with no single Python builtin behind it; it
          names the structural "materialize the stream" fold.

    Yields:
        A list of every item, in order. Empty list for an empty stream.

    Example:
        >>> nu.run(nu.Collect(nu.Iter([1, 2, 3])))[0]
        [1, 2, 3]
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            out: list = []
            for v in sync_iter(stream(rt)):
                out.append(v)
            return out

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            out: list = []
            async for v in aiter_any(await stream(rt)):
                out.append(v)
            return out

        return athunk
