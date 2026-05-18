"""Nu's sort taxonomy: the kind hierarchy, the subsort relation, the matrix.

A sort is a node's structural category. Sorts form a tree; ``subsort`` walks
it. The composition matrix is keyed by the eight leaf labels a parent sees
when slot-fitting a child.
"""

from __future__ import annotations

from enum import StrEnum


__all__ = ["MATRIX", "SUBSORT", "Effect", "Mode", "own_label", "subsort"]


class Effect(StrEnum):
    """An interaction with Context, carried in a tracked-effect tuple."""

    RESOLVE = "resolve"
    READ = "read"
    WRITE = "write"


class Mode(StrEnum):
    """An execution context a kind is appropriate for."""

    SYNC = "sync"
    ASYNC = "async"


# The sort tree: child sort -> parent sort. Ref is a root of its own; the
# Interaction sub-kinds descend from Interaction.
SUBSORT: dict[str, str] = {
    "Query": "Interaction",
    "Command": "Interaction",
    "Flow": "Interaction",
    "Span": "Interaction",
    "ScalarQuery": "Query",
    "StreamQuery": "Query",
    "Reduction": "ScalarQuery",
    "ScalarCommand": "Command",
    "Strategy": "Flow",
    "Control": "Flow",
    "Bracket": "Span",
    "Policy": "Span",
}


def subsort(a: str, b: str) -> bool:
    """Return True if sort ``a`` is ``b`` or descends from it."""
    current: str | None = a
    while current is not None:
        if current == b:
            return True
        current = SUBSORT.get(current)
    return False


def own_label(sort: str) -> str | None:
    """Map a sort to its composition-matrix label, or None if it has none."""
    if sort == "Ref":
        return "Ref"
    if subsort(sort, "StreamQuery"):
        return "StreamQ"
    if subsort(sort, "ScalarQuery"):
        return "ScalarQ"
    if subsort(sort, "Command"):
        return "ScalarC"
    if subsort(sort, "Strategy"):
        return "Strategy"
    if subsort(sort, "Control"):
        return "Control"
    if subsort(sort, "Bracket"):
        return "Bracket"
    if subsort(sort, "Policy"):
        return "Policy"
    return None


_VALUE = frozenset({"Ref", "ScalarQ", "StreamQ", "Bracket", "Policy"})
_WORK = frozenset({"ScalarC", "Strategy", "Control", "Bracket", "Policy"})
_ALL = frozenset(
    {"Ref", "ScalarQ", "StreamQ", "ScalarC", "Strategy", "Control", "Bracket", "Policy"}
)

# Composition matrix: parent label -> the set of child labels it accepts.
# Mirrors model/02-atoms/00-map.md.
MATRIX: dict[str, frozenset[str]] = {
    "Ref": _VALUE,
    "ScalarQ": _VALUE,
    "StreamQ": _VALUE,
    "ScalarC": _VALUE,
    "Strategy": _WORK,
    "Control": _ALL,
    "Bracket": _ALL,
    "Policy": _ALL,
}
