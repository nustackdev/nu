"""Primitive form nodes.

Each node is a Span over one body that mixes in its surface from
``nu.surfaces.primitives`` (``Str`` = ``StrSurface`` on a ``Form[str]``). The
methods live on the surface; the node adds only its constructor.
"""

from __future__ import annotations

from typing import Any

from nu.lang import NULL, Form, Null
from nu.surfaces.primitives import (
    BoolSurface,
    BytesSurface,
    FloatSurface,
    IntSurface,
    NoneSurface,
    NullSurface,
    ObjectSurface,
    StrSurface,
)


__all__ = [
    "Bool",
    "Bytes",
    "Float",
    "Int",
    "None_",
    "NullForm",
    "Object",
    "Str",
]


class Bool(BoolSurface, Form[bool]):
    """Boolean interface. Logical + comparable.

    Notes:
        - Logical operators are the named forms `and_`, `or_`, `not_`. Python
          reserves `and`, `or`, `not` as keywords, so they cannot be method
          names. `&`, `|` and `>>` compose flows (Race, Parallel,
          Sequential) on a Bool like on every term.
        - Short-circuits like Python: the right operand is only
          evaluated when the left does not already decide the result.
        - Comparison operators yield Bool too, treating False as less than
          True.

    Example:
        >>> nu.run(nu.Bool(True).and_(nu.Bool(False)))[0]
        False
    """


class Bytes(BytesSurface, Form[bytes]):
    """Bytes interface. Sliceable + comparable + logical + bytes methods.

    Notes:
        - Indexing with `[]` yields Int, the byte's value 0-255. Slicing
          with `[:]` yields Bytes.
        - `decode` and `hex_` are the only two methods that leave bytes:
          `decode` produces a Str, `hex_` produces a Str of hex digits.
          Every other method stays in Bytes.
        - Comparison operators yield Bool, ordering lexicographically by
          byte value, same as Python's `bytes` ordering.
        - Logical operators are the named forms `and_`, `or_`, `not_`.

    Example:
        >>> nu.run(nu.Bytes(b"hi") + nu.Bytes(b" there"))[0]
        b'hi there'
    """


class Float(FloatSurface, Form[float]):
    """Float interface. Numeric + comparable + logical.

    Notes:
        - Arithmetic against an Int, or a plain int or float, stays Float.
          There's no promotion to track since Float is already the wider
          type.
        - Division `/` and floor division `//` both stay Float. Unlike Int,
          where `/` promotes to Float but `//` stays Int, here every
          arithmetic operator returns Float.
        - Comparison operators yield Bool. Chained comparisons like
          `a > b > c` do not build a single term; write them as
          `And(a > b, b > c)`.
        - `nan` compares False against everything, including itself, so
          `Float(nan) == Float(nan)` is False.
        - Logical operators are the named forms `and_`, `or_`, `not_`.

    Example:
        >>> nu.run(nu.Float(2.5) * nu.Float(4.0))[0]
        10.0
    """


class Int(IntSurface, Form[int]):
    """Integer interface. Full numeric + comparable + logical + bitwise.

    Notes:
        - Arithmetic against a Float or a Python float promotes the result to
          Float. Everything else stays Int.
        - Division `/` always yields Float regardless of operand type; use
          `//` for integer floor division that stays Int.
        - Comparison operators yield Bool. Chained comparisons like
          `a > b > c` do not build a single term; write them as
          `And(a > b, b > c)`.
        - Logical operators are the named forms `and_`, `or_`, `not_`, and
          bit operations are named too: `bitand`, `bitor`, `bitxor`,
          `bitnot`, `lshift`, `rshift`. `&`, `|` and `>>` compose flows
          (Race, Parallel, Sequential) on an Int like on every term, and
          `^`, `~`, `<<` are not defined.

    Example:
        >>> nu.run(nu.Int(6) * nu.Int(7))[0]
        42
    """


class None_(NoneSurface, Form[None]):  # noqa: N801
    """None interface. Logical only.

    Notes:
        - Wraps Python's `None`. It's the typical return of an effect-only
          Command, one that runs for a side effect and yields nothing
          meaningful (`sleep`, `inc`, `dec`).
        - `==` / `!=` build an `Eq` / `Ne` term like every other Form, so
          `x == nu.None_()` asks whether x yields None at run time. There is
          no `is_`.
        - NULL is not None: NULL is an address that holds nothing, None is a
          stored value, and ``NULL == None`` is False.

    Example:
        >>> nu.run(nu.None_())[0] is None
        True
    """

    def __init__(self, source: object = None) -> None:
        """Wrap source as a None_ term.

        Args:
            source: the value to wrap. Defaults to `None`.

        Example:
            >>> nu.run(nu.None_())[0] is None
            True
        """
        super().__init__(source)


class NullForm(NullSurface, Form[Null]):
    """Wraps NULL, the value an absent read gives.

    Example:
        >>> nu.run(nu.NullForm())[0]
        <NULL>
    """

    def __init__(self) -> None:
        """Build the node wrapping NULL. Takes no arguments."""
        super().__init__(NULL)

    @classmethod
    def create(cls) -> NullForm:
        """A NULL term, so a branch can yield NULL like any other value.

        Yields:
            NULL. Writes refuse it, reads downstream see an absent value.

        Example:
            >>> nu.run(nu.If(False, nu.Int(1), nu.NullForm.create()))[0]
            <NULL>
        """
        return cls()


class Object(ObjectSurface, Form[Any]):
    """The interface every term has. Full operator surface, no promise about the runtime type.

    Arithmetic, bitwise, subscript, and attribute descent are all
    absorbing: the result of any of them is another Object, since the
    concrete type isn't known until evaluation. Comparison and logical
    operators are the exception - they still yield Bool, because "is
    this true" is a well-typed question even when the operand type
    isn't.

    Notes:
        - Typed as `Form[Any]`, not `Form[object]`. That lets an
          Object value slot into any narrow Arg position (IntArg, StrArg,
          ...), so `intref + objval` resolves through Int's `__add__`
          and lands as Int instead of falling through to Object's `__radd__`.
        - `&`, `|` and `>>` compose flows (Race, Parallel, Sequential)
          like on every term. Bit, set and merge operations are named
          methods (`bitand`, `union`, `merge`, ...).
        - There's no `__call__`. A callable value in a Nu tree goes
          through an interaction (built via `host` or hand-written),
          not raw Python call dispatch.

    Example:
        >>> nu.run(nu.Object(6) * nu.Object(7))[0]
        42
    """


class Str(StrSurface, Form[str]):
    """String interface. Addable + sliceable + comparable + logical + string methods.

    Notes:
        - `+` concatenates; there's no numeric arithmetic on Str.
        - Comparison operators compare lexicographically, Python str
          ordering, and yield Bool. Chained comparisons like `a > b > c`
          do not build a single term; write them as `And(a > b, b > c)`.
        - Logical operators are the named forms `and_`, `or_`, `not_`, and
          coerce by truthiness: the empty string is False, every other
          string is True.
        - Failures (a search that finds nothing with `index`/`rindex`, a
          wrong type, a multi-character `fillchar`, an unencodable
          character, a missing `format_map` key, an out-of-range index)
          raise, matching Python.

    Example:
        >>> nu.run(nu.Str("ab") + nu.Str("cd"))[0]
        'abcd'
    """
