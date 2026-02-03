"""auto_atomic — Wrap Term-only subtrees in Atomic spans."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import Span
from everybase.meta import conditional_wrap

from ..spans import Atomic


if TYPE_CHECKING:
    from pv.view import View

    from everybase import Node


__all__ = [
    "auto_atomic",
]


def _is_span_free(node: Node) -> bool:
    """True if subtree contains no Spans (only Terms and Flows)."""
    if isinstance(node, Span):
        return False
    return all(_is_span_free(c) for c in node.children)


def auto_atomic(tree: Node, shape: type, view_cls: type[View]) -> Node:
    """Wrap span-free subtrees in ``Atomic`` spans.

    Walks *tree* bottom-up. At each node, groups contiguous children
    whose subtrees are span-free (only Terms and Flows, no existing
    Spans) and wraps each group in a single
    ``Atomic(shape, view_cls, *children)``.

    This means a ``Flow(Term, Term)`` is treated as a single unit and
    wrapped together with adjacent Terms, rather than being recursed
    into and having its children wrapped individually.

    Args:
        tree: Expression tree to rewrite.
        shape: Shape class for storage context lookup.
        view_cls: View class to open on top of the storage context.

    Returns:
        New tree with Atomic spans injected.
    """

    def _wrap(children: tuple[Node, ...]) -> Atomic:
        return Atomic(shape, view_cls, *children)

    result = conditional_wrap(tree, _is_span_free, _wrap)

    # conditional_wrap leaves a matching root unchanged (no parent to
    # wrap it). If the whole tree is span-free, wrap it here.
    if _is_span_free(result):
        return _wrap((result,))

    return result
