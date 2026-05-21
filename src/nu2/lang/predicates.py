"""Predicates: the building blocks Nu's laws are written from.

A law is a ``scope`` predicate and a ``holds`` predicate. This module supplies
both, plus the message functions that name a failure. Scope predicates select
nodes; holds predicates state the condition a scoped node must satisfy. Every
predicate reads attributes compilation produced, so a subtree-wide check reads
a folded attribute rather than walking the tree.

Predicates compose with ``&``, ``|`` and ``~``; feed any of them to a ``Law``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.attribution import Predicate, predicate
from nu2.lang.attrs import Attr
from nu2.lang.sort import MATRIX, Sort, matrix_sort, subsort


if TYPE_CHECKING:
    from nu2.engine.attribution import Program
    from nu2.engine.attribution.program import Path
    from nu2.lang.cardinality import Cardinality
    from nu2.lang.effects import Effect

__all__ = [
    "attr_equals",
    "attr_true",
    "cardinality_is",
    "compose_detail",
    "composes",
    "declares_effect",
    "has_children",
    "no_child_yields",
    "no_composition_effect",
    "of_sort",
    "ref_slot_detail",
    "ref_slots_hold_refs",
]


# --- scope predicates: which nodes a law judges --------------------------


def of_sort(sort: Sort) -> Predicate:
    """Nodes whose sort is ``sort`` or descends from it."""
    return Predicate(lambda program, path: subsort(program.attr(path, Attr.SORT), sort))


def cardinality_is(cardinality: Cardinality) -> Predicate:
    """Nodes whose sort declares the given cardinality."""
    return Predicate(lambda program, path: program.attr(path, Attr.CARDINALITY) is cardinality)


def attr_true(name: Attr) -> Predicate:
    """Nodes where the attribute ``name`` is truthy."""
    return Predicate(lambda program, path: bool(program.attr(path, name)))


@predicate
def has_children(program: Program, path: Path) -> bool:
    """Nodes that hold at least one child."""
    return bool(program.children(path))


# --- holds predicates: the condition a scoped node must satisfy ----------


def no_composition_effect(effect: Effect) -> Predicate:
    """Holds when no effect of the node's subtree is ``effect``."""
    return Predicate(
        lambda program, path: all(
            eff is not effect for _, eff in program.attr(path, Attr.COMPOSITION_EFFECTS)
        )
    )


def declares_effect(effect: Effect) -> Predicate:
    """Holds when the node annotates at least one slot with ``effect``."""
    return Predicate(lambda program, path: effect in program.attr(path, Attr.OWN_EFFECTS).values())


def attr_equals(name: Attr, value: object) -> Predicate:
    """Holds when the attribute ``name`` equals ``value``."""
    return Predicate(lambda program, path: program.attr(path, name) == value)


def no_child_yields(cardinality: Cardinality) -> Predicate:
    """Holds when no direct child resolves its cardinality to ``cardinality``."""
    return Predicate(
        lambda program, path: all(
            program.attr(child, Attr.CHILD_CARDINALITY) is not cardinality
            for child in program.children(path)
        )
    )


# --- composition matrix --------------------------------------------------


def _slot_fit_sort(program: Program, path: Path) -> Sort | None:
    """The matrix sort a parent sees for the node at ``path``, through Spans.

    A Span is transparent: its parent slot-fits it by the sort of its body.
    """
    sort: Sort = program.attr(path, Attr.SORT)
    if not subsort(sort, Sort.SPAN):
        return matrix_sort(sort)
    body = program.children(path)
    return _slot_fit_sort(program, body[0]) if body else matrix_sort(sort)


def _rejected_child(program: Program, path: Path) -> Path | None:
    """The first child the node's composition matrix row rejects, if any."""
    row = matrix_sort(program.attr(path, Attr.SORT))
    if row is None:
        return None
    for child in program.children(path):
        fit = _slot_fit_sort(program, child)
        if fit is not None and fit not in MATRIX[row]:
            return child
    return None


@predicate
def composes(program: Program, path: Path) -> bool:
    """Holds when every child fits the node's composition matrix row."""
    return _rejected_child(program, path) is None


def compose_detail(program: Program, path: Path) -> str:
    """Name the parent sort and the child sort its matrix rejects."""
    parent = matrix_sort(program.attr(path, Attr.SORT))
    child = _rejected_child(program, path)
    fit = _slot_fit_sort(program, child) if child is not None else None
    return f"{parent} cannot hold {fit}"


# --- ref-typed slots -----------------------------------------------------


def _unfilled_ref_slot(program: Program, path: Path) -> int | None:
    """The first annotated effect slot not filled by a Ref, if any."""
    kids = program.children(path)
    for slot in program.attr(path, Attr.OWN_EFFECTS):
        if slot < len(kids) and program.attr(kids[slot], Attr.SORT) is not Sort.REF:
            return slot
    return None


@predicate
def ref_slots_hold_refs(program: Program, path: Path) -> bool:
    """Holds when every annotated effect slot present is filled by a Ref."""
    return _unfilled_ref_slot(program, path) is None


def ref_slot_detail(program: Program, path: Path) -> str:
    """Name the annotated slot that should hold a Ref but does not."""
    return f"slot {_unfilled_ref_slot(program, path)} must hold a Ref"
