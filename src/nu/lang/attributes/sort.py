"""Sort attribute: the structural taxonomy of a Term.

A sort is a node's structural category. Sorts form a tree with two roots, Ref
and Interaction; ``subsort`` walks it. The composition matrix records, per
parent sort, the child sorts that parent may hold; ``matrix_sort`` folds any
sort onto the eight that carry a row. The synthesized ``has_command`` folds
the sort tree to a subtree-presence flag.

The user-facing Term classes that declare these sorts live in
``nu.lang.kinds``; this module owns the value space (``Sort`` enum,
matrix, helpers) and the sort-flavored attribute folds only.
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


from typing import TYPE_CHECKING

from nu.engine import Attribute, Synthesized

from .names import Attr


if TYPE_CHECKING:
    from nu.engine import Path, Program

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
    ACTION = "action"
    SCALAR_ACTION = "scalar_action"
    STREAM_ACTION = "stream_action"
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
    Sort.ACTION: Sort.INTERACTION,
    Sort.FLOW: Sort.INTERACTION,
    Sort.SPAN: Sort.INTERACTION,
    Sort.SCALAR_QUERY: Sort.QUERY,
    Sort.STREAM_QUERY: Sort.QUERY,
    Sort.REDUCTION: Sort.SCALAR_QUERY,
    Sort.SCALAR_COMMAND: Sort.COMMAND,
    Sort.SCALAR_ACTION: Sort.ACTION,
    Sort.STREAM_ACTION: Sort.ACTION,
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
    Sort.SCALAR_ACTION,
    Sort.STREAM_ACTION,
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


# Child sorts that produce a value, and child sorts that do work. Action is the
# dual citizen, in both cardinalities: a ScalarAction or StreamAction yields (so
# joins _VALUE) and mutates Context (so joins _WORK alongside Command). A
# StreamAction yielding into a scalar slot is gated by the cardinality law, not
# here, the same way a StreamQuery sits in _VALUE yet a scalar consumer must
# reduce it.
_VALUE = frozenset(
    {
        Sort.REF,
        Sort.SCALAR_QUERY,
        Sort.STREAM_QUERY,
        Sort.SCALAR_ACTION,
        Sort.STREAM_ACTION,
        Sort.BRACKET,
        Sort.POLICY,
    }
)
_WORK = frozenset(
    {
        Sort.SCALAR_COMMAND,
        Sort.SCALAR_ACTION,
        Sort.STREAM_ACTION,
        Sort.STRATEGY,
        Sort.CONTROL,
        Sort.BRACKET,
        Sort.POLICY,
    }
)
_ANY = _VALUE | _WORK

# The composition matrix: each parent sort mapped to the child sorts it holds.
# A value-producing parent holds values; a Strategy holds work; the parents
# that take a body (Control, Bracket, Policy) hold anything. Action's slots
# need values (the payload, the address) like Command's do, in either cardinality.
MATRIX: dict[Sort, frozenset[Sort]] = {
    Sort.REF: _VALUE,
    Sort.SCALAR_QUERY: _VALUE,
    Sort.STREAM_QUERY: _VALUE,
    Sort.SCALAR_COMMAND: _VALUE,
    Sort.SCALAR_ACTION: _VALUE,
    Sort.STREAM_ACTION: _VALUE,
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
