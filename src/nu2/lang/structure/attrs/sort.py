"""Sort attribute: the structural taxonomy of a Term.

A sort is a node's structural category. Sorts form a tree with two roots, Ref
and Interaction; ``subsort`` walks it. The composition matrix records, per
parent sort, the child sorts that parent may hold; ``matrix_sort`` folds any
sort onto the eight that carry a row. The synthesized ``has_command`` folds
the sort tree to a subtree-presence flag.

The user-facing Term classes that declare these sorts live in
``nu2.lang.structure.sorts``; this module owns the value space (``Sort``
enum, matrix, helpers) and the sort-flavored attribute folds only.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from nu2.engine.structure import Attribute, Synthesized
from nu2.lang.structure.attrs.names import Attr


if TYPE_CHECKING:
    from nu2.engine.compilation import Path, Program

__all__ = [
    "ATTRIBUTES",
    "MATRIX",
    "Sort",
    "matrix_sort",
    "subsort",
]


class Sort(StrEnum):
    """A node's structural category, a member of the sort tree.

    The leaf sorts are the categories an actual node carries. The interior
    sorts (Interaction, Query, Command, Flow, Span) group them and exist for
    ``subsort`` queries; no node carries one directly.
    """

    REF = "ref"
    INTERACTION = "interaction"
    QUERY = "query"
    SCALAR_QUERY = "scalar_query"
    STREAM_QUERY = "stream_query"
    REDUCTION = "reduction"
    COMMAND = "command"
    SCALAR_COMMAND = "scalar_command"
    FLOW = "flow"
    STRATEGY = "strategy"
    CONTROL = "control"
    SPAN = "span"
    BRACKET = "bracket"
    POLICY = "policy"


# The sort tree, as a child -> parent map. REF and INTERACTION are the roots.
_PARENT: dict[Sort, Sort] = {
    Sort.QUERY: Sort.INTERACTION,
    Sort.COMMAND: Sort.INTERACTION,
    Sort.FLOW: Sort.INTERACTION,
    Sort.SPAN: Sort.INTERACTION,
    Sort.SCALAR_QUERY: Sort.QUERY,
    Sort.STREAM_QUERY: Sort.QUERY,
    Sort.REDUCTION: Sort.SCALAR_QUERY,
    Sort.SCALAR_COMMAND: Sort.COMMAND,
    Sort.STRATEGY: Sort.FLOW,
    Sort.CONTROL: Sort.FLOW,
    Sort.BRACKET: Sort.SPAN,
    Sort.POLICY: Sort.SPAN,
}


def subsort(sort: Sort, ancestor: Sort) -> bool:
    """Return whether ``sort`` is ``ancestor`` or descends from it in the tree."""
    current: Sort | None = sort
    while current is not None:
        if current == ancestor:
            return True
        current = _PARENT.get(current)
    return False


# The eight sorts that carry a matrix row, longest descent first so that
# ``matrix_sort`` resolves a sort to its nearest matrix ancestor.
_MATRIX_SORTS: tuple[Sort, ...] = (
    Sort.STREAM_QUERY,
    Sort.SCALAR_QUERY,
    Sort.SCALAR_COMMAND,
    Sort.STRATEGY,
    Sort.CONTROL,
    Sort.BRACKET,
    Sort.POLICY,
    Sort.REF,
)


def matrix_sort(sort: Sort) -> Sort | None:
    """Resolve ``sort`` to the matrix sort it slot-fits as, or None.

    A Reduction slot-fits as a ScalarQuery, anything under Command as a
    ScalarCommand, and so on. An interior sort with no matrix row yields None.
    """
    for candidate in _MATRIX_SORTS:
        if subsort(sort, candidate):
            return candidate
    return None


# Child sorts that produce a value, and child sorts that do work.
_VALUE = frozenset({Sort.REF, Sort.SCALAR_QUERY, Sort.STREAM_QUERY, Sort.BRACKET, Sort.POLICY})
_WORK = frozenset({Sort.SCALAR_COMMAND, Sort.STRATEGY, Sort.CONTROL, Sort.BRACKET, Sort.POLICY})
_ANY = _VALUE | _WORK

# The composition matrix: each parent sort mapped to the child sorts it holds.
# A value-producing parent holds values; a Strategy holds work; the parents
# that take a body (Control, Bracket, Policy) hold anything.
MATRIX: dict[Sort, frozenset[Sort]] = {
    Sort.REF: _VALUE,
    Sort.SCALAR_QUERY: _VALUE,
    Sort.STREAM_QUERY: _VALUE,
    Sort.SCALAR_COMMAND: _VALUE,
    Sort.STRATEGY: _WORK,
    Sort.CONTROL: _ANY,
    Sort.BRACKET: _ANY,
    Sort.POLICY: _ANY,
}


# --- has_command: a sort fold -----------------------------------------------


def _is_command(program: Program, path: Path) -> bool:
    """A node is itself a Command."""
    return subsort(program.attr(path, Attr.SORT), Sort.COMMAND)


def _any(own: bool, children: list[bool]) -> bool:
    """Fold a flag up a subtree by disjunction."""
    return own or any(children)


ATTRIBUTES: tuple[Attribute, ...] = (
    Synthesized(
        name=Attr.HAS_COMMAND,
        base=_is_command,
        combine=_any,
        reads=(Attr.SORT,),
    ),
)
