"""Tree display -- pretty-printing for term trees."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable

    from ..tree import Node


__all__ = [
    "format_tree",
    "print_tree",
]


def _default_label(node: Node) -> str:
    """Default label: ClassName or repr for leaf nodes with useful info."""
    cls = type(node).__name__

    # Show source value for leaf Value nodes
    if hasattr(node, "_source") and node.is_leaf:
        src = node._source
        if not isinstance(src, type(node).__mro__[0]) and not hasattr(src, "children"):
            return f"{cls}({src!r})"

    # Show method name for MethodCall nodes
    if hasattr(node, "_method_name"):
        name = node._method_name
        return f"{cls}(.{name})"

    # Show func name for FuncCall nodes
    if hasattr(node, "_func"):
        func = node._func
        fname = getattr(func, "__name__", repr(func))
        return f"{cls}({fname})"

    return cls


def format_tree(
    root: Node,
    *,
    label: Callable[[Node], str] | None = None,
    indent: str = "  ",
) -> str:
    """Format a tree as an indented string.

    Args:
        root: Root node of the tree.
        label: Callable to produce a label for each node.
               Defaults to class name with useful details.
        indent: Indentation string per level.

    Returns:
        Multi-line string representation.
    """
    get_label = label or _default_label
    lines: list[str] = []

    def _walk(node: Node, prefix: str, connector: str) -> None:
        lines.append(f"{prefix}{connector}{get_label(node)}")
        children = node.children
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            if prefix:
                child_prefix = prefix.replace("├─", "│ ").replace("└─", "  ")
            else:
                child_prefix = prefix
            child_connector = "└─" if is_last else "├─"
            _walk(child, child_prefix + indent, child_connector)

    _walk(root, "", "")
    return "\n".join(lines)


def print_tree(
    root: Node,
    *,
    label: Callable[[Node], str] | None = None,
    indent: str = "  ",
) -> None:
    """Print a tree with box-drawing connectors.

    Args:
        root: Root node of the tree.
        label: Callable to produce a label for each node.
               Defaults to class name with useful details.
        indent: Indentation string per level.
    """
    print(format_tree(root, label=label, indent=indent))  # noqa: T201
