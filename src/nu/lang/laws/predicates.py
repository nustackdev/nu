"""Generic predicate building blocks shared across law dimensions.

A law is a ``scope`` predicate (which nodes it judges) and a ``holds``
predicate (the condition each scoped node must satisfy). This module owns
the *generic* combinators every dimension reaches for: scope by sort, scope
by attribute truth, child enumeration, simple effect and cardinality
folds. Dimension-specific helpers (the composition matrix walk, the
ref-slot detail) live in their dimension module.

Every predicate reads attributes the compile phase produced; a subtree-wide
check reads a folded attribute rather than walking the tree. Predicates
compose with ``&``, ``|`` and ``~``; feed any of them to a ``Law``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Predicate, predicate
from nu.lang.attributes import Attr, Sort, subsort


if TYPE_CHECKING:
    from nu.engine import Path, Program
    from nu.lang.attributes import Cardinality, Effect


__all__ = [
    "attr_equals",
    "attr_true",
    "cardinality_is",
    "child_paths",
    "has_children",
    "no_child_yields",
    "no_composition_effect",
    "of_sort",
]


def child_paths(program: Program, path: Path) -> list[Path]:
    """The child paths of ``path``."""
    path_of = program.path_of
    return [path_of[c] for c in program.children[program.id_of[path]]]


# --- scope predicates ---------------------------------------------------


def of_sort(sort: Sort) -> Predicate:
    """Nodes whose sort is ``sort`` or descends from it."""
    return Predicate(lambda program, path: subsort(program.attr(path, Attr.SORT), sort))


def cardinality_is(cardinality: Cardinality) -> Predicate:
    """Nodes whose sort declares the given cardinality."""
    return Predicate(lambda program, path: program.attr(path, Attr.CARDINALITY) is cardinality)


def attr_true(name: Attr) -> Predicate:
    """Nodes where the attribute ``name`` is truthy."""
    return Predicate(lambda program, path: bool(program.attr(path, name)))


def attr_equals(name: Attr, value: object) -> Predicate:
    """Nodes where the attribute ``name`` equals ``value``."""
    return Predicate(lambda program, path: program.attr(path, name) == value)


@predicate
def has_children(program: Program, path: Path) -> bool:
    """Nodes that hold at least one child."""
    return bool(program.children[program.id_of[path]])


# --- holds predicates ---------------------------------------------------


def no_composition_effect(effect: Effect) -> Predicate:
    """Holds when no effect of the node's subtree is ``effect``."""
    return Predicate(
        lambda program, path: all(
            eff is not effect for _, eff in program.attr(path, Attr.COMPOSITION_EFFECTS)
        )
    )


def no_child_yields(cardinality: Cardinality) -> Predicate:
    """Holds when no direct child resolves its cardinality to ``cardinality``."""
    return Predicate(
        lambda program, path: all(
            program.attr(child, Attr.CHILD_CARDINALITY) is not cardinality
            for child in child_paths(program, path)
        )
    )
