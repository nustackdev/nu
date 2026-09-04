"""Span transparency laws: a Span wraps a body and forwards its yield.

A Span has a body; the Span's resolved cardinality matches the body's
resolved cardinality. Most Span constraints follow from the composition
matrix walk treating Span as transparent; this module hosts what's left.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Law, predicate
from nu.lang.attributes import Attr, Sort

from .predicates import child_paths, has_children, of_sort


if TYPE_CHECKING:
    from nu.engine import Path, Program


__all__ = ["LAWS"]


@predicate
def has_body(program: Program, path: Path) -> bool:
    """Holds when the Span has at least one child (its body slot)."""
    return bool(child_paths(program, path))


@predicate
def cardinality_matches_body(program: Program, path: Path) -> bool:
    """Holds when the Span's child_cardinality equals the body's."""
    children = child_paths(program, path)
    if not children:
        return True
    own = program.attr(path, Attr.CHILD_CARDINALITY)
    body = program.attr(children[0], Attr.CHILD_CARDINALITY)
    return own is body


def cardinality_detail(program: Program, path: Path) -> str:
    """Name the Span's declared cardinality and the body's actual one."""
    children = child_paths(program, path)
    own = program.attr(path, Attr.CHILD_CARDINALITY)
    body = program.attr(children[0], Attr.CHILD_CARDINALITY)
    return f"a Span's declared body cardinality '{own}' does not match body's actual '{body}'"


LAWS: tuple[Law, ...] = (
    Law(
        "span_has_body",
        scope=of_sort(Sort.SPAN),
        holds=has_body,
        message="a Span has no body",
    ),
    Law(
        "span_cardinality_matches_body",
        scope=of_sort(Sort.SPAN) & has_children,
        holds=cardinality_matches_body,
        message=cardinality_detail,
    ),
)
