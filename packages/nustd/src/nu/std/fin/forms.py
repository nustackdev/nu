"""Financial value types as Forms: ``Percentage`` and ``BasisPoint``.

Each Form is the typed access surface over its native dataclass
(``nu.std.fin.native``), the same way ``Fraction`` wraps ``fractions.Fraction``:

- **constructors** are ``host`` atoms in ``interactions``; the
  literal constructor is ``.of(...)`` since ``__init__`` wraps a Nu term.
- **conversions / application** (``to_dec``, ``apply``, ``add_to`` ...) are
  factory atoms binding the unbound native methods.
- **arithmetic** (``+`` ``-`` ``*`` ``/`` and unary ``-``) reuses the core
  arithmetic atoms - Python performs the real op on the resolved values and the
  result is rewrapped.
- **comparison** reuses the core comparison atoms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

from nu.lang import Form, TypedNu
from nu.std.fin.native import PyBasisPoint, PyPercentage


if TYPE_CHECKING:
    from nu.forms.primitives import Bool, Float, Int
    from nu.lang import Arg, FloatArg, IntArg

    PercentageArg: TypeAlias = "Arg[PyPercentage] | FloatArg"
    BasisPointArg: TypeAlias = "Arg[PyBasisPoint] | IntArg"


__all__ = ["BasisPoint", "Percentage"]


class Percentage(Form, TypedNu[PyPercentage]):
    """A percentage as a Form (``75.5`` = 75.5%).

    Build one with ``Percentage.of(75.5)`` (or ``from_dec`` / ``from_bps`` /
    ``from_ratio``); convert with ``to_dec`` / ``to_bps``; apply to an amount
    with ``apply`` / ``add_to`` / ``sub_from``.
    """

    # --- constructors --------------------------------------------------------

    @classmethod
    def of(cls, value: FloatArg) -> Percentage:
        """A percentage from a raw value: ``Percentage(75.5)``."""
        from .interactions import PercentageOf

        return Percentage(PercentageOf(value))

    @classmethod
    def from_dec(cls, dec: FloatArg) -> Percentage:
        """From a decimal ratio: ``Percentage.from_dec(0.755)`` -> 75.5%."""
        from .interactions import PercentageFromDec

        return Percentage(PercentageFromDec(dec))

    @classmethod
    def from_bps(cls, bps: IntArg) -> Percentage:
        """From basis points: ``Percentage.from_bps(7550)`` -> 75.5%."""
        from .interactions import PercentageFromBps

        return Percentage(PercentageFromBps(bps))

    @classmethod
    def from_ratio(cls, numerator: FloatArg, denominator: FloatArg) -> Percentage:
        """From a ratio: ``Percentage.from_ratio(3, 4)`` -> 75%."""
        from .interactions import PercentageFromRatio

        return Percentage(PercentageFromRatio(numerator, denominator))

    # --- conversions ---------------------------------------------------------

    def to_dec(self) -> Float:
        """The decimal ratio (75.5% -> ``0.755``)."""
        from nu.forms import Float

        from .interactions import PercentageToDec

        return Float(PercentageToDec(self))

    def to_bps(self) -> Int:
        """The basis points (75.5% -> ``7550``)."""
        from nu.forms import Int

        from .interactions import PercentageToBps

        return Int(PercentageToBps(self))

    def to_float(self) -> Float:
        """The raw percentage value."""
        from nu.forms import Float

        from .interactions import PercentageToFloat

        return Float(PercentageToFloat(self))

    # --- application ---------------------------------------------------------

    def apply(self, amount: FloatArg) -> Float:
        """This percentage of ``amount``."""
        from nu.forms import Float

        from .interactions import PercentageApply

        return Float(PercentageApply(self, amount))

    def add_to(self, amount: FloatArg) -> Float:
        """``amount`` grown by this percentage."""
        from nu.forms import Float

        from .interactions import PercentageAddTo

        return Float(PercentageAddTo(self, amount))

    def sub_from(self, amount: FloatArg) -> Float:
        """``amount`` reduced by this percentage."""
        from nu.forms import Float

        from .interactions import PercentageSubFrom

        return Float(PercentageSubFrom(self, amount))

    # --- validation ----------------------------------------------------------

    def is_valid(self, min_val: float = 0.0, max_val: float = 100.0) -> Bool:
        """Whether the value falls within ``[min_val, max_val]``."""
        from nu.forms import Bool

        from .interactions import PercentageIsValid

        return Bool(PercentageIsValid(self, min_val, max_val))

    def clamp(self, min_val: float = 0.0, max_val: float = 100.0) -> Percentage:
        """This percentage clamped to ``[min_val, max_val]``."""
        from .interactions import PercentageClamp

        return Percentage(PercentageClamp(self, min_val, max_val))

    # --- arithmetic (reuse core atoms) ---------------------------------------

    def __add__(self, other: PercentageArg) -> Percentage:
        from nu.core import Add

        return Percentage(Add(self, other))

    def __sub__(self, other: PercentageArg) -> Percentage:
        from nu.core import Sub

        return Percentage(Sub(self, other))

    def __mul__(self, factor: FloatArg) -> Percentage:
        from nu.core import Mul

        return Percentage(Mul(self, factor))

    def __truediv__(self, divisor: FloatArg) -> Percentage:
        from nu.core import Div

        return Percentage(Div(self, divisor))

    def __neg__(self) -> Percentage:
        from nu.core import Neg

        return Percentage(Neg(self))

    # --- comparison (reuse core atoms) ---------------------------------------

    def __gt__(self, other: PercentageArg) -> Bool:
        from nu.core import Gt
        from nu.forms import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: PercentageArg) -> Bool:
        from nu.core import Lt
        from nu.forms import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: PercentageArg) -> Bool:
        from nu.core import Ge
        from nu.forms import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: PercentageArg) -> Bool:
        from nu.core import Le
        from nu.forms import Bool

        return Bool(Le(self, other))

    def eq(self, other: PercentageArg) -> Bool:
        """Whether two percentages are equal."""
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def ne(self, other: PercentageArg) -> Bool:
        """Whether two percentages differ."""
        from nu.core import Ne
        from nu.forms import Bool

        return Bool(Ne(self, other))


class BasisPoint(Form, TypedNu[PyBasisPoint]):
    """A basis-point count as a Form - 1/100th of a percent (``500`` = 5%).

    Build one with ``BasisPoint.of(500)`` (or ``from_pct`` / ``from_dec``);
    convert with ``to_pct`` / ``to_dec``; apply to an amount with ``apply`` /
    ``add_to`` / ``sub_from``.
    """

    # --- constructors --------------------------------------------------------

    @classmethod
    def of(cls, value: IntArg) -> BasisPoint:
        """A basis-point count from a raw int: ``BasisPoint(500)``."""
        from .interactions import BasisPointOf

        return BasisPoint(BasisPointOf(value))

    @classmethod
    def from_pct(cls, pct: FloatArg) -> BasisPoint:
        """From a percentage: ``BasisPoint.from_pct(5.0)`` -> 500 bps."""
        from .interactions import BasisPointFromPct

        return BasisPoint(BasisPointFromPct(pct))

    @classmethod
    def from_dec(cls, dec: FloatArg) -> BasisPoint:
        """From a decimal ratio: ``BasisPoint.from_dec(0.05)`` -> 500 bps."""
        from .interactions import BasisPointFromDec

        return BasisPoint(BasisPointFromDec(dec))

    # --- conversions ---------------------------------------------------------

    def to_pct(self) -> Float:
        """The percentage (500 bps -> ``5.0``)."""
        from nu.forms import Float

        from .interactions import BasisPointToPct

        return Float(BasisPointToPct(self))

    def to_dec(self) -> Float:
        """The decimal ratio (500 bps -> ``0.05``)."""
        from nu.forms import Float

        from .interactions import BasisPointToDec

        return Float(BasisPointToDec(self))

    def to_int(self) -> Int:
        """The raw basis-point count."""
        from nu.forms import Int

        from .interactions import BasisPointToInt

        return Int(BasisPointToInt(self))

    # --- application ---------------------------------------------------------

    def apply(self, amount: FloatArg) -> Float:
        """This many basis points of ``amount``."""
        from nu.forms import Float

        from .interactions import BasisPointApply

        return Float(BasisPointApply(self, amount))

    def add_to(self, amount: FloatArg) -> Float:
        """``amount`` grown by these basis points."""
        from nu.forms import Float

        from .interactions import BasisPointAddTo

        return Float(BasisPointAddTo(self, amount))

    def sub_from(self, amount: FloatArg) -> Float:
        """``amount`` reduced by these basis points."""
        from nu.forms import Float

        from .interactions import BasisPointSubFrom

        return Float(BasisPointSubFrom(self, amount))

    # --- arithmetic (reuse core atoms) ---------------------------------------

    def __add__(self, other: BasisPointArg) -> BasisPoint:
        from nu.core import Add

        return BasisPoint(Add(self, other))

    def __sub__(self, other: BasisPointArg) -> BasisPoint:
        from nu.core import Sub

        return BasisPoint(Sub(self, other))

    def __mul__(self, factor: FloatArg) -> BasisPoint:
        from nu.core import Mul

        return BasisPoint(Mul(self, factor))

    def __truediv__(self, divisor: FloatArg) -> BasisPoint:
        from nu.core import Div

        return BasisPoint(Div(self, divisor))

    def __floordiv__(self, divisor: IntArg) -> BasisPoint:
        from nu.core import FloorDiv

        return BasisPoint(FloorDiv(self, divisor))

    # --- comparison (reuse core atoms) ---------------------------------------

    def __gt__(self, other: BasisPointArg) -> Bool:
        from nu.core import Gt
        from nu.forms import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: BasisPointArg) -> Bool:
        from nu.core import Lt
        from nu.forms import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: BasisPointArg) -> Bool:
        from nu.core import Ge
        from nu.forms import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: BasisPointArg) -> Bool:
        from nu.core import Le
        from nu.forms import Bool

        return Bool(Le(self, other))

    def eq(self, other: BasisPointArg) -> Bool:
        """Whether two basis-point counts are equal."""
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def ne(self, other: BasisPointArg) -> Bool:
        """Whether two basis-point counts differ."""
        from nu.core import Ne
        from nu.forms import Bool

        return Bool(Ne(self, other))
