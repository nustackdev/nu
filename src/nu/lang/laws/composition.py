"""Sort and composition laws: the structural floor of Nu.

Every direct child of every node fits its parent's composition matrix row.
A Query atom declares no mutation on itself; a Command and an Action each
declare at least one; a Flow's body slots hold mutators. Span is handled
transparently in the matrix-fit walk: a Span child slot-fits as its body's
sort.

These laws read ``sort`` and ``mutates``; nothing here recomputes
attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Law, predicate
from nu.lang.attributes import MATRIX, Attr, Sort, matrix_sort, subsort

from .predicates import (
    attr_true,
    child_paths,
    has_children,
    of_sort,
)


if TYPE_CHECKING:
    from nu.engine import Path, Program


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


# --- flow slot-role walk ------------------------------------------------


_MUTATING_SORTS: frozenset[Sort] = frozenset({Sort.COMMAND, Sort.ACTION, Sort.FLOW})
_YIELDING_SORTS: frozenset[Sort] = frozenset({Sort.REF, Sort.QUERY, Sort.ACTION})


def _effective_sort(program: Program, path: Path) -> Sort:
    """The sort of ``path`` after looking through Spans to the body.

    A Span is transparent: its parent sees through to whatever the Span
    wraps. An empty Span resolves to its own sort.
    """
    sort: Sort = program.attr(path, Attr.SORT)
    if not subsort(sort, Sort.SPAN):
        return sort
    body = child_paths(program, path)
    return _effective_sort(program, body[0]) if body else sort


def _non_mutating_body(program: Program, path: Path) -> Path | None:
    """The first direct body-slot child that is not a mutating child."""
    param_slots: frozenset[int] = program.attr(path, Attr.PARAM_SLOTS)
    for slot, child in enumerate(child_paths(program, path)):
        if slot in param_slots:
            continue
        sort = _effective_sort(program, child)
        if not any(subsort(sort, m) for m in _MUTATING_SORTS):
            return child
    return None


def _non_yielding_param(program: Program, path: Path) -> Path | None:
    """The first direct param-slot child that is not a yielding child."""
    param_slots: frozenset[int] = program.attr(path, Attr.PARAM_SLOTS)
    for slot, child in enumerate(child_paths(program, path)):
        if slot not in param_slots:
            continue
        sort = _effective_sort(program, child)
        if not any(subsort(sort, y) for y in _YIELDING_SORTS):
            return child
    return None


@predicate
def flow_body_mutators(program: Program, path: Path) -> bool:
    """Holds when every direct body-slot child of a Flow is mutating."""
    return _non_mutating_body(program, path) is None


def flow_body_detail(program: Program, path: Path) -> str:
    """Name the non-mutating child sort a Flow body slot holds."""
    child = _non_mutating_body(program, path)
    sort = _effective_sort(program, child) if child is not None else None
    return f"a Flow body slot is not a mutating child: {sort}"


@predicate
def control_param_yielders(program: Program, path: Path) -> bool:
    """Holds when every direct param-slot child of a Control is yielding."""
    return _non_yielding_param(program, path) is None


def control_param_detail(program: Program, path: Path) -> str:
    """Name the non-yielding child sort a Control param slot holds."""
    child = _non_yielding_param(program, path)
    sort = _effective_sort(program, child) if child is not None else None
    return f"a Control param slot is not a yielding child: {sort}"


# --- laws ---------------------------------------------------------------


LAWS: tuple[Law, ...] = (
    Law(
        "composition",
        scope=has_children,
        holds=composes,
        message=compose_detail,
    ),
    Law(
        "query_no_own_write",
        scope=of_sort(Sort.QUERY),
        holds=~attr_true(Attr.MUTATES),
        message="a Query declares a mutation slot",
    ),
    Law(
        "command_has_write",
        scope=of_sort(Sort.COMMAND),
        holds=attr_true(Attr.MUTATES),
        message="a Command declares no mutation slot",
    ),
    Law(
        "action_has_write",
        scope=of_sort(Sort.ACTION),
        holds=attr_true(Attr.MUTATES),
        message="an Action declares no mutation slot",
    ),
    Law(
        "flow_body_is_mutator",
        scope=of_sort(Sort.FLOW),
        holds=flow_body_mutators,
        message=flow_body_detail,
    ),
    Law(
        "control_param_is_yielder",
        scope=of_sort(Sort.CONTROL),
        holds=control_param_yielders,
        message=control_param_detail,
    ),
)
