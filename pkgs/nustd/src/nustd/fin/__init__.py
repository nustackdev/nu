"""Nu surface for financial value types - ``Percentage`` and ``BasisPoint``.

There is no Python stdlib ``fin`` module; these are Nu's own value types, built
the same way the stdlib surfaces are - a native dataclass (``native``, exported
with a ``Py`` prefix) wrapped by a Form (``forms``) whose constructors and
methods are ``interactions`` atoms. Import them like the rest of the std
library::

    from nustd.fin import BasisPoint, Percentage       # Forms: Percentage.of(75.5)
    from nustd.fin import PyBasisPoint, PyPercentage    # raw Python values
"""

from __future__ import annotations

from nustd.fin.forms import BasisPoint, Percentage
from nustd.fin.native import PyBasisPoint, PyPercentage


__all__ = ["BasisPoint", "Percentage", "PyBasisPoint", "PyPercentage"]
