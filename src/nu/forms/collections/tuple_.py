"""Tuple - tuple interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic

from typing_extensions import TypeVarTuple, Unpack

from nu.lang import TypedNu

from .abc import SequenceForm
from .abc.sequence_interactions import TupleCreate, TupleOf


if TYPE_CHECKING:
    from nu.lang import Arg, IntArg, Nu, TupleArg

    from ..primitives import Any, Bool
    from .list_ import List


__all__ = [
    "Tuple",
]


Ts = TypeVarTuple("Ts")


class Tuple(
    SequenceForm[tuple[Unpack[Ts]], object, "List[object]", "Any"],
    TypedNu[tuple[Unpack[Ts]]],
    Generic[Unpack[Ts]],
):
    """Tuple interface. Immutable sequence + comparable."""

    @classmethod
    def create(cls) -> Tuple[Unpack[Ts]]:
        """Yield an empty tuple."""
        return cls(TupleCreate())

    @classmethod
    def of(cls, *items: Arg) -> Tuple:
        """Yield a tuple from positional item expressions.

        ``Tuple.of(x, y, z)`` evaluates each argument in the current
        context and packs the results: ``(<x>, <y>, <z>)``. Sibling to
        ``Dict.of``. An item that resolves to a sentinel collapses the
        whole result to Invalid.
        """
        return cls(TupleOf(*items))

    def _wrap_sliceable_result(self, operand: Nu) -> Tuple:
        """Wrap operand as Tuple for slice results."""
        return Tuple(operand)

    def _wrap_iterable_result(self, operand: Nu) -> List:
        """Wrap operand as List."""
        from .list_ import List

        return List(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        """Wrap operand as Any element."""
        from ..primitives import Any

        return Any(operand)

    # =========================================================================
    # ARITHMETIC (concatenation / repeat): new value, no mutation
    # =========================================================================

    def __add__(self, other: TupleArg[Unpack[Ts]]) -> Tuple:
        """Concat: self + other -> new tuple (Query)."""
        from nu.core import Add

        return Tuple(Add(self, other))

    def __radd__(self, other: TupleArg[Unpack[Ts]]) -> Tuple:
        """Concat: other + self -> new tuple (Query)."""
        from nu.core import Add

        return Tuple(Add(other, self))

    def __mul__(self, n: IntArg) -> Tuple:
        """Repeat: self * n -> new tuple (Query)."""
        from nu.core import Mul

        return Tuple(Mul(self, n))

    def __rmul__(self, n: IntArg) -> Tuple:
        """Repeat: n * self -> new tuple (Query)."""
        from nu.core import Mul

        return Tuple(Mul(n, self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: TupleArg[Unpack[Ts]]) -> Bool:
        from nu.core import Gt

        from ..primitives import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: TupleArg[Unpack[Ts]]) -> Bool:
        from nu.core import Lt

        from ..primitives import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: TupleArg[Unpack[Ts]]) -> Bool:
        from nu.core import Ge

        from ..primitives import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: TupleArg[Unpack[Ts]]) -> Bool:
        from nu.core import Le

        from ..primitives import Bool

        return Bool(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: TupleArg[Unpack[Ts]]) -> Bool:  # type: ignore[override]
        from nu.core import Eq

        from ..primitives import Bool

        return Bool(Eq(self, other))

    def __ne__(self, other: TupleArg[Unpack[Ts]]) -> Bool:  # type: ignore[override]
        from nu.core import Ne

        from ..primitives import Bool

        return Bool(Ne(self, other))

    def is_(self, other: TupleArg[Unpack[Ts]]) -> Bool:
        """Identity comparison: self is other."""
        from nu.core import Is

        from ..primitives import Bool

        return Bool(Is(self, other))
