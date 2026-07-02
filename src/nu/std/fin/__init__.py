"""Nu surface for financial value types - ``Percentage`` and ``BasisPoint``.

There is no Python stdlib ``fin`` module; these are Nu's own value types, built
the same way the stdlib surfaces are - a native dataclass (``native``) wrapped
by a Form (``forms``) whose constructors and methods are ``interactions`` atoms.
Import them like the rest of the std library::

    from nu.std.fin import BasisPoint, Percentage   # Percentage.of(75.5), BasisPoint.of(500)
"""

from __future__ import annotations

from nu.std.fin.forms import BasisPoint, Percentage


__all__ = ["BasisPoint", "Percentage"]
