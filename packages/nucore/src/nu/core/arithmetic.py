"""Arithmetic atoms: Python's numeric builtins and operators.

Maps Python's native numeric functions and arithmetic operators onto Nu
ScalarQueries. None touch the Context on their own - effects only ride in
through Ref children.

Builtins / operators to cover (Python -> Nu):
- ``+`` -> ``Add``, ``-`` -> ``Sub``, ``*`` -> ``Mul``, ``/`` -> ``Div``
- ``@`` -> ``MatMul``
- ``//`` -> ``FloorDiv``, ``%`` -> ``Mod``, ``**`` / ``pow`` -> ``Pow``
- unary ``-`` -> ``Neg``, unary ``+`` -> ``Pos``, ``abs`` -> ``Abs``
- ``divmod`` -> ``DivMod``, ``round`` -> ``Round``

Sorts: all ScalarQuery (Q). ``Add`` and ``Mul`` fold a variadic child list.
``Sub``, ``Div``, ``FloorDiv``, ``Mod``, ``Pow`` and ``DivMod`` are binary.
``Neg``, ``Pos`` and ``Abs`` are unary. ``Round`` takes one child (value) or
two (value, ndigits). ``DivMod`` yields the ``(quotient, remainder)`` pair as
its single scalar.

Each atom defines ``compile`` (sync hot path) and ``acompile`` (async hot
path). Both return a thunk ``(rt) -> value`` (sync) or ``(rt) -> awaitable``
(async) that captures the precompiled child thunks, so recursion skips the
``Runtime.eval`` / ``Runtime.aeval`` dispatch hop per child. Sentinel
propagation is inlined: an EMPTY or INVALID operand collapses the result to
INVALID without further folding.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = [
    "Abs",
    "Add",
    "Div",
    "DivMod",
    "FloorDiv",
    "MatMul",
    "Mod",
    "Mul",
    "Neg",
    "Pos",
    "Pow",
    "Round",
    "Sub",
]


class Add(ScalarQuery):
    """The sum of its scalar children.

    Args:
        *children: the values to add, folded left to right.

    Notes:
        - Folds from the first child rather than from zero, so any type
          supporting ``+`` works, including string, list and tuple concatenation.
        - No children at all yields 0, the additive identity.
        - Children are evaluated in order and the fold stops at the first
          sentinel it meets.

    Yields:
        The sum. INVALID when any child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Add(1, 2, 3))[0]
        6
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            s: object = 0  # additive identity for the no-children case
            for i, ct in enumerate(children):
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                # Fold from the first operand so `+` works for any type that
                # supports it (str / list / tuple concat), not only numbers.
                s = v if i == 0 else s + v
            return s

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            s: object = 0  # additive identity for the no-children case
            for i, ct in enumerate(children):
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                s = v if i == 0 else s + v
            return s

        return athunk


class Mul(ScalarQuery):
    """The product of its scalar children.

    Args:
        *children: the values to multiply.

    Notes:
        - Starts from 1, the multiplicative identity, so no children at all
          yields 1.
        - Children are evaluated in order and the fold stops at the first
          sentinel it meets.

    Yields:
        The product. INVALID when any child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Mul(2, 3, 4))[0]
        24
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            out: object = 1
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out * v
            return out

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            out: object = 1
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out * v
            return out

        return athunk


class MatMul(ScalarQuery):
    """The matrix product of its two children.

    Args:
        left: the left operand.
        right: the right operand.

    Notes:
        - Delegates entirely to the operands' own ``__matmul__``, so what a
          matrix product means is theirs to decide. Nu adds no numeric
          behaviour of its own here.
        - Nothing in the standard library defines ``@``, so in practice the
          operands come from a numeric library.
        - The right child is evaluated only after the left yields a value, so
          a sentinel on the left short-circuits without touching the right.

    Yields:
        The product. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> class Grid:
        ...     def __matmul__(self, other):
        ...         return "product"
        >>> nu.run(nu.MatMul(Grid(), Grid()))[0]
        'product'
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
            return a @ b

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
            return a @ b

        return athunk


