"""Shared TypeVars for the everyabc type system.

Covariant:
    T_co — Result/value type for Term, Ref, Morphism hierarchies.
           These types only appear in return positions (execute, fetch, apply).
"""

from typing import TypeVar


T_co = TypeVar("T_co", covariant=True)
