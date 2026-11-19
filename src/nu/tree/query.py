"""Tree queries -- read-only inspection of Term structures.

Domain-free: predicates and counts over any Term tree.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Term

from .walk import preorder


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu


__all__ = [
    "children",
    "count",
    "depth",
    "equal",
    "fields",
    "find",
    "find_first",
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


_NOT_FIELDS = frozenset({"_children", "_frozen"})
"""Instance attributes that are not fields: the child tuple and the freeze flag."""


def fields(node: Term) -> dict[str, object]:
    """The node's fields: what it holds besides its children.

    Every instance attribute a kind sets in ``__init__`` (a Literal's
    ``value``, a Ref's ``owner_shape``, a Raise's ``exc_cls``). Fields are
    frozen by convention, so the returned dict is a fresh snapshot; changing
    it does not change the node. Build a variant with ``node.evolve(**fields)``.

    Example:
        >>> nu.tree.fields(nu.Literal(42))
        {'value': 42}
    """
    return {k: v for k, v in vars(node).items() if k not in _NOT_FIELDS}


def equal(a: object, b: object) -> bool:
    """Structural equality: same kinds, same fields, same children, recursively.

    The explicit spelling of "these two trees are the same program". ``==`` on
    a term builds a comparison term (on a Form) or raises (on a bare term), so
    it never answers this. Plain values in fields compare by type and ``==``;
    terms anywhere inside them (a Literal holding a body, a case table)
    compare structurally.
    """
    if a is b:
        return True
    if type(a) is not type(b):
        return False
    if isinstance(a, Term) and isinstance(b, Term):
        return equal(a._children, b._children) and equal(fields(a), fields(b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b, strict=True))
    return bool(a == b)
