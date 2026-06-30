"""The builtin ``complex`` as a Form - the value type behind ``nu.std.cmath``.

``complex`` is a builtin with no module of its own; ``cmath`` is its companion
set of functions, so the two co-locate here. This file is the value-type half:
``complex`` as the typed access surface for Python's ``complex`` numbers.

The class name is lowercase ``complex`` to mirror the builtin (hence
``# noqa: N801``), backed by ``from builtins import complex as _complex``.

- **property reads** (``.real``, ``.imag``) reuse core ``GetAttrQuery``.
- **the constructor** is a ``ScalarQueryFactory`` atom in ``interactions``; the
  literal constructor is ``.of(...)`` since ``__init__`` wraps a Nu term.
- **``conjugate()``** is a ``ScalarQueryFactory`` atom over the unbound method.
- **arithmetic** (``+ - * / ** -x +x abs``) reuses the core arithmetic atoms -
  Python performs the real op on the resolved values. ``abs`` is the magnitude
  (a float); the rest stay ``complex``.
- **comparison**: ``complex`` supports only ``==`` / ``!=`` (it is not
  orderable), so just ``eq`` / ``ne`` via the core equality atoms.
"""

from __future__ import annotations

from builtins import complex as _complex
from typing import TYPE_CHECKING

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.forms.primitives import BoolForm, FloatForm
    from nu.lang import Arg, FloatArg

    type ComplexArg = Arg[_complex]


__all__ = ["complex"]


class complex(Form, TypedNu[_complex]):  # noqa: N801
    """``builtins.complex`` as a Form - a complex number.

    Build one with ``complex.of(real, imag)``; read its parts as properties
    (``.real`` / ``.imag``); transform it with arithmetic or ``conjugate()``.
    Complex numbers are not orderable, so only ``eq`` / ``ne`` are provided.
    """

    @classmethod
    def of(cls, real: FloatArg = 0, imag: FloatArg = 0) -> complex:
        """Build a complex number: ``complex(real, imag)``."""
        from .interactions import ComplexOf

        return complex(ComplexOf(real, imag))

    def real(self) -> FloatForm:
        """The real part."""
        from nu import FloatForm
        from nu.core import GetAttrQuery

        return FloatForm(GetAttrQuery(self, "real"))

    def imag(self) -> FloatForm:
        """The imaginary part."""
        from nu import FloatForm
        from nu.core import GetAttrQuery

        return FloatForm(GetAttrQuery(self, "imag"))

    def conjugate(self) -> complex:
        """The complex conjugate (negates the imaginary part)."""
        from .interactions import ComplexConjugate

        return complex(ComplexConjugate(self))

    def __add__(self, other: ComplexArg) -> complex:
        from nu.core import AddQuery

        return complex(AddQuery(self, other))

    def __sub__(self, other: ComplexArg) -> complex:
        from nu.core import SubQuery

        return complex(SubQuery(self, other))

    def __mul__(self, other: ComplexArg) -> complex:
        from nu.core import MulQuery

        return complex(MulQuery(self, other))

    def __truediv__(self, other: ComplexArg) -> complex:
        from nu.core import DivQuery

        return complex(DivQuery(self, other))

    def __pow__(self, other: ComplexArg) -> complex:
        from nu.core import PowQuery

        return complex(PowQuery(self, other))

    def __neg__(self) -> complex:
        from nu.core import NegQuery

        return complex(NegQuery(self))

    def __pos__(self) -> complex:
        from nu.core import PosQuery

        return complex(PosQuery(self))

    def __abs__(self) -> FloatForm:
        from nu import FloatForm
        from nu.core import AbsQuery

        return FloatForm(AbsQuery(self))

    def eq(self, other: ComplexArg) -> BoolForm:
        """Whether two complex numbers are equal."""
        from nu import BoolForm
        from nu.core import EqQuery

        return BoolForm(EqQuery(self, other))

    def ne(self, other: ComplexArg) -> BoolForm:
        """Whether two complex numbers differ."""
        from nu import BoolForm
        from nu.core import NeQuery

        return BoolForm(NeQuery(self, other))
