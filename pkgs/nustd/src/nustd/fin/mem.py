"""The mem leaves for basis points and percentages: kept as their raw number in a plain dict.

Each leaf pairs the ``nustd.fin`` value form with the mem leaf and
translates at the boundary: ``set`` lowers the value, a read lifts it back, so
the ref is an operand of the real value throughout. The leaves live with
their library, not in ``nu.mem``: a container declared with the Python type
holds untyped ``ObjectRef`` children, and a container declared with the leaf
class holds these.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core import ToFloat, ToInt
from nu.domains.shape import SetCmd
from nu.lang import Nu
from nu.mem.refs import ItemRef
from nustd.fin.forms import BasisPoint as BasisPointForm
from nustd.fin.forms import Percentage as PercentageForm
from nustd.fin.native import PyBasisPoint, PyPercentage


if TYPE_CHECKING:
    from nu.lang import Arg


__all__ = ["BasisPointRef", "PercentageRef"]


class BasisPointRef(ItemRef, BasisPointForm):
    """A BasisPoint slot in the dict substrate, stored as a raw int of bps.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Stored as the bps count itself (250 for 2.5%), an int, so no
          rounding creeps in the way a stored float would.

    Yields:
        A BasisPoint wrapping the stored int. EMPTY when the slot was never
        written.

    Example:
        >>> from nustd.fin import PyBasisPoint
        >>> class Fees(nu.Shape):
        ...     taker = nustd.fin.mem.BasisPointRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Fees)
        >>> _ = nu.run(Fees.taker.set(PyBasisPoint(250)), ctx)
        >>> data
        {'taker': 250}
        >>> nu.run(Fees.taker.apply(1000), ctx)[0]
        25.0
    """

    def _lift(self, raw: object) -> PyBasisPoint:
        """Wrap the stored int back as a BasisPoint."""
        return raw if isinstance(raw, PyBasisPoint) else PyBasisPoint(int(raw))  # type: ignore[arg-type]

    def set(self, value: Arg[PyBasisPoint | int]) -> SetCmd:
        """Write a BasisPoint into the slot as a raw int of bps.

        Notes:
            - A plain Python value is converted at tree-build time; a Nu
              operand gets a ``ToInt`` node instead.
        """
        val = ToInt(value) if isinstance(value, Nu) else int(value)
        return SetCmd(self, val)


class PercentageRef(ItemRef, PercentageForm):
    """A Percentage slot in the dict substrate, stored as a raw float.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Stored as the percentage number itself (2.5 for 2.5%), not the
          0.025 decimal fraction.

    Yields:
        A Percentage wrapping the stored float. EMPTY when the slot was never
        written.

    Example:
        >>> from nustd.fin import PyPercentage
        >>> class Fees(nu.Shape):
        ...     rate = nustd.fin.mem.PercentageRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Fees)
        >>> _ = nu.run(Fees.rate.set(PyPercentage(2.5)), ctx)
        >>> data
        {'rate': 2.5}
        >>> nu.run(Fees.rate.to_bps(), ctx)[0]
        250
    """

    def _lift(self, raw: object) -> PyPercentage:
        """Wrap the stored float back as a Percentage."""
        return raw if isinstance(raw, PyPercentage) else PyPercentage(float(raw))  # type: ignore[arg-type]

    def set(self, value: Arg[PyPercentage | float]) -> SetCmd:
        """Write a Percentage into the slot as a raw float.

        Notes:
            - A plain Python value is converted at tree-build time; a Nu
              operand gets a ``ToFloat`` node instead.
        """
        val = ToFloat(value) if isinstance(value, Nu) else float(value)
        return SetCmd(self, val)
