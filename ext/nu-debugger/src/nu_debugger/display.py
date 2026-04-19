"""ANSI color-coded tree display.

Color coding by node category for rich terminal output.
Uses duck-typing (hasattr checks) to detect node categories
without importing from other Nu modules.

Color scheme:
    Literals             : cyan
    Literals (computed)  : dim cyan
    Refs                 : yellow
    Ops                  : green
    Connectors           : dim
    Nu names             : bold (within their color)
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.terms import Nu


__all__ = [
    "format_tree",
    "print_tree",
]


# =============================================================================
# ANSI ESCAPE CODES
# =============================================================================

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Category colors
CYAN = "\033[36m"  # Literals
DIM_CYAN = "\033[2;36m"  # Literals (computed / wrapping children)
YELLOW = "\033[33m"  # Refs
GREEN = "\033[32m"  # Ops

# Op indicator
PURE_DOT = f"{GREEN}\u25cf{RESET}"  # filled circle, green


# =============================================================================
# NODE CATEGORIZATION (duck-typed, no imports)
# =============================================================================


def _is_ref(node: Nu) -> bool:
    """Refs have resolve and fetch methods."""
    return hasattr(node, "resolve") and hasattr(node, "fetch")


def _is_literal(node: Nu) -> bool:
    """Literals have a source attribute, no apply method, not a Ref."""
    return hasattr(node, "source") and not hasattr(node, "apply") and not _is_ref(node)


def _is_op(node: Nu) -> bool:
    """Ops have an apply method."""
    return hasattr(node, "apply") or hasattr(node, "_func") or hasattr(node, "_method_name")


# =============================================================================
# LABEL FORMATTING
# =============================================================================


def _get_category_color(node: Nu) -> str:
    """Determine the ANSI color for a node based on its category."""
    if _is_ref(node):
        return YELLOW
    if _is_op(node):
        return GREEN
    if _is_literal(node):
        if hasattr(node, "source") and node._is_leaf:
            return CYAN
        return DIM_CYAN
    return ""


def _format_ref_label(node: Nu) -> str:
    """Format label for Ref nodes: IntRef@'address'."""
    cls = type(node).__name__

    addr_repr = None
    if hasattr(node, "address"):
        addr = node.address
        if hasattr(addr, "source") and hasattr(addr, "is_leaf") and addr._is_leaf:
            addr_repr = repr(addr.source)
        elif hasattr(addr, "source"):
            addr_repr = repr(addr.source)

    shape_str = ""
    if hasattr(node, "owner_shape") and node.owner_shape is not None:
        shape_str = f"[{node.owner_shape.__name__}]"
    elif hasattr(node, "get_root_shape"):
        try:
            root_shape = node.get_root_shape()
            if root_shape is not None:
                shape_str = f"[{root_shape.__name__}]"
        except Exception:  # noqa: S110
            pass

    if addr_repr:
        return f"{cls}{shape_str}@{addr_repr}"
    return f"{cls}{shape_str}"


def _format_literal_label(node: Nu) -> str:
    """Format label for Literal nodes: IntI(42) or IntI."""
    cls = type(node).__name__
    if hasattr(node, "source") and node._is_leaf:
        src = node.source
        return f"{cls}({src!r})"
    return cls


def _format_op_label(node: Nu) -> str:
    """Format label for Op nodes: .method_name or func_name."""
    cls = type(node).__name__

    if hasattr(node, "_method_name"):
        return f"{cls}(.{node._method_name})"

    if hasattr(node, "_func"):
        func = node._func
        fname = getattr(func, "__name__", repr(func))
        return f"{cls}({fname})"

    return cls


def _default_label(node: Nu, *, color: bool = True) -> str:
    """Build a color-coded label for a node."""
    if _is_ref(node):
        text = _format_ref_label(node)
    elif _is_op(node):
        text = _format_op_label(node)
    elif _is_literal(node):
        text = _format_literal_label(node)
    else:
        text = type(node).__name__

    if not color:
        if _is_op(node):
            return f"\u25cf {text}"
        return text

    cat_color = _get_category_color(node)

    if cat_color:
        colored_text = f"{cat_color}{BOLD}{text}{RESET}"
    else:
        colored_text = f"{BOLD}{text}{RESET}"

    if _is_op(node):
        colored_text = f"{PURE_DOT} {colored_text}"

    return colored_text


# =============================================================================
# TREE CONNECTORS
# =============================================================================

CONNECTOR_BRANCH = "\u251c\u2500\u2500"  # "├──"
CONNECTOR_LAST = "\u2514\u2500\u2500"  # "└──"
CONNECTOR_PIPE = "\u2502  "  # "│  "
CONNECTOR_SPACE = "   "  # "   "


def _dim(text: str, *, color: bool = True) -> str:
    """Wrap text in dim ANSI if color enabled."""
    if color:
        return f"{DIM}{text}{RESET}"
    return text


# =============================================================================
# PUBLIC API
# =============================================================================


def format_tree(
    root: Nu,
    *,
    label: Callable[[Nu], str] | None = None,
    indent: str = "  ",
    color: bool = True,
) -> str:
    """Format a tree as a color-coded string with box-drawing connectors.

    Args:
        root: Root node of the tree.
        label: Custom callable to produce a label for each node.
               When provided, disables built-in color logic (labels are used as-is).
        indent: Extra indentation string per level (added after connector).
        color: Whether to emit ANSI escape codes. Defaults to True.

    Returns:
        Multi-line string representation.
    """
    lines: list[str] = []

    def _get_label(node: Nu) -> str:
        if label is not None:
            return label(node)
        return _default_label(node, color=color)

    def _walk(node: Nu, prefix: str, connector: str, is_root: bool = False) -> None:
        node_label = _get_label(node)

        if is_root:
            lines.append(node_label)
        else:
            dim_connector = _dim(connector, color=color)
            lines.append(f"{prefix}{dim_connector} {node_label}")

        children = node.children
        child_count = len(children)

        for i, child in enumerate(children):
            is_last = i == child_count - 1

            if is_root:
                child_prefix = ""
                child_connector = CONNECTOR_LAST if is_last else CONNECTOR_BRANCH
            else:
                if connector == CONNECTOR_LAST:
                    child_prefix = prefix + CONNECTOR_SPACE
                else:
                    child_prefix = prefix + _dim(CONNECTOR_PIPE, color=color)

                child_connector = CONNECTOR_LAST if is_last else CONNECTOR_BRANCH

            _walk(child, child_prefix, child_connector)

    _walk(root, "", "", is_root=True)
    return "\n".join(lines)


def print_tree(
    root: Nu,
    *,
    label: Callable[[Nu], str] | None = None,
    indent: str = "  ",
    color: bool = True,
) -> None:
    """Print a tree with ANSI color-coded labels and box-drawing connectors.

    Args:
        root: Root node of the tree.
        label: Custom callable to produce a label for each node.
        indent: Extra indentation string per level.
        color: Whether to emit ANSI escape codes. Defaults to True.
    """
    print(format_tree(root, label=label, indent=indent, color=color))  # noqa: T201
