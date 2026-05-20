"""Attr: the name of every attribute in the Nu schema.

One typed vocabulary, so nothing refers to an attribute by a bare string. A
declared attribute is named off the class binding that carries it; a computed
attribute is named where its concern registers it. Every concern module and
every law reads its names from here.
"""

from __future__ import annotations

from enum import StrEnum


__all__ = ["Attr"]


class Attr(StrEnum):
    """The name of every attribute in the Nu schema, grouped by concern."""

    # structure
    SORT = "sort"
    # effects
    OWN_EFFECTS = "own_effects"
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
    # algebra
    COMMUTATIVE = "commutative"
    ASSOCIATIVE = "associative"
    IDEMPOTENT = "idempotent"
    DETERMINISTIC = "deterministic"
    # sort fold: a helper for the Flow law, beyond the settled concern vocab
    HAS_COMMAND = "has_command"
