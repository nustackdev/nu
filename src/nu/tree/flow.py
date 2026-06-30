"""Flow-aware wrapping primitives.

Generic, semantically-aware tools for injecting wrappers (Brackets,
Policies, instrumentation) at the natural unit of mutation: the Flow.
No fabric or boundary knowledge — wrappers and predicates are
caller-provided. Effect analysis (which Refs a subtree touches) lives
in the sibling ``effects`` module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Flow


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu


__all__ = [
    "is_flow",
    "wrap_flow_children",
    "wrap_flows",
]


def is_flow(node: Nu) -> bool:
    """Predicate: node is a Flow."""
    return isinstance(node, Flow)


def wrap_flows(
    tree: Nu,
    wrapper: Callable[[Nu], Nu],
    *,
    predicate: Callable[[Nu], bool] | None = None,
) -> Nu:
    """Wrap outermost Flow nodes with ``wrapper(flow)``.

    Walks top-down. When a Flow (matching ``predicate`` if given) is
    found, calls ``wrapper(flow)`` and does not recurse inside — that
    subtree is claimed whole. Non-matching nodes are recursed into.

    Use this to inject one boundary per outermost unit of mutation,
    respecting the algebraic structure already present in the tree.
    """

    def _walk(node: Nu) -> Nu:
        if isinstance(node, Flow) and (predicate is None or predicate(node)):
            return wrapper(node)
        if not node.children:
            return node
        new_children = tuple(_walk(c) for c in node.children)
        if all(n is o for n, o in zip(new_children, node.children, strict=True)):
            return node
        return node.with_children(*new_children)

    return _walk(tree)


def wrap_flow_children(
    tree: Nu,
    wrapper: Callable[[Nu], Nu],
    *,
    descend: Callable[[Nu], bool] | None = None,
) -> Nu:
    """At each Flow node, replace every direct child with ``wrapper(child)``.

    Walk is bottom-up: inner Flows are processed before outer ones, so
    by the time the outer Flow is reached, its inner Flow children
    already carry their per-branch wraps.

    The Flow node itself is unchanged in shape — only its children are
    swapped. Use this when the boundary unit is the Flow's branch, not
    the Flow as a whole.

    ``descend``: optional predicate. If it returns ``False`` for a node,
    that subtree is treated as opaque — recursion stops there. Use this
    to keep existing wrappers (e.g. Brackets) intact while still letting
    the outer Flow wrap them as a whole.
    """

    def _walk(node: Nu) -> Nu:
        if descend is not None and not descend(node):
            return node
        if not node.children:
            return node
        new_children = tuple(_walk(c) for c in node.children)
        if all(n is o for n, o in zip(new_children, node.children, strict=True)):
            new_node = node
        else:
            new_node = node.with_children(*new_children)
        if isinstance(new_node, Flow):
            wrapped = tuple(wrapper(c) for c in new_node.children)
            if any(w is not c for w, c in zip(wrapped, new_node.children, strict=True)):
                return new_node.with_children(*wrapped)
        return new_node

    return _walk(tree)
