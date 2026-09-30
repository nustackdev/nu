"""The kv leaf for a Fraction: kept as its ``n/d`` str, so the ratio stays exact.

The leaf pairs the ``nustd.fractions`` value form with the kv leaf and
translates at the boundary: ``set`` lowers the value, a read lifts it back, so
the ref is an operand of the real value throughout. The leaf lives with
its library, not in ``nustd.kv``: a container declared with the Python type
holds untyped ``ObjectRef`` children, and a container declared with the leaf
class holds this one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core import ToStr
from nu.domains.shape import SetCmd
from nu.lang import Nu
from nustd.fractions.forms import Fraction as FractionForm
from nustd.kv.refs import ItemRef


if TYPE_CHECKING:
    from fractions import Fraction

    from nu.lang import Arg


__all__ = ["FractionRef"]


class FractionRef(ItemRef, FractionForm):
    """A Fraction leaf in KV storage, stored as its ``numerator/denominator`` str.

    Notes:
        - Stored as str, so the ratio survives exactly instead of being
          flattened to a float.
        - Reads parse back to a Fraction, already in lowest terms because
          that is what Fraction does with the str.
        - An absent leaf reads as EMPTY.

    Example:
        class Split(Shape):
            share = FractionRef.slot()
        run(Split.share.set(Fraction(1, 3)), ctx)
    """

    def _lift(self, raw: object) -> Fraction:
        """Parse the stored str back to a Fraction."""
        from fractions import Fraction as FractionCls

        return raw if isinstance(raw, FractionCls) else FractionCls(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[Fraction | str]) -> SetCmd:
        """Write a Fraction to the leaf, serialized to its str form.

        Args:
            value: a Fraction, a str spelling one, or an expression yielding
                either.

        Notes:
            - A plain value is stringified before the write; an expression
              is wrapped in a ToStr so the conversion happens at run time.

        Example:
            run(Split.share.set(Fraction(1, 3)), ctx)
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)
