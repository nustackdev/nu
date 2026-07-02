"""fin interactions - one ``ScalarQueryFactory`` binding per host call.

Constructors bind the native class / its classmethods; methods bind the
*unbound* method (a plain callable whose first argument is the receiver, so
``p.to_dec()`` is ``Percentage.to_dec(p)``). Arithmetic and comparison are not
here - they reuse the core atoms.
"""

from __future__ import annotations

from nu.lang import ScalarQueryFactory
from nu.std.fin.native import BasisPoint as _BasisPoint
from nu.std.fin.native import Percentage as _Percentage


__all__ = [
    "BasisPointAddTo",
    "BasisPointApply",
    "BasisPointFromDec",
    "BasisPointFromPct",
    "BasisPointOf",
    "BasisPointSubFrom",
    "BasisPointToDec",
    "BasisPointToInt",
    "BasisPointToPct",
    "PercentageAddTo",
    "PercentageApply",
    "PercentageClamp",
    "PercentageFromBps",
    "PercentageFromDec",
    "PercentageFromRatio",
    "PercentageIsValid",
    "PercentageOf",
    "PercentageSubFrom",
    "PercentageToBps",
    "PercentageToDec",
    "PercentageToFloat",
]


# --- percentage constructors ------------------------------------------------

PercentageOf = ScalarQueryFactory("PercentageOf", _Percentage)
PercentageFromDec = ScalarQueryFactory("PercentageFromDec", _Percentage.from_dec)
PercentageFromBps = ScalarQueryFactory("PercentageFromBps", _Percentage.from_bps)
PercentageFromRatio = ScalarQueryFactory("PercentageFromRatio", _Percentage.from_ratio)

# --- percentage conversions -------------------------------------------------

PercentageToDec = ScalarQueryFactory("PercentageToDec", _Percentage.to_dec)
PercentageToBps = ScalarQueryFactory("PercentageToBps", _Percentage.to_bps)
PercentageToFloat = ScalarQueryFactory("PercentageToFloat", _Percentage.to_float)

# --- percentage application + validation ------------------------------------

PercentageApply = ScalarQueryFactory("PercentageApply", _Percentage.apply)
PercentageAddTo = ScalarQueryFactory("PercentageAddTo", _Percentage.add_to)
PercentageSubFrom = ScalarQueryFactory("PercentageSubFrom", _Percentage.sub_from)
PercentageIsValid = ScalarQueryFactory("PercentageIsValid", _Percentage.is_valid)
PercentageClamp = ScalarQueryFactory("PercentageClamp", _Percentage.clamp)

# --- basis point constructors -----------------------------------------------

BasisPointOf = ScalarQueryFactory("BasisPointOf", _BasisPoint)
BasisPointFromPct = ScalarQueryFactory("BasisPointFromPct", _BasisPoint.from_pct)
BasisPointFromDec = ScalarQueryFactory("BasisPointFromDec", _BasisPoint.from_dec)

# --- basis point conversions ------------------------------------------------

BasisPointToPct = ScalarQueryFactory("BasisPointToPct", _BasisPoint.to_pct)
BasisPointToDec = ScalarQueryFactory("BasisPointToDec", _BasisPoint.to_dec)
BasisPointToInt = ScalarQueryFactory("BasisPointToInt", _BasisPoint.to_int)

# --- basis point application ------------------------------------------------

BasisPointApply = ScalarQueryFactory("BasisPointApply", _BasisPoint.apply)
BasisPointAddTo = ScalarQueryFactory("BasisPointAddTo", _BasisPoint.add_to)
BasisPointSubFrom = ScalarQueryFactory("BasisPointSubFrom", _BasisPoint.sub_from)
