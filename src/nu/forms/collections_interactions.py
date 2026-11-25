"""Collection constructor interactions.

The atoms only the collection forms' constructors build (``List.create``,
``Dict.of``, ...). No surface method builds them, so they live with the forms,
not with the surfaces.

Empty: ListCreate, TupleCreate, DictCreate, SetCreate, FrozenSetCreate
From items: ListOf, TupleOf, DictOf, SetOf, FrozenSetOf
"""

from __future__ import annotations

from nu.factory.host import host


__all__ = [
    "DictCreate",
    "DictOf",
    "FrozenSetCreate",
    "FrozenSetOf",
    "ListCreate",
    "ListOf",
    "SetCreate",
    "SetOf",
    "TupleCreate",
    "TupleOf",
]


# =============================================================================
# SEQUENCE CONSTRUCTORS
# =============================================================================

# Empty list: deterministic (always []), but each eval must yield a *fresh*
# mutable object - a future fold/CSE pass must not alias two ListCreate results.
ListCreate = host(list, name="ListCreate")
# Empty tuple: deterministic and immutable (sharing one () is fine).
TupleCreate = host(tuple, name="TupleCreate")
# Tuple from positional items: TupleOf(a, b) evaluates each child expression and
# packs the values into a fresh tuple. Sibling to DictOf.
TupleOf = host(lambda *items: items, name="TupleOf")
# List from positional items: sibling to TupleOf; each eval yields a fresh
# mutable list.
ListOf = host(lambda *items: list(items), name="ListOf")


# =============================================================================
# MAPPING CONSTRUCTORS
# =============================================================================

# Empty dict: deterministic (always {}), but each eval must yield a *fresh*
# mutable object - a future fold/CSE pass must not alias two DictCreate results.
DictCreate = host(dict, name="DictCreate")
# Dict from named fields: DictOf(a=x, b=y) evaluates each field expression and
# zips names back into a fresh dict.
DictOf = host(dict, name="DictOf")


# =============================================================================
# SET CONSTRUCTORS
# =============================================================================

# Empty set: deterministic (always set()), but each eval must yield a *fresh*
# mutable object - a future fold/CSE pass must not alias two SetCreate results.
SetCreate = host(set, name="SetCreate")
# Empty frozenset: deterministic and immutable (sharing one frozenset() is fine).
FrozenSetCreate = host(frozenset, name="FrozenSetCreate")
# Set / FrozenSet from positional items: siblings to TupleOf / ListOf.
SetOf = host(lambda *items: set(items), name="SetOf")
FrozenSetOf = host(lambda *items: frozenset(items), name="FrozenSetOf")
