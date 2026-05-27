"""Sort and composition laws: the structural floor of Nu.

Every direct child of every node fits its parent's composition matrix row.
A Query atom annotates no WRITE on itself; a Command annotates at least
one; a Flow's body is a mutator. Span is handled transparently in the
matrix-fit walk: a Span child slot-fits as its body's sort.

These laws read ``sort``, ``own_effects``, ``composition_effects`` and the
synthesized ``has_command`` folds; nothing here recomputes attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine import Law, predicate
from nu2.lang.attributes import MATRIX, Attr, Effect, Sort, matrix_sort, subsort

from .predicates import (
    attr_true,
    child_paths,
    declares_effect,
    has_children,
    no_composition_effect,
    of_sort,
)


if TYPE_CHECKING:
    from nu2.engine import Path, Program


__all__ = ["LAWS"]


# --- composition matrix walk -------------------------------------------


def _slot_fit_sort(program: Program, path: Path) -> Sort | None:
    """The matrix sort a parent sees for the node at ``path``, through Spans.

    A Span is transparent: its parent slot-fits it by the sort of its body.
    """
    sort: Sort = program.attr(path, Attr.SORT)
    if not subsort(sort, Sort.SPAN):
        return matrix_sort(sort)
    body = child_paths(program, path)
    return _slot_fit_sort(program, body[0]) if body else matrix_sort(sort)


def _rejected_child(program: Program, path: Path) -> Path | None:
    """The first child the node's composition matrix row rejects, if any."""
    row = matrix_sort(program.attr(path, Attr.SORT))
    if row is None:
        return None
    for child in child_paths(program, path):
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


# --- laws ---------------------------------------------------------------


LAWS: tuple[Law, ...] = (
    Law(
        "composition",
        scope=has_children,
        holds=composes,
        message=compose_detail,
    ),
    Law(
        "query_no_write",
        scope=of_sort(Sort.QUERY),
        holds=no_composition_effect(Effect.WRITE),
        message="a Query subtree contains a WRITE",
    ),
    Law(
        "command_has_write",
        scope=of_sort(Sort.COMMAND),
        holds=declares_effect(Effect.WRITE),
        message="a Command annotates no WRITE slot",
    ),
    Law(
        "flow_has_command",
        scope=of_sort(Sort.FLOW),
        holds=attr_true(Attr.HAS_COMMAND),
        message="a Flow subtree contains no Command",
    ),
)
