"""Nu surface for Python's ``fractions`` module - exact rational arithmetic.

Mirrors ``fractions`` 1-1: ``Fraction`` is the class (a Form), backed by
``fractions.Fraction``. ``fractions`` has no module-level functions, so there
are just two layers: ``forms`` (the class) and ``interactions`` (the
constructor and method atoms; property reads use core ``GetAttr``,
arithmetic and comparison use the core atoms). Import it like the stdlib::

    from nu.std.fractions import Fraction
    import nu.std.fractions as fractions    # fractions.Fraction.of(1, 3), ...
"""

from __future__ import annotations

from nu.std.fractions.forms import Fraction


__all__ = ["Fraction"]
