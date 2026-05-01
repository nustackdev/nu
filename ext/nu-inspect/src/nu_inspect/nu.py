"""Nu tree rendering -- ANSI, plain, or HTML.

Classification follows the current Nu kind model (see
`projects/nu/model/02-atoms`). Each node is one of:

    Ref        - address atom              (yellow)
    Literal    - trivial scalar Query      (cyan / dim cyan)
    Query      - non-Literal Query         (green)
    Command    - mutating atom             (red)
    Flow       - composer (Strategy/Control) (blue)
    Span       - transparent (Bracket/Policy) (magenta)

Classification is via isinstance against the kind classes from
`nu.terms`. No duck-typing on private attributes.
"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import TYPE_CHECKING, Any
from typing import Literal as TLiteral

from nu.queries.literal import Literal
from nu.terms import (
    Bracket,
    Command,
    Flow,
    Policy,
    Query,
    Ref,
    Span,
    Strategy,
)


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.terms import Nu


__all__ = ["render_nu"]


# -- ANSI escape codes --------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

CYAN = "\033[36m"
DIM_CYAN = "\033[2;36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"

PURE_DOT = f"{GREEN}●{RESET}"


# -- Classification (isinstance against the kind classes) ---------------------


def _is_literal(node: Any) -> bool:
    return isinstance(node, Literal)


def _is_ref(node: Any) -> bool:
    return isinstance(node, Ref)


def _is_query(node: Any) -> bool:
    return isinstance(node, Query)


def _is_command(node: Any) -> bool:
    return isinstance(node, Command)


def _is_flow(node: Any) -> bool:
    return isinstance(node, Flow)


def _is_span(node: Any) -> bool:
    return isinstance(node, Span)


def _classify(node: Any) -> str:
    """Return one of: span, flow, ref, op, cmd, value."""
    if _is_span(node):
        return "span"
    if _is_flow(node):
        return "flow"
    if _is_ref(node):
        return "ref"
    if _is_command(node):
        return "cmd"
    if _is_literal(node):
        return "value"
    if _is_query(node):
        return "op"
    return "value"


# -- ANSI labels --------------------------------------------------------------


def _category_color(node: Any) -> str:
    if _is_span(node):
        return MAGENTA
    if _is_flow(node):
        return BLUE
    if _is_ref(node):
        return YELLOW
    if _is_command(node):
        return RED
    if _is_literal(node):
        # Trivial leaf literal vs computed (children present).
        return CYAN if not node._children else DIM_CYAN
    if _is_query(node):
        return GREEN
    return ""


def _ref_label(node: Ref) -> str:
    cls = type(node).__name__
    name = getattr(node, "name", None)
    name_repr = repr(name) if name is not None else "<dyn>"

    shape_str = ""
    owner = getattr(node, "owner_shape", None)
    if owner is not None:
        shape_str = f"[{owner.__name__}]"
    else:
        get_root = getattr(node, "get_root_shape", None)
        if callable(get_root):
            try:
                root = get_root()
            except Exception:
                root = None
            if root is not None:
                shape_str = f"[{root.__name__}]"

    return f"{cls}{shape_str}@{name_repr}"


def _literal_label(node: Literal) -> str:
    cls = type(node).__name__
    if not node._children:
        return f"{cls}({node._value!r})"
    return cls


def _invocation_suffix(node: Any) -> str:
    """Optional method/func suffix for Invoke / FuncCall / MethodCall."""
    method = getattr(node, "_method_name", None)
    if method is not None:
        return f"(.{method})"
    func = getattr(node, "_func", None)
    if func is not None:
        fname = getattr(func, "__name__", repr(func))
        return f"({fname})"
    return ""


def _kind_label(node: Any) -> str:
    return f"{type(node).__name__}{_invocation_suffix(node)}"


def _default_label(node: Any, *, color: bool = True) -> str:
    if _is_ref(node):
        text = _ref_label(node)
    elif _is_literal(node):
        text = _literal_label(node)
    else:
        text = _kind_label(node)

    if not color:
        # Mark Query (pure value-producer) with a leading dot for plain output.
        if _is_query(node) and not _is_literal(node):
            return f"● {text}"
        return text

    cat_color = _category_color(node)
    colored = f"{cat_color}{BOLD}{text}{RESET}" if cat_color else f"{BOLD}{text}{RESET}"
    if _is_query(node) and not _is_literal(node):
        colored = f"{PURE_DOT} {colored}"
    return colored


# -- Tree connectors ----------------------------------------------------------

CONNECTOR_BRANCH = "├──"
CONNECTOR_LAST = "└──"
CONNECTOR_PIPE = "│  "
CONNECTOR_SPACE = "   "


def _dim(text: str, *, color: bool = True) -> str:
    return f"{DIM}{text}{RESET}" if color else text


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

    def _walk(node: Nu, prefix: str, connector: str, *, is_root: bool = False) -> None:
        node_label = _get_label(node)
        if is_root:
            lines.append(node_label)
        else:
            lines.append(f"{prefix}{_dim(connector, color=color)} {node_label}")

        children = node._children
        last_idx = len(children) - 1
        for i, child in enumerate(children):
            is_last = i == last_idx
            if is_root:
                child_prefix = ""
            else:
                child_prefix = (
                    prefix + CONNECTOR_SPACE
                    if connector == CONNECTOR_LAST
                    else prefix + _dim(CONNECTOR_PIPE, color=color)
                )
            child_connector = CONNECTOR_LAST if is_last else CONNECTOR_BRANCH
            _walk(child, child_prefix, child_connector)

    _walk(root, "", "", is_root=True)
    return "\n".join(lines)


# -- HTML labels + attrs ------------------------------------------------------


def _html_label(node: Any) -> str:
    if _is_ref(node):
        return _ref_label(node)
    if _is_literal(node):
        return _literal_label(node)
    if _is_span(node):
        cls = type(node).__name__
        body_slot = getattr(type(node), "body_slot", None)
        if body_slot is not None and body_slot < len(node._children):
            body = node._children[body_slot]
            return f"{cls}<{type(body).__name__}>"
        return cls
    return _kind_label(node)


def _html_attrs(node: Any) -> dict[str, Any]:
    attrs: dict[str, Any] = {}

    if _is_ref(node):
        name = getattr(node, "name", None)
        if name is not None:
            attrs["name"] = name
        owner = getattr(node, "owner_shape", None)
        if owner is not None:
            attrs["owner_shape"] = owner.__name__

    if _is_literal(node) and not node._children:
        attrs["value"] = repr(node._value)

    if _is_span(node):
        body_slot = getattr(type(node), "body_slot", None)
        if body_slot is not None:
            attrs["body_slot"] = body_slot
        if isinstance(node, Bracket):
            attrs["span_kind"] = "bracket"
        elif isinstance(node, Policy):
            attrs["span_kind"] = "policy"
        else:
            attrs["span_kind"] = "span"

    if _is_flow(node):
        attrs["flow_kind"] = "strategy" if isinstance(node, Strategy) else "control"
        body_slots = getattr(type(node), "body_slots", None)
        if body_slots:
            attrs["body_slots"] = list(body_slots)

    realization = getattr(type(node), "realization", None)
    if realization is not None:
        attrs["realization"] = getattr(realization, "name", str(realization))

    own_effects = getattr(type(node), "own_effects", None)
    if own_effects:
        attrs["own_effects"] = {str(slot): _format_effect(eff) for slot, eff in own_effects.items()}

    method = getattr(node, "_method_name", None)
    if method is not None:
        attrs["method"] = method
    func = getattr(node, "_func", None)
    if func is not None:
        attrs["func"] = getattr(func, "__name__", repr(func))

    return attrs


def _format_effect(eff: Any) -> str:
    if isinstance(eff, frozenset):
        return "{" + ", ".join(getattr(e, "name", str(e)) for e in eff) + "}"
    return getattr(eff, "name", str(eff))


def _serialize(root: Any) -> dict[str, Any]:
    counter = [0]

    def _ser(node: Any) -> dict[str, Any]:
        node_id = counter[0]
        counter[0] += 1

        category = _classify(node)
        children = [_ser(child) for child in node._children]

        # `pure` flag is meaningful for value-producers: True for any Query
        # (its subtree contributes only RESOLVE/READ), False for Command/Flow
        # (Flow yields nothing but holds Commands), N/A for Span/Ref/Literal.
        pure: bool | None
        if _is_query(node) and not _is_literal(node):
            pure = True
        elif _is_command(node):
            pure = False
        else:
            pure = None

        return {
            "id": node_id,
            "type": type(node).__name__,
            "category": category,
            "label": _html_label(node),
            "pure": pure,
            "leaf": not node._children,
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


# -- Public entry -------------------------------------------------------------


def render_nu(
    nu: Nu,
    *,
    as_: TLiteral["ansi", "plain", "html"] = "ansi",
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
