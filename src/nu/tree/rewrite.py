"""Generic tree rewrites -- structural Term-to-Term operations.

Transforms are ``Nu -> Nu`` functions that change tree shape. All
operations are non-mutating (return new trees) and domain-free -- they
touch only ``._children`` and ``._with_children``, so they apply to any
Term tree.

Key design: child reconstruction goes through ``with_children`` -- no
type dispatch.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu


type Transform = "Callable[[Nu], Nu]"
"""A tree transform: takes a node tree and returns a new node tree."""

__all__ = [
    "Transform",
    "apply",
    "compose",
    "conditional_wrap",
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

    ``compose(f, g)(x) == g(f(x))``.
    """

    def composed(root: Nu) -> Nu:
        for t in transforms:
            root = t(root)
        return root

    return composed


def apply(root: Nu, *transforms: Transform) -> Nu:
    """Apply transforms in order to root."""
    for t in transforms:
        root = t(root)
    return root


def map_children(node: Nu, fn: Callable[[Nu], Nu]) -> Nu:
    """Apply fn to each direct child, reconstruct via ``with_children``.

    Shallow (one level). For deep transforms, use ``map_nodes``.
    """
    if not node._children:
        return node
    return node._with_children(*(fn(c) for c in node._children))


def map_nodes(
    root: Nu,
    fn: Callable[[Nu], Nu],
    order: Literal["bottom_up", "top_down"] = "bottom_up",
) -> Nu:
    """Apply fn to every node in the tree.

    Args:
        root:  Tree root.
        fn:    Function applied to each node.
        order: ``"bottom_up"`` (default) transforms children first,
               ``"top_down"`` transforms parent first.
    """
    if order == "top_down":
        node = fn(root)
        if not node._children:
            return node
        return node._with_children(*(map_nodes(c, fn, order) for c in node._children))
    # bottom_up
    if root._children:
        root = root._with_children(*(map_nodes(c, fn, order) for c in root._children))
    return fn(root)


def replace(
    root: Nu,
    pred: Callable[[Nu], bool],
    replacement: Callable[[Nu], Nu],
) -> Nu:
    """Replace nodes matching pred with ``replacement(node)``. Bottom-up."""

    def _replace(node: Nu) -> Nu:
        return replacement(node) if pred(node) else node

    return map_nodes(root, _replace, order="bottom_up")


def wrap(
    root: Nu,
    pred: Callable[[Nu], bool],
    wrapper: Callable[[Nu], Nu],
) -> Nu:
    """Wrap nodes matching pred: ``node -> wrapper(node)``. Bottom-up."""

    def _wrap(node: Nu) -> Nu:
        return wrapper(node) if pred(node) else node

    return map_nodes(root, _wrap, order="bottom_up")


def unwrap(
    root: Nu,
    pred: Callable[[Nu], bool],
) -> Nu:
    """Remove single-child wrapper nodes matching pred, splicing child up."""

    def _process(node: Nu) -> Nu:
        if not node._children:
            return node
        new_children: list[Nu] = []
        for child in node._children:
            processed = _process(child)
            if pred(processed) and len(processed._children) == 1:
                new_children.append(processed._children[0])
            else:
                new_children.append(processed)
        return node._with_children(*new_children)

    return _process(root)


def graft(root: Nu, target: Nu, subtree: Nu) -> Nu:
    """Replace target node with subtree (identity comparison)."""
    return replace(root, lambda n: n is target, lambda _: subtree)


def prune(root: Nu, pred: Callable[[Nu], bool]) -> Nu | None:
    """Remove subtrees matching pred. Returns ``None`` if root matches.

    Preserves unchanged subtrees by identity.
    """
    if pred(root):
        return None

    if not root._children:
        return root

    new_children: list[Nu] = []
    for child in root._children:
        pruned = prune(child, pred)
        if pruned is not None:
            new_children.append(pruned)

    if len(new_children) == len(root._children) and all(
        n is o for n, o in zip(new_children, root._children, strict=True)
    ):
        return root
    return root._with_children(*new_children)


def conditional_wrap(
    root: Nu,
    pred: Callable[[Nu], bool],
    wrapper: Callable[[Nu], Nu],
) -> Nu:
    """Wrap each matching child, bottom-up.

    At each node, matching children are wrapped individually via
    ``wrapper(child)``. Non-matching children are recursed into.

    Matching children are **not** recursed into -- they are claimed
    whole by the nearest non-matching ancestor, giving the biggest
    matching subtree at each level.
    """
    if pred(root) or not root._children:
        return root

    new_children: list[Nu] = []
    for child in root._children:
        if pred(child):
            new_children.append(wrapper(child))
        else:
            new_children.append(conditional_wrap(child, pred, wrapper))

    return root._with_children(*new_children)
