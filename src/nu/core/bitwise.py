"""Bitwise atoms: Python's bit-level operators.

Maps Python's bitwise operators onto Nu ScalarQueries over integers. Pure
compute; no Context effect of their own.

Operators to cover (Python -> Nu):
- ``&`` -> ``BitAnd``, ``|`` -> ``BitOr``, ``^`` -> ``BitXor``
- ``~`` -> ``BitNot`` (unary)
- ``<<`` -> ``LShift``, ``>>`` -> ``RShift``

Sorts: all ScalarQuery (Q). ``BitAnd`` / ``BitOr`` / ``BitXor`` fold over
their children from the first one with Python's operator (with no children
they yield the int identity, ``-1`` for AND, ``0`` for OR / XOR); the shifts are
binary and ``BitNot`` is unary. Each atom defines ``compile`` (sync hot path)
and ``acompile`` (async hot path), both returning a thunk that captures the
precompiled child thunks. Sentinel propagation is inlined: an EMPTY or INVALID
operand collapses the result to INVALID.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["BitAnd", "BitNot", "BitOr", "BitXor", "LShift", "RShift"]


_START = object()
"""Fold marker: no child folded yet, so the first value starts the fold."""


class BitAnd(ScalarQuery):
    """The bitwise AND of its scalar children.

    Args:
        *children: the integers to AND together, folded left to right.

    Notes:
        - Folds from the first child with Python's `&`, so it keeps the
          operands' own meaning (bools stay bool, sets intersect). No
          children at all yields -1, the int AND identity.
        - Operands are Python ints, two's-complement under the hood, so a
          negative operand ANDs its infinite leading 1s in.
        - Children are evaluated in order and the fold stops at the first
          sentinel it meets.

    Yields:
        The AND. INVALID when any child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.BitAnd(12, 10))[0]
        8
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            out: object = _START
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = v if out is _START else out & v
            return -1 if out is _START else out

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            out: object = _START
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = v if out is _START else out & v
            return -1 if out is _START else out

        return athunk


class BitOr(ScalarQuery):
    """The bitwise OR of its scalar children.

    Args:
        *children: the integers to OR together, folded left to right.

    Notes:
        - Folds from the first child with Python's `|`, so it keeps the
          operands' own meaning (bools stay bool, sets union, dicts merge).
          No children at all yields 0, the int OR identity.
        - Operands are Python ints, two's-complement under the hood, so a
          negative operand carries its infinite leading 1s through.
        - Children are evaluated in order and the fold stops at the first
          sentinel it meets.

    Yields:
        The OR. INVALID when any child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.BitOr(12, 10))[0]
        14
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            out: object = _START
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = v if out is _START else out | v
            return 0 if out is _START else out

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            out: object = _START
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = v if out is _START else out | v
            return 0 if out is _START else out

        return athunk


class BitXor(ScalarQuery):
    """The bitwise XOR of its scalar children.

    Args:
        *children: the integers to XOR together, folded left to right.

    Notes:
        - Folds from the first child with Python's `^`, so it keeps the
          operands' own meaning (bools stay bool, sets take the symmetric
          difference). No children at all yields 0, the int XOR identity.
        - Operands are Python ints, two's-complement under the hood, so a
          negative operand flips its infinite leading 1s in the fold.
        - Children are evaluated in order and the fold stops at the first
          sentinel it meets.

    Yields:
        The XOR. INVALID when any child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.BitXor(12, 10))[0]
        6
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            out: object = _START
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = v if out is _START else out ^ v
            return 0 if out is _START else out

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            out: object = _START
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = v if out is _START else out ^ v
            return 0 if out is _START else out

        return athunk


class BitNot(ScalarQuery):
    """The bitwise NOT of its one child.

    Args:
        value: the integer to invert.

    Notes:
        - Python ints have no fixed width, so NOT is the identity ``~x ==
          -x - 1``: flipping every bit of a two's-complement number just
          negates it and subtracts one.

    Yields:
        The inverted value. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.BitNot(5))[0]
        -6
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return ~v

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return ~v

        return athunk


class LShift(ScalarQuery):
    """The first child shifted left by the second.

    Args:
        value: the integer to shift.
        count: how many bits to shift by.

    Notes:
        - Equivalent to multiplying by ``2 ** count``; sign is preserved
          since Python ints have no fixed width to overflow out of.
        - A negative count raises. Only sentinels collapse to INVALID; a
          real error stays a real error.
        - The count child is evaluated only after the value yields, so a
          sentinel on the value short-circuits without touching the count.

    Yields:
        The shifted value. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.LShift(1, 4))[0]
        16
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
            return a << b

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
            return a << b

        return athunk


class RShift(ScalarQuery):
    """The first child shifted right by the second.

    Args:
        value: the integer to shift.
        count: how many bits to shift by.

    Notes:
        - Arithmetic shift: floor division by ``2 ** count``, sign extended,
          as Python's ``>>`` does. -16 shifted right by 2 is -4, not -3.
        - A negative count raises. Only sentinels collapse to INVALID; a
          real error stays a real error.
        - The count child is evaluated only after the value yields, so a
          sentinel on the value short-circuits without touching the count.

    Yields:
        The shifted value. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.RShift(-16, 2))[0]
        -4
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
            return a >> b

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
            return a >> b

        return athunk
