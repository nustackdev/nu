"""Nu tree rendering -- ANSI, plain, or HTML.

Color coding by node category for ANSI. Duck-typed node classification
with no imports from other Nu modules.

ANSI color scheme:
    Literals             : cyan
    Literals (computed)  : dim cyan
    Refs                 : yellow
    Ops                  : green
    Connectors           : dim
    Nu names             : bold (within their color)
"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import TYPE_CHECKING, Any, Literal


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.terms import Nu


__all__ = ["render_nu"]


# ── ANSI escape codes ─────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

CYAN = "\033[36m"
DIM_CYAN = "\033[2;36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"

PURE_DOT = f"{GREEN}\u25cf{RESET}"


# ── Node categorization (duck-typed, no imports) ─────────────────────────────


def _is_span(node: Any) -> bool:
    return (
        hasattr(node, "enter") and hasattr(node, "exit_success") and hasattr(node, "exit_failure")
    )


def _is_flow(node: Any) -> bool:
    return (
        hasattr(node, "run")
        and not hasattr(node, "apply")
        and not hasattr(node, "is_self_pure")
        and not _is_span(node)
    )


def _is_ref(node: Any) -> bool:
    return hasattr(node, "resolve") and hasattr(node, "fetch")


def _is_value(node: Any) -> bool:
    return hasattr(node, "is_self_pure") and not hasattr(node, "apply") and not _is_ref(node)


def _is_literal(node: Any) -> bool:
    """Literals have a source attribute, no apply method, not a Ref."""
    return hasattr(node, "source") and not hasattr(node, "apply") and not _is_ref(node)


def _is_op(node: Any) -> bool:
    return hasattr(node, "apply") or hasattr(node, "_func") or hasattr(node, "_method_name")


def _is_morphism(node: Any) -> bool:
    return _is_op(node)


def _is_pure(node: Any) -> bool:
    if hasattr(node, "is_self_pure"):
        return node.is_self_pure
    return True


def _classify_html(node: Any) -> str:
    if _is_span(node):
        return "span"
    if _is_flow(node):
        return "flow"
    if _is_ref(node):
        return "ref"
    if _is_morphism(node):
        return "op" if _is_pure(node) else "cmd"
    if _is_value(node):
        return "value"
    return "value"


# ── ANSI labels ───────────────────────────────────────────────────────────────


def _get_category_color(node: Any) -> str:
    if _is_ref(node):
        return YELLOW
    if _is_op(node):
        return GREEN
    if _is_literal(node):
        if hasattr(node, "source") and node._is_leaf:
            return CYAN
        return DIM_CYAN
    return ""


def _format_ref_label(node: Any) -> str:
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


def _format_literal_label(node: Any) -> str:
    cls = type(node).__name__
    if hasattr(node, "source") and node._is_leaf:
        src = node.source
        return f"{cls}({src!r})"
    return cls


def _format_op_label(node: Any) -> str:
    cls = type(node).__name__
    if hasattr(node, "_method_name"):
        return f"{cls}(.{node._method_name})"
    if hasattr(node, "_func"):
        func = node._func
        fname = getattr(func, "__name__", repr(func))
        return f"{cls}({fname})"
    return cls


def _default_label(node: Any, *, color: bool = True) -> str:
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


# ── Tree connectors ──────────────────────────────────────────────────────────

CONNECTOR_BRANCH = "\u251c\u2500\u2500"
CONNECTOR_LAST = "\u2514\u2500\u2500"
CONNECTOR_PIPE = "\u2502  "
CONNECTOR_SPACE = "   "


def _dim(text: str, *, color: bool = True) -> str:
    if color:
        return f"{DIM}{text}{RESET}"
    return text


def _render_ansi(
    root: Nu,
    *,
    label: Callable[[Nu], str] | None = None,
    color: bool = True,
) -> str:
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


# ── HTML labels + attrs ──────────────────────────────────────────────────────


def _html_label(node: Any) -> str:
    cls = type(node).__name__

    if _is_span(node):
        if hasattr(node, "shape"):
            shape = node.shape
            shape_name = shape.__name__ if hasattr(shape, "__name__") else str(shape)
            return f"{cls}[{shape_name}]"
        return cls

    if _is_ref(node):
        addr_repr = None
        if hasattr(node, "address"):
            addr = node.address
            if hasattr(addr, "source"):
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

    if _is_morphism(node):
        if hasattr(node, "_method_name"):
            return f"{cls}(.{node._method_name})"
        if hasattr(node, "_func"):
            func = node._func
            fname = getattr(func, "__name__", repr(func))
            return f"{cls}({fname})"
        return cls

    if _is_value(node):
        if hasattr(node, "source") and node._is_leaf:
            return f"{cls}({node.source!r})"
        return cls

    return cls


def _html_attrs(node: Any) -> dict[str, Any]:
    attrs: dict[str, Any] = {}

    if hasattr(node, "shape"):
        shape = node.shape
        attrs["shape"] = shape.__name__ if hasattr(shape, "__name__") else str(shape)

    if hasattr(node, "owner_shape") and node.owner_shape is not None:
        attrs["owner_shape"] = node.owner_shape.__name__

    if hasattr(node, "address"):
        addr = node.address
        if hasattr(addr, "source"):
            attrs["address"] = repr(addr.source)

    if hasattr(node, "_method_name"):
        attrs["method"] = node._method_name

    if hasattr(node, "_func"):
        func = node._func
        attrs["func"] = getattr(func, "__name__", repr(func))

    if hasattr(node, "source") and node._is_leaf:
        attrs["source"] = repr(node.source)

    if hasattr(node, "is_self_pure"):
        attrs["purity"] = "pure" if node.is_self_pure else "impure"

    if hasattr(node, "_view_cls"):
        attrs["view_cls"] = node._view_cls.__name__

    if hasattr(node, "_kwarg_keys"):
        attrs["kwarg_keys"] = list(node._kwarg_keys)

    if hasattr(node, "_case_keys"):
        attrs["case_keys"] = list(node._case_keys)

    return attrs


def _serialize(root: Any) -> dict[str, Any]:
    counter = [0]

    def _ser(node: Any) -> dict[str, Any]:
        node_id = counter[0]
        counter[0] += 1

        category = _classify_html(node)
        children = [_ser(child) for child in node.children]

        pure: bool | None = None
        if _is_morphism(node):
            pure = _is_pure(node)

        return {
            "id": node_id,
            "type": type(node).__name__,
            "category": category,
            "label": _html_label(node),
            "pure": pure,
            "leaf": node._is_leaf,
            "attrs": _html_attrs(node),
            "children": children,
        }

    return _ser(root)


def _render_html(root: Nu, *, title: str = "Nu tree explorer") -> str:
    data = _serialize(root)
    template = files("nu_inspect").joinpath("explorer.html.tmpl").read_text(encoding="utf-8")
    tree_json = json.dumps(data, indent=2)
    html = template.replace("__TREE_DATA__", tree_json)
    html = html.replace("__TREE_TITLE__", title)
    return html


# ── Public entry ──────────────────────────────────────────────────────────────


def render_nu(
    nu: Nu,
    *,
    as_: Literal["ansi", "plain", "html"] = "ansi",
    label: Callable[[Nu], str] | None = None,
    title: str = "Nu tree explorer",
) -> str:
    """Render a Nu tree as a string.

    Args:
        nu: Root node of the tree.
        as_: Output format. ``"ansi"`` (default) emits ANSI color codes,
            ``"plain"`` emits plain text, ``"html"`` emits a self-contained
            interactive HTML explorer.
        label: Custom label callable (ANSI/plain only). Ignored for ``"html"``.
        title: Page title (HTML only).

    Returns:
        Multi-line string (ANSI/plain) or full HTML document.
    """
    if as_ == "html":
        return _render_html(nu, title=title)
    color = as_ == "ansi"
    return _render_ansi(nu, label=label, color=color)
