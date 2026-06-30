"""functools module-level functions.

``reduce`` is the only ``functools`` member that maps to a Nu interaction (a
runtime value fold). The rest are out of the value model and intentionally
absent - see the package docstring.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import AnyForm
from nu.core import IterQuery
from nu.lang.sentinels import UNSET

from .interactions import ReduceQuery


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu.lang import Arg, Nu


__all__ = ["reduce"]


def reduce(function: Nu, iterable: Arg[Iterable], initializer: object = UNSET) -> AnyForm:
    """Fold ``iterable`` left-to-right with ``function`` (``functools.reduce``).

    ``function`` is a Nu query that reads the accumulator and the current item
    via a typed AttrRef - ``IntAttrRef("acc")`` and ``IntAttrRef("item")`` - so a
    sum is ``reduce(IntAttrRef("acc") + IntAttrRef("item"), xs)``. With
    ``initializer`` the accumulator starts there; otherwise at the first item.
    """
    # A Reduction requires a stream source; IterQuery lifts the iterable to one.
    if initializer is UNSET:
        return AnyForm(ReduceQuery(IterQuery(iterable), function))
    return AnyForm(ReduceQuery(IterQuery(iterable), function, initial=initializer))
