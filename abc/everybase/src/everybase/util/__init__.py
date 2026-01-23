"""Utility functions for everybase.

- ensure_term(): Convert Python values to Term expressions
- typed_ref(): Wrap operations in typed Ref classes
- combiners: Combination utilities for Terms
"""

from .combiners import all_, and_, any_, coalesce, ifelse, none_, or_
from .conversion import ensure_term, typed_ref


__all__ = [
    "all_",
    "and_",
    "any_",
    "coalesce",
    "ensure_term",
    "ifelse",
    "none_",
    "or_",
    "typed_ref",
]
