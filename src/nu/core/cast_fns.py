"""Cast wrappers: coerce ``x`` into a Nu term of the target Form.

Lives in a separate module from ``cast`` because these functions shadow the
Python builtins (``str``, ``int``, ``list``, ...) and would collide with the
same names used as type annotations inside ``cast.py``.

``sorted`` and ``format`` sit here too: not casts, but the same kind of
builtin mirror, wrapping their query in the Form it yields.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core.cast import (
    ToDict,
    ToFloat,
    ToFrozenSet,
    ToInt,
    ToList,
    ToSet,
    ToStr,
    ToTuple,
)
from nu.core.repr import Format
from nu.core.transform import Sorted


if TYPE_CHECKING:
    from nu.forms.collections import Dict, FrozenSet, List, Set, Tuple
    from nu.forms.primitives import Float, Int, Str

__all__ = [
    "dict",
    "float",
    "format",
    "frozenset",
    "int",
    "list",
    "set",
    "sorted",
    "str",
    "tuple",
]


def str(x: object) -> Str:  # shadowing the builtin is intended
    """Coerce ``x`` to a Nu ``Str`` term. ``Str(ToStr(x))`` in one call."""
    from nu.forms.primitives import Str

    return Str(ToStr(x))


def int(x: object) -> Int:  # shadowing the builtin is intended
    """Coerce ``x`` to a Nu ``Int`` term. ``Int(ToInt(x))`` in one call."""
    from nu.forms.primitives import Int

    return Int(ToInt(x))


def float(x: object) -> Float:  # shadowing the builtin is intended
    """Coerce ``x`` to a Nu ``Float`` term. ``Float(ToFloat(x))`` in one call."""
    from nu.forms.primitives import Float

    return Float(ToFloat(x))


def list(x: object) -> List:  # shadowing the builtin is intended
    """Coerce ``x`` to a Nu ``List`` term. ``List(ToList(x))`` in one call.

    For building a list from positional Nu expressions, use ``nu.List.of(...)``.
    """
    from nu.forms.collections import List

    return List(ToList(x))


def tuple(x: object) -> Tuple:  # shadowing the builtin is intended
    """Coerce ``x`` to a Nu ``Tuple`` term. ``Tuple(ToTuple(x))`` in one call.

    For building a tuple from positional Nu expressions, use ``nu.Tuple.of(...)``.
    """
    from nu.forms.collections import Tuple

    return Tuple(ToTuple(x))


def set(x: object) -> Set:  # shadowing the builtin is intended
    """Coerce ``x`` to a Nu ``Set`` term. ``Set(ToSet(x))`` in one call.

    For building a set from positional Nu expressions, use ``nu.Set.of(...)``.
    """
    from nu.forms.collections import Set

    return Set(ToSet(x))


def frozenset(x: object) -> FrozenSet:  # shadowing the builtin is intended
    """Coerce ``x`` to a Nu ``FrozenSet`` term. ``FrozenSet(ToFrozenSet(x))`` in one call.

    For building a frozenset from positional Nu expressions, use
    ``nu.FrozenSet.of(...)``.
    """
    from nu.forms.collections import FrozenSet

    return FrozenSet(ToFrozenSet(x))


def dict(x: object) -> Dict:  # shadowing the builtin is intended
    """Coerce ``x`` to a Nu ``Dict`` term. ``Dict(ToDict(x))`` in one call.

    For building a dict from named Nu expressions, use ``nu.Dict.of(...)``.
    """
    from nu.forms.collections import Dict

    return Dict(ToDict(x))


def sorted(x: object) -> List:  # shadowing the builtin is intended
    """Sort ``x`` into a Nu ``List`` term. ``List(Sorted(x))`` in one call.

    Example:
        >>> nu.run(nu.sorted([3, 1, 2]).slice(0, 2))[0]
        [1, 2]
    """
    from nu.forms.collections import List

    return List(Sorted(x))


def format(value: object, spec: object = None) -> Str:  # shadowing the builtin is intended
    """Format ``value`` under ``spec`` into a Nu ``Str`` term. ``Str(Format(...))`` in one call.

    Args:
        value: the value to format.
        spec: the format spec, e.g. ``".2f"``. Left out, the empty spec
            applies, as with Python's ``format(value)``.

    Notes:
        - Always a string, so it reads as one: ``.upper()``, ``+`` and the
          rest of the ``Str`` surface take it as is.

    Example:
        >>> nu.run(nu.format(3.14159, ".2f") + "s")[0]
        '3.14s'
        >>> nu.run(nu.format(7))[0]
        '7'
    """
    from nu.forms.primitives import Str

    return Str(Format(value) if spec is None else Format(value, spec))
