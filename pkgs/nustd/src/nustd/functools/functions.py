"""functools module-level functions.

``reduce`` is the only ``functools`` member that maps to a Nu interaction (a
runtime value fold). The rest are out of the value model and intentionally
absent - see the package docstring.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core import Iter
from nu.forms import Object
from nu.lang.sentinels import UNSET

from .interactions import Reduce


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from nu.context import Attr
    from nu.lang import Arg, Nu


__all__ = ["reduce"]


def reduce(
    function: Nu | Callable[[Attr, Attr], Nu],
    iterable: Arg[Iterable],
    initializer: object = UNSET,
) -> Object:
    """Fold ``iterable`` left-to-right with ``function`` (``functools.reduce``).

    ``function`` is a lambda over the accumulator and the current item,
    called once at construction with refs to them, so it builds the step and
    never computes with them in Python. Given as a tree instead, it reads them
    via ``nu.Attr("acc")`` and ``nu.Attr("item")``. With ``initializer`` the
    accumulator starts there; otherwise at the first item.

    Example:
        >>> nu.run(nustd.functools.reduce(lambda acc, x: nu.Int(acc) * 10 + x, [1, 2, 3]))[0]
        123

        The same as a tree:

        >>> nu.run(nustd.functools.reduce(nu.Int(nu.Attr("acc")) * 10 + nu.Attr("item"), [1, 2, 3]))[0]
        123
    """
    # A Reduction requires a stream source; Iter lifts the iterable to one.
    if initializer is UNSET:
        return Object(Reduce(Iter(iterable), function))
    return Object(Reduce(Iter(iterable), function, initial=initializer))
