"""POC 3: ANSI color-coded tree display.

Full color coding by node category for rich terminal output.
Uses duck-typing (hasattr checks) to detect node categories
without importing from other everybase modules.

Color scheme:
    Values (literals)   : cyan
    Values (computed)   : dim cyan
    Refs                : yellow
    Pure ops (Calculation): green
    Impure ops (Command): red
    Flows               : blue
    Spans               : magenta/bold
    Connectors          : dim
    Nu names          : bold (within their color)
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
CYAN = "\033[36m"  # Values (literal)
DIM_CYAN = "\033[2;36m"  # Values (computed / wrapping children)
YELLOW = "\033[33m"  # Refs
GREEN = "\033[32m"  # Pure ops (Operations)
RED = "\033[31m"  # Impure ops (Commands)
BLUE = "\033[34m"  # Flows
MAGENTA_BOLD = "\033[1;35m"  # Spans

# Purity indicators
PURE_DOT = f"{GREEN}\u25cf{RESET}"  # filled circle, green
IMPURE_DOT = f"{RED}\u25c6{RESET}"  # filled diamond, red


# =============================================================================
# NODE CATEGORIZATION (duck-typed, no imports)
# =============================================================================


def _is_span(node: Nu) -> bool:
    """Span nodes have enter/exit lifecycle methods."""
    return (
        hasattr(node, "enter") and hasattr(node, "exit_success") and hasattr(node, "exit_failure")
    )


def _is_flow(node: Nu) -> bool:
    """Flow nodes have execute but NOT enter/exit (that's Span)."""
    # Flow is an Nu that is neither Nu nor Span.
    # Flows don't have is_self_pure (that's Nu) and don't have enter (that's Span).
    return hasattr(node, "execute") and not hasattr(node, "is_self_pure") and not _is_span(node)


def _is_ref(node: Nu) -> bool:
    """Refs have resolve and fetch methods."""
    return hasattr(node, "resolve") and hasattr(node, "fetch")


def _is_value(node: Nu) -> bool:
    """Values have source OR are Value subclass (is_self_pure True, not op)."""
    # Values have is_self_pure = True and no apply method (ops have apply).
    return hasattr(node, "is_self_pure") and not hasattr(node, "apply") and not _is_ref(node)


def _is_op(node: Nu) -> bool:
    """Ops have an apply method."""
    return hasattr(node, "apply") or hasattr(node, "_func") or hasattr(node, "_method_name")


def _is_pure(node: Nu) -> bool:
    """Check if a node is pure (Calculation mixin)."""
    if hasattr(node, "is_self_pure"):
        return node.is_self_pure
    return True


# =============================================================================
# LABEL FORMATTING
# =============================================================================


def _get_category_color(node: Nu) -> str:
    """Determine the ANSI color for a node based on its category."""
    if _is_span(node):
        return MAGENTA_BOLD
    if _is_flow(node):
        return BLUE
    if _is_ref(node):
        return YELLOW
    if _is_op(node):
        return GREEN if _is_pure(node) else RED
    if _is_value(node):
        # Literal values (leaf with source) get bright cyan;
        # computed values (wrapping children) get dim cyan.
        if hasattr(node, "source") and node.is_leaf:
            return CYAN
        return DIM_CYAN
    # Fallback: no special color
    return ""


def _format_span_label(node: Nu) -> str:
    """Format label for Span nodes: Atomic[ScopeName]."""
    cls = type(node).__name__
    if hasattr(node, "scope") and node.scope is not None:
        scope = node.scope
        scope_name = scope.__name__ if hasattr(scope, "__name__") else str(scope)
        return f"{cls}[{scope_name}]"
    return cls


def _format_ref_label(node: Nu) -> str:
    """Format label for Ref nodes: IntRef@'address'."""
    cls = type(node).__name__

    # Try to get address from the address property or children[0]
    addr_repr = None
    if hasattr(node, "address"):
        addr = node.address
        # If address is itself a Value leaf with source, show the source
        if hasattr(addr, "source") and hasattr(addr, "is_leaf") and addr.is_leaf:
            addr_repr = repr(addr.source)
        elif hasattr(addr, "source"):
            addr_repr = repr(addr.source)

    # Try to show parent chain (shape info)
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


def _format_value_label(node: Nu) -> str:
    """Format label for Value nodes: IntI(42) or IntI."""
    cls = type(node).__name__
    if hasattr(node, "source") and node.is_leaf:
        src = node.source
        return f"{cls}({src!r})"
    return cls


def _format_op_label(node: Nu) -> str:
    """Format label for op nodes: .method_name or func_name."""
    cls = type(node).__name__

    # MethodCall nodes
    if hasattr(node, "_method_name"):
        return f"{cls}(.{node._method_name})"

    # FuncCall nodes
    if hasattr(node, "_func"):
        func = node._func
        fname = getattr(func, "__name__", repr(func))
        return f"{cls}({fname})"

    return cls


def _default_label(node: Nu, *, color: bool = True) -> str:
    """Build a color-coded label for a node.

    Args:
        node: Tree node to label.
        color: Whether to emit ANSI escape codes.

    Returns:
        Formatted label string.
    """
    # Determine raw text label
    if _is_span(node):
        text = _format_span_label(node)
    elif _is_flow(node):
        text = type(node).__name__
    elif _is_ref(node):
        text = _format_ref_label(node)
    elif _is_op(node):
        text = _format_op_label(node)
    elif _is_value(node):
        text = _format_value_label(node)
    else:
        text = type(node).__name__

    if not color:
        # Plain text -- add purity indicator for ops only
        if _is_op(node):
            indicator = "\u25cf" if _is_pure(node) else "\u25c6"
            return f"{indicator} {text}"
        return text

    # Colorized output
    cat_color = _get_category_color(node)

    # Bold the class name portion within the color
    if cat_color:
        colored_text = f"{cat_color}{BOLD}{text}{RESET}"
    else:
        colored_text = f"{BOLD}{text}{RESET}"

    # Add purity indicator for op nodes
    if _is_op(node):
        if _is_pure(node):
            colored_text = f"{PURE_DOT} {colored_text}"
        else:
            colored_text = f"{IMPURE_DOT} {colored_text}"

    return colored_text


# =============================================================================
# TREE CONNECTORS
# =============================================================================

# Box-drawing characters for tree connectors
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
                # Extend the prefix based on whether we're the last child
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
