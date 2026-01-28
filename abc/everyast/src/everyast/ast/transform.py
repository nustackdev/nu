"""Tree transforms -- structural tree-to-tree operations.

Transforms are Node -> Node functions. They modify tree shape.
All operations are non-mutating (return new trees).

Key design: map_children uses with_children() -- no type dispatch.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeAlias


if TYPE_CHECKING:
    from collections.abc import Callable

    from .node import Node

Transform: TypeAlias = "Callable[[Node], Node]"  # noqa: UP040
"""A tree transform: takes a node tree and returns a new node tree."""

__all__ = [
    "Transform",
    "apply",
    "compose",
    "graft",
    "map_children",
    "map_nodes",
    "prune",
    "replace",
    "unwrap",
    "wrap",
]


def compose(*transforms: Transform) -> Transform:
    """Compose transforms left-to-right.

    compose(f, g)(x) == g(f(x)).
    """

    def composed(root: Node) -> Node:
        for t in transforms:
            root = t(root)
        return root

    return composed


def apply(root: Node, *transforms: Transform) -> Node:
    """Apply transforms in order to root."""
    for t in transforms:
        root = t(root)
    return root


def map_children(node: Node, fn: Callable[[Node], Node]) -> Node:
    """Apply fn to each direct child, reconstruct via with_children.

    Shallow (one level). For deep transforms, use map_nodes.
    """
    if node.is_leaf:
        return node
    return node.with_children(*(fn(c) for c in node.children))


def map_nodes(
    root: Node,
    fn: Callable[[Node], Node],
    order: Literal["bottom_up", "top_down"] = "bottom_up",
) -> Node:
    """Apply fn to every node in the tree.

    Args:
        root: Tree root.
        fn: Function applied to each node.
        order: "bottom_up" (default) transforms children first,
               "top_down" transforms parent first.
    """
    if order == "top_down":
        node = fn(root)
        if node.is_leaf:
            return node
        return node.with_children(*(map_nodes(c, fn, order) for c in node.children))
    # bottom_up
    if not root.is_leaf:
        root = root.with_children(*(map_nodes(c, fn, order) for c in root.children))
    return fn(root)


def replace(
    root: Node,
    pred: Callable[[Node], bool],
    replacement: Callable[[Node], Node],
) -> Node:
    """Replace nodes matching pred with replacement(node). Bottom-up."""

    def _replace(node: Node) -> Node:
        return replacement(node) if pred(node) else node

    return map_nodes(root, _replace, order="bottom_up")


def wrap(
    root: Node,
    pred: Callable[[Node], bool],
    wrapper: Callable[[Node], Node],
) -> Node:
    """Wrap nodes matching pred: node -> wrapper(node). Bottom-up."""

    def _wrap(node: Node) -> Node:
        return wrapper(node) if pred(node) else node

    return map_nodes(root, _wrap, order="bottom_up")


def unwrap(
    root: Node,
    pred: Callable[[Node], bool],
) -> Node:
    """Remove single-child wrapper nodes matching pred, splicing child up."""

    def _process(node: Node) -> Node:
        if node.is_leaf:
            return node
        new_children: list[Node] = []
        for child in node.children:
            processed = _process(child)
            if pred(processed) and processed.child_count == 1:
                new_children.append(processed.children[0])
            else:
                new_children.append(processed)
        return node.with_children(*new_children)

    return _process(root)


def graft(root: Node, target: Node, subtree: Node) -> Node:
    """Replace target node with subtree (identity comparison)."""
    return replace(root, lambda n: n is target, lambda _: subtree)


def prune(root: Node, pred: Callable[[Node], bool]) -> Node | None:
    """Remove subtrees matching pred. Returns None if root matches.

    Preserves unchanged subtrees by identity.
    """
    if pred(root):
        return None

    if root.is_leaf:
        return root

    new_children: list[Node] = []
    for child in root.children:
        pruned = prune(child, pred)
        if pruned is not None:
            new_children.append(pruned)

    if len(new_children) == len(root.children):
        if all(n is o for n, o in zip(new_children, root.children, strict=True)):
            return root
    return root.with_children(*new_children)
