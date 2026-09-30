"""The mem leaf for a Fraction: kept as its ``n/d`` str, so the ratio stays exact.

The leaf pairs the ``nustd.fractions`` value form with the mem leaf and
translates at the boundary: ``set`` lowers the value, a read lifts it back, so
the ref is an operand of the real value throughout. The leaf lives with
its library, not in ``nu.mem``: a container declared with the Python type
holds untyped ``ObjectRef`` children, and a container declared with the leaf
class holds this one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core import ToStr
from nu.domains.shape import SetCmd
from nu.lang import Nu
from nu.mem.refs import ItemRef
from nustd.fractions.forms import Fraction as FractionForm


if TYPE_CHECKING:
    from fractions import Fraction

    from nu.lang import Arg


__all__ = ["FractionRef"]


class FractionRef(ItemRef, FractionForm):
    """A Fraction slot in the dict substrate, stored as ``"numerator/denom"``.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - The stored string is ``str(Fraction)``, already in lowest terms,
          so the exact ratio round-trips.

    Yields:
        A Fraction, parsed from the stored string. EMPTY when the slot was
        never written.

    Example:
        >>> from fractions import Fraction
        >>> class Split(nu.Shape):
        ...     share = nustd.fractions.mem.FractionRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Split)
        >>> _ = nu.run(Split.share.set(Fraction(3, 4)), ctx)
        >>> data
        {'share': '3/4'}
        >>> nu.run(Split.share, ctx)[0]
        Fraction(3, 4)
    """

    def _lift(self, raw: object) -> Fraction:
        """Parse the stored str back to a Fraction."""
        from fractions import Fraction as FractionCls

        return raw if isinstance(raw, FractionCls) else FractionCls(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[Fraction | str]) -> SetCmd:
        """Write a Fraction into the slot as its string form.

        Notes:
            - A plain Python value is serialised at tree-build time; a Nu
              operand gets a ``ToStr`` node instead.
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)
