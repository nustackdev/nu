"""fin interactions - one ``ScalarQueryFactory`` binding per host call.

Constructors bind the native class / its classmethods; methods bind the
*unbound* method (a plain callable whose first argument is the receiver, so
``p.to_dec()`` is ``Percentage.to_dec(p)``). Arithmetic and comparison are not
here - they reuse the core atoms.
"""

from __future__ import annotations

from nu.lang import ScalarQueryFactory
from nu.std.fin.native import PyBasisPoint, PyPercentage


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

PercentageOf = ScalarQueryFactory("PercentageOf", PyPercentage)
PercentageFromDec = ScalarQueryFactory("PercentageFromDec", PyPercentage.from_dec)
PercentageFromBps = ScalarQueryFactory("PercentageFromBps", PyPercentage.from_bps)
PercentageFromRatio = ScalarQueryFactory("PercentageFromRatio", PyPercentage.from_ratio)

# --- percentage conversions -------------------------------------------------

PercentageToDec = ScalarQueryFactory("PercentageToDec", PyPercentage.to_dec)
PercentageToBps = ScalarQueryFactory("PercentageToBps", PyPercentage.to_bps)
PercentageToFloat = ScalarQueryFactory("PercentageToFloat", PyPercentage.to_float)

# --- percentage application + validation ------------------------------------

PercentageApply = ScalarQueryFactory("PercentageApply", PyPercentage.apply)
PercentageAddTo = ScalarQueryFactory("PercentageAddTo", PyPercentage.add_to)
PercentageSubFrom = ScalarQueryFactory("PercentageSubFrom", PyPercentage.sub_from)
PercentageIsValid = ScalarQueryFactory("PercentageIsValid", PyPercentage.is_valid)
PercentageClamp = ScalarQueryFactory("PercentageClamp", PyPercentage.clamp)

# --- basis point constructors -----------------------------------------------

BasisPointOf = ScalarQueryFactory("BasisPointOf", PyBasisPoint)
BasisPointFromPct = ScalarQueryFactory("BasisPointFromPct", PyBasisPoint.from_pct)
BasisPointFromDec = ScalarQueryFactory("BasisPointFromDec", PyBasisPoint.from_dec)

# --- basis point conversions ------------------------------------------------

BasisPointToPct = ScalarQueryFactory("BasisPointToPct", PyBasisPoint.to_pct)
BasisPointToDec = ScalarQueryFactory("BasisPointToDec", PyBasisPoint.to_dec)
BasisPointToInt = ScalarQueryFactory("BasisPointToInt", PyBasisPoint.to_int)

# --- basis point application ------------------------------------------------

BasisPointApply = ScalarQueryFactory("BasisPointApply", PyBasisPoint.apply)
BasisPointAddTo = ScalarQueryFactory("BasisPointAddTo", PyBasisPoint.add_to)
BasisPointSubFrom = ScalarQueryFactory("BasisPointSubFrom", PyBasisPoint.sub_from)
