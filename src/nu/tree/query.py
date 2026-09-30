"""Tree queries -- read-only inspection of Term structures.

Domain-free: predicates and counts over any Term tree.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Term

from .walk import preorder


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from nu.lang import Nu


__all__ = [
    "children",
    "count",
    "depth",
    "equal",
    "find",
    "find_first",
    "payload",
    "size",
]


def find(root: Nu, pred: Callable[[Nu], bool]) -> list[Nu]:
    """Find all nodes matching predicate (pre-order)."""
    return [node for node in preorder(root) if pred(node)]


def find_first(root: Nu, pred: Callable[[Nu], bool]) -> Nu | None:
    """Find first matching node (pre-order), or None."""
    for node in preorder(root):
        if pred(node):
            return node
    return None


def count(root: Nu, pred: Callable[[Nu], bool] | None = None) -> int:
    """Count nodes matching predicate. ``None`` counts all."""
    if pred is None:
        return sum(1 for _ in preorder(root))
    return sum(1 for node in preorder(root) if pred(node))


def size(root: Nu) -> int:
    """Total number of nodes."""
    return count(root)


def depth(root: Nu) -> int:
    """Maximum depth. A leaf has depth 0."""
    if not root._children:
        return 0
    return 1 + max(depth(c) for c in root._children)


def children(node: Nu) -> tuple[Nu, ...]:
    """The node's direct children, in slot order."""
    return node._children


def payload(node: Nu) -> Mapping[str, object]:
    """The node's construction data: what it holds besides its children.

    Read-only by contract. A rewrite that keeps a node's payload shares it,
    so two variants of one node report the same mapping.
    """
    return node._payload


def equal(a: object, b: object) -> bool:
    """Structural equality: same kinds, same payloads, same children, recursively.

    The explicit spelling of "these two trees are the same program". ``==`` on
    a term builds a comparison term (on a Form) or raises (on a bare term), so
    it never answers this. Plain values in payloads compare by type and
    ``==``; terms anywhere inside them (a body held in a payload, a case
    table) compare structurally.
    """
    if a is b:
        return True
    if type(a) is not type(b):
        return False
    if isinstance(a, Term) and isinstance(b, Term):
        return equal(a._children, b._children) and equal(a._payload, b._payload)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b, strict=True))
    return bool(a == b)
