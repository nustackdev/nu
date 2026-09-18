"""Attr: the name of every attribute in the Nu schema.

One typed vocabulary, so nothing refers to an attribute by a bare string. A
declared attribute is named off the class binding that carries it; a computed
attribute is named where its concern registers it. Every concern module and
every law reads its names from here.
"""

from __future__ import annotations

import sys as _sys


if _sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum as _Enum

    class StrEnum(str, _Enum):
        """Backport of enum.StrEnum for Python 3.10."""

        def __new__(cls, value: str) -> StrEnum:
            member = str.__new__(cls, value)
            member._value_ = value
            return member

        def __str__(self) -> str:
            return str.__str__(self)


__all__ = ["Attr"]


class Attr(StrEnum):
    """The name of every attribute in the Nu schema, grouped by concern."""

    # structure
    SORT = "sort"
    PARAM_SLOTS = "param_slots"
    STRUCTURAL = "structural"
    # effects
    MUTATES = "mutates"
    COMPOSITION_EFFECTS = "composition_effects"
    # cardinality
    CARDINALITY = "cardinality"
    CHILD_CARDINALITY = "child_cardinality"
    # sync / async
    REQUIRES_ASYNC = "requires_async"
    ASYNC_AFFINITY = "async_affinity"
    HAS_ASYNC_ONLY_ATOM = "has_async_only_atom"
    HAS_SYNC_ONLY_ATOM = "has_sync_only_atom"
    ON_LOOP = "on_loop"
    # exec order
    EXEC_ORDER = "exec_order"
    # sort fold: a helper for the Flow law, beyond the settled concern vocab
    HAS_COMMAND = "has_command"
    # dyn fold: subtree contains a Dyn node (dynamic evaluation of a runtime term)
    HAS_DYNAMIC = "has_dynamic"
