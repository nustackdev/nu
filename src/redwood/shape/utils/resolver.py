"""Reference resolution utilities.

Centralized logic for resolving refs to paths and navigating trees.
Used by all operations and commands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from redwood.abc import TupleKey

    from ..evaluation import Ref
    from ..types import Context

__all__ = [
    # "get_view",
    # "navigate_to_parent",
    "resolve_ref",
]


def resolve_ref(ref: Ref, context: Context) -> TupleKey:
    """Resolve reference to concrete path segments.

    For static refs: returns cached path immediately (O(1))
    For dynamic refs: evaluates expressions to compute path

    Args:
        ref: Reference to resolve
        context: Context for evaluating dynamic components

    Returns:
        Tuple of path segments

    Example:
        >>> resolve_ref(Market.orders["AAPL"].price, ctx)
        ("orders", "AAPL", "price")
    """
    return ref.resolve(context)


# def navigate_to_parent(
#     tree: Tree,
#     path: TupleKey,
#     context: Context,
# ) -> Tree:
#     """Navigate to parent container using path segments.

#     Walks the tree using tree.at() for each segment.

#     Args:
#         tree: Root tree instance
#         path: Path segments to navigate
#         context: Context (unused, but kept for consistency)

#     Returns:
#         Tree node at the path

#     Example:
#         >>> node = navigate_to_parent(tree, ("orders", "AAPL"), ctx)
#         >>> # node is now at Market.orders["AAPL"]
#     """
#     current = tree
#     for segment in path:
#         current = current.at(segment)
#     return current


# def get_view(
#     tree: Tree,
#     view_type: type,
#     context: Context,
# ) -> View:
#     """Get view instance for a tree node.

#     Simple wrapper around tree.view() for consistency.

#     Args:
#         tree: Tree node
#         view_type: View class to instantiate
#         context: Context containing storage_context

#     Returns:
#         View instance

#     Example:
#         >>> view = get_view(node, DictView, ctx)
#         >>> value = view.get("price")
#     """
#     return tree.view(view_type, ctx=context.storage_context)