class Sub(ScalarQuery):
    """The first child minus the second.

    Args:
        left: the value to subtract from.
        right: the value to subtract.

    Notes:
        - The right child is evaluated only after the left yields a value, so
          a sentinel on the left short-circuits without touching the right.

    Yields:
        The difference. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Sub(10, 3))[0]
        7
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
            return a - b

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
            return a - b

        return athunk


class Div(ScalarQuery):
    """The first child divided by the second (true division).

    Args:
        left: the numerator.
        right: the denominator.

    Notes:
        - True division, so two ints yield a float.
        - A zero denominator raises. Only sentinels collapse to INVALID; a
          real error stays a real error.

    Yields:
        The quotient. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Div(7, 2))[0]
        3.5
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
            return a / b

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
            return a / b

        return athunk


class FloorDiv(ScalarQuery):
    """The first child floor-divided by the second.

    Args:
        left: the numerator.
        right: the denominator.

    Notes:
        - Floors toward negative infinity, as Python's ``//`` does, so
          -7 floor-divided by 2 is -4 and not -3.

    Yields:
        The floored quotient. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.FloorDiv(7, 2))[0]
        3
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
            return a // b

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
            return a // b

        return athunk


class Mod(ScalarQuery):
    """The first child modulo the second.

    Args:
        left: the value to divide.
        right: the divisor.

    Notes:
        - The result takes the sign of the divisor, as Python's ``%`` does,
          so -7 modulo 3 is 2 and not -1.

    Yields:
        The remainder. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Mod(7, 2))[0]
        1
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
            return a % b

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
            return a % b

        return athunk


class Pow(ScalarQuery):
    """The first child raised to the power of the second.

    Args:
        base: the value to raise.
        exponent: the power to raise it to.

    Notes:
        - A negative exponent yields a float, as Python's ``**`` does.

    Yields:
        The power. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Pow(2, 10))[0]
        1024
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
            return a**b

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
            return a**b

        return athunk


class Neg(ScalarQuery):
    """The arithmetic negation of its one child.

    Args:
        value: the value to negate.

    Yields:
        The negation. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Neg(4))[0]
        -4
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return -v

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return -v

        return athunk


class Pos(ScalarQuery):
    """The unary plus of its one child.

    Args:
        value: the value to apply unary plus to.

    Notes:
        - Identity for numbers, but a real operation nonetheless: a type
          defining ``__pos__`` decides what it means.

    Yields:
        The value. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Pos(-4))[0]
        -4
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return +v

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return +v

        return athunk


class Abs(ScalarQuery):
    """The absolute value of its one child.

    Args:
        value: the value to take the magnitude of.

    Yields:
        The absolute value. INVALID when the child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Abs(-4))[0]
        4
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return abs(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return abs(v)

        return athunk


class DivMod(ScalarQuery):
    """The ``(quotient, remainder)`` pair of its two children.

    Args:
        left: the value to divide.
        right: the divisor.

    Notes:
        - One scalar that happens to be a pair, not two values, so indexing
          it is how either half is reached.

    Yields:
        The pair. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.DivMod(7, 2))[0]
        (3, 1)
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
            return divmod(a, b)

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
            return divmod(a, b)

        return athunk


class Round(ScalarQuery):
    """The first child rounded, to the second child's digits when given.

    Args:
        value: the value to round.
        ndigits: how many digits to keep. Optional: leave the child out
            entirely to round to a whole number.

    Notes:
        - Rounds half to even, as Python's ``round`` does, so 2.5 rounds to 2
          and 3.5 rounds to 4.
        - Without an ndigits child the result is an int. With one it keeps
          the value's own type.

    Yields:
        The rounded value. INVALID when either child is EMPTY or INVALID.

    Example:
        >>> nu.run(nu.Round(3.14159, 2))[0]
        3.14
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        if len(children) == 1:
            (only,) = children

            def thunk_value(rt: Runtime) -> object:
                v = only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return round(v)

            return thunk_value

        value, ndigits = children

        def thunk(rt: Runtime) -> object:
            v = value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            n = ndigits(rt)
            if n is EMPTY or n is INVALID:
                return INVALID
            return round(v, n)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        if len(children) == 1:
            (only,) = children

            async def athunk_value(rt: Runtime) -> object:
                v = await only(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                return round(v)

            return athunk_value

        value, ndigits = children

        async def athunk(rt: Runtime) -> object:
            v = await value(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            n = await ndigits(rt)
            if n is EMPTY or n is INVALID:
                return INVALID
            return round(v, n)

        return athunk
