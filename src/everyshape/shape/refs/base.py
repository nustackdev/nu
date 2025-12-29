"""Base ref classes.

This module re-exports the fundamental ref base classes from term.py.
These are the abstract base classes that define the core ref contracts.

For capability implementations, see bases.py.
For complete ref implementations, see refs.py.

Classes:
    PrimitiveRefBase: Base for refs pointing to leaf values (re-exported as PrimitiveRef)
    ViewRefBase: Base for refs pointing to containers (re-exported as ViewRef)
"""

from __future__ import annotations

# Re-export the base classes from term.py with Base suffix for clarity
from ..term import PrimitiveRef as PrimitiveRefBase
from ..term import ViewRef as ViewRefBase


__all__ = [
    "PrimitiveRefBase",
    "ViewRefBase",
]
