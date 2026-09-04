"""Comparison atoms: Python's ordering and identity operators.

Maps Python's comparison operators onto Nu ScalarQueries yielding a bool. Pure
compute over their operands; no Context effect of their own.

Operators to cover (Python -> Nu):
- ``==`` -> ``Eq``, ``!=`` -> ``Ne``
- ``<`` -> ``Lt``, ``>`` -> ``Gt``, ``<=`` -> ``Le``, ``>=`` -> ``Ge``
- ``is`` / ``is not`` -> ``Is`` (identity)

Sorts: all ScalarQuery (Q). Membership (``in``) lives in ``access`` as
``Contains``.

Each atom is binary and defines ``compile`` (sync hot path) and ``acompile``
(async hot path). Both return a thunk ``(rt) -> value`` (sync) or
``(rt) -> awaitable`` (async) that captures the precompiled child thunks, so
recursion skips the ``Runtime.eval`` / ``Runtime.aeval`` dispatch hop per
child. Sentinel propagation is inlined: an EMPTY or INVALID operand collapses
the result to INVALID without comparing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["Eq", "Ge", "Gt", "Is", "Le", "Lt", "Ne"]


class Eq(ScalarQuery):
    """Whether its two children are equal (``==``).

    Args:
        left: the first value.
        right: the second value.

    Notes:
        - Delegates to Python's ``==``, so equality is by value, not type:
          ``1 == 1.0`` is True regardless of int vs float.
        - The right child is evaluated only after the left yields a value, so
          a sentinel on the left short-circuits without touching the right.

    Yields:
        A bool. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Eq(1, 1.0))[0]
        True
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a == b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a == b

        return athunk


class Ne(ScalarQuery):
    """Whether its two children are unequal (``!=``).

    Args:
        left: the first value.
        right: the second value.

    Notes:
        - Delegates to Python's ``!=``, so it's the negation of ``Eq``: value
          comparison, not type comparison.
        - The right child is evaluated only after the left yields a value, so
          a sentinel on the left short-circuits without touching the right.

    Yields:
        A bool. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Ne(1, 2))[0]
        True
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a != b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a != b

        return athunk


class Lt(ScalarQuery):
    """Whether the first child is less than the second (``<``).

    Args:
        left: the value to check.
        right: the value to check it against.

    Notes:
        - Delegates to Python's ``<``. Operands that don't support ordering
          between their types raise, same as bare Python; only a sentinel
          operand collapses to INVALID.
        - The right child is evaluated only after the left yields a value, so
          a sentinel on the left short-circuits without touching the right.

    Yields:
        A bool. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Lt(1, 2))[0]
        True
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a < b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a < b

        return athunk


class Gt(ScalarQuery):
    """Whether the first child is greater than the second (``>``).

    Args:
        left: the value to check.
        right: the value to check it against.

    Notes:
        - Delegates to Python's ``>``. Operands that don't support ordering
          between their types raise, same as bare Python; only a sentinel
          operand collapses to INVALID.
        - The right child is evaluated only after the left yields a value, so
          a sentinel on the left short-circuits without touching the right.

    Yields:
        A bool. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Gt(3, 2))[0]
        True
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a > b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a > b

        return athunk


class Le(ScalarQuery):
    """Whether the first child is less than or equal to the second (``<=``).

    Args:
        left: the value to check.
        right: the value to check it against.

    Notes:
        - Delegates to Python's ``<=``. Operands that don't support ordering
          between their types raise, same as bare Python; only a sentinel
          operand collapses to INVALID.
        - The right child is evaluated only after the left yields a value, so
          a sentinel on the left short-circuits without touching the right.

    Yields:
        A bool. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Le(2, 2))[0]
        True
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a <= b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a <= b

        return athunk


class Ge(ScalarQuery):
    """Whether the first child is greater than or equal to the second (``>=``).

    Args:
        left: the value to check.
        right: the value to check it against.

    Notes:
        - Delegates to Python's ``>=``. Operands that don't support ordering
          between their types raise, same as bare Python; only a sentinel
          operand collapses to INVALID.
        - The right child is evaluated only after the left yields a value, so
          a sentinel on the left short-circuits without touching the right.

    Yields:
        A bool. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Ge(2, 2))[0]
        True
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a >= b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a >= b

        return athunk


class Is(ScalarQuery):
    """Whether its two children are the same object (``is``).

    Args:
        left: the first value.
        right: the second value.

    Notes:
        - Delegates to Python's ``is``: object identity, not value equality.
          Two distinct objects that compare equal (e.g. two separate lists
          with the same contents) are not the same object.
        - The right child is evaluated only after the left yields a value, so
          a sentinel on the left short-circuits without touching the right.

    Yields:
        A bool. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> x = object()
        >>> nu.run(nu.Is(x, x))[0]
        True
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a is b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a is b

        return athunk
