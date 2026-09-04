"""fin interactions - one ``host`` binding per host call.

Constructors bind the native class / its classmethods; methods bind the
*unbound* method (a plain callable whose first argument is the receiver, so
``p.to_dec()`` is ``Percentage.to_dec(p)``). Arithmetic and comparison are not
here - they reuse the core atoms.
"""

from __future__ import annotations

from nu.factory import host
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

PercentageOf = host(PyPercentage, name="PercentageOf")
PercentageFromDec = host(PyPercentage.from_dec, name="PercentageFromDec")
PercentageFromBps = host(PyPercentage.from_bps, name="PercentageFromBps")
PercentageFromRatio = host(PyPercentage.from_ratio, name="PercentageFromRatio")

# --- percentage conversions -------------------------------------------------

PercentageToDec = host(PyPercentage.to_dec, name="PercentageToDec")
PercentageToBps = host(PyPercentage.to_bps, name="PercentageToBps")
PercentageToFloat = host(PyPercentage.to_float, name="PercentageToFloat")

# --- percentage application + validation ------------------------------------

PercentageApply = host(PyPercentage.apply, name="PercentageApply")
PercentageAddTo = host(PyPercentage.add_to, name="PercentageAddTo")
PercentageSubFrom = host(PyPercentage.sub_from, name="PercentageSubFrom")
PercentageIsValid = host(PyPercentage.is_valid, name="PercentageIsValid")
PercentageClamp = host(PyPercentage.clamp, name="PercentageClamp")

# --- basis point constructors -----------------------------------------------

BasisPointOf = host(PyBasisPoint, name="BasisPointOf")
BasisPointFromPct = host(PyBasisPoint.from_pct, name="BasisPointFromPct")
BasisPointFromDec = host(PyBasisPoint.from_dec, name="BasisPointFromDec")

# --- basis point conversions ------------------------------------------------

BasisPointToPct = host(PyBasisPoint.to_pct, name="BasisPointToPct")
BasisPointToDec = host(PyBasisPoint.to_dec, name="BasisPointToDec")
BasisPointToInt = host(PyBasisPoint.to_int, name="BasisPointToInt")

# --- basis point application ------------------------------------------------

BasisPointApply = host(PyBasisPoint.apply, name="BasisPointApply")
BasisPointAddTo = host(PyBasisPoint.add_to, name="BasisPointAddTo")
BasisPointSubFrom = host(PyBasisPoint.sub_from, name="BasisPointSubFrom")
