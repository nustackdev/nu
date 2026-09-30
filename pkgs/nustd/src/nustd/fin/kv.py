"""The kv leaves for basis points and percentages: kept as their raw number in KV storage.

Each leaf pairs the ``nustd.fin`` value form with the kv leaf and
translates at the boundary: ``set`` lowers the value, a read lifts it back, so
the ref is an operand of the real value throughout. The leaves live with
their library, not in ``nustd.kv``: a container declared with the Python type
holds untyped ``ObjectRef`` children, and a container declared with the leaf
class holds these.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.core import ToFloat, ToInt
from nu.domains.shape import SetCmd
from nu.lang import Nu
from nustd.fin.forms import BasisPoint as BasisPointForm
from nustd.fin.forms import Percentage as PercentageForm
from nustd.fin.native import PyBasisPoint, PyPercentage
from nustd.kv.refs import ItemRef


if TYPE_CHECKING:
    from nu.lang import Arg


__all__ = ["BasisPointRef", "PercentageRef"]


class BasisPointRef(ItemRef, BasisPointForm):
    """A BasisPoint leaf in KV storage, stored as the raw int count of bps.

    Notes:
        - Stored as an int, so a rate is exact and no float rounding creeps
          in between writes and reads.
        - Reads wrap the int back into a BasisPoint, so the conversions
          (``to_pct``, ``to_dec``) and the fee helpers are there on the ref.
        - An absent leaf reads as EMPTY, not as zero bps.

    Example:
        class Fee(Shape):
            taker = BasisPointRef.slot()
        run(Fee.taker.set(25), ctx)
    """

    def _lift(self, raw: object) -> PyBasisPoint:
        """Wrap the stored int back as a BasisPoint."""
        return raw if isinstance(raw, PyBasisPoint) else PyBasisPoint(int(raw))  # type: ignore[arg-type]

    def set(self, value: Arg[PyBasisPoint | int]) -> SetCmd:
        """Write a BasisPoint to the leaf, serialized to its raw int.

        Args:
            value: a BasisPoint, an int count of bps, or an expression
                yielding either.

        Notes:
            - A plain value goes through ``int()`` before the write; an
              expression is wrapped in a ToInt. Either way a fractional
              input truncates toward zero rather than rounding.

        Example:
            run(Fee.taker.set(25), ctx)
        """
        val = ToInt(value) if isinstance(value, Nu) else int(value)
        return SetCmd(self, val)


class PercentageRef(ItemRef, PercentageForm):
    """A Percentage leaf in KV storage, stored as the raw float percentage.

    Notes:
        - Stored as the percentage itself, not as a fraction: 12.5 percent
          is 12.5 on disk, not 0.125.
        - Reads wrap the float back into a Percentage, so the conversions
          (``to_dec``, ``to_bps``) and the apply helpers are on the ref.
        - Float storage, so it carries float rounding; BasisPointRef is the
          exact one.

    Example:
        class Fee(Shape):
            slippage = PercentageRef.slot()
        run(Fee.slippage.set(0.5), ctx)
    """

    def _lift(self, raw: object) -> PyPercentage:
        """Wrap the stored float back as a Percentage."""
        return raw if isinstance(raw, PyPercentage) else PyPercentage(float(raw))  # type: ignore[arg-type]

    def set(self, value: Arg[PyPercentage | float]) -> SetCmd:
        """Write a Percentage to the leaf, serialized to its raw float.

        Args:
            value: a Percentage, a raw float percentage, or an expression
                yielding either.

        Notes:
            - A plain value goes through ``float()`` before the write; an
              expression is wrapped in a ToFloat.
            - The number written is the percentage, so pass 12.5 for 12.5
              percent.

        Example:
            run(Fee.slippage.set(0.5), ctx)
        """
        val = ToFloat(value) if isinstance(value, Nu) else float(value)
        return SetCmd(self, val)
