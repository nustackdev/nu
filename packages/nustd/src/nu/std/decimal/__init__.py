"""Nu surface for Python's ``decimal`` module - the ``Decimal`` type.

Mirrors ``decimal`` 1-1 for the value type: ``Decimal`` is a Form backed by
``decimal.Decimal``, so arithmetic stays exact. ``decimal``'s module-level
helpers and contexts (``getcontext``, ``localcontext``, ``ROUND_*`` ...) are out
of scope, so there are just two layers: ``forms`` (the class) and
``interactions`` (the constructor and method atoms; arithmetic and comparison
use the core atoms). Import it like the stdlib::

    from nu.std.decimal import Decimal    # Decimal.of("0.1") + Decimal.of("0.2")
"""

from __future__ import annotations

from nu.std.decimal.forms import Decimal


__all__ = ["Decimal"]
