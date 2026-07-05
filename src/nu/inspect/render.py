"""Nu tree rendering -- an ANSI or plain box-tree of any Nu term.

The one inspection primitive: hand it a Nu tree, get back a printable string
that shows the structure, one node per line, with the kind of each node color
coded. Useful at a REPL or in a log to see what a program actually compiled to.

Classification is ``isinstance`` against the kind taxonomy (``nu.lang``); no
duck-typing on private attributes. Each node is one of:

    Ref        - a location in a fabric              (yellow)
    Literal    - the constant-yielding Query          (cyan / dim cyan)
    Query      - a non-Literal value producer          (green, marked with a dot)
    Command    - a mutating kind, yields nothing       (red)
    Action     - a mutating kind that also yields       (bright red)
    Flow       - a composer of mutating kinds            (blue; Strategy / Control)
    Span       - a transparent wrapper                   (magenta; Bracket / Policy)

The green dot on a non-Literal Query marks a **value producer**: a kind that
yields a computed value and contributes no WRITE. It is not a purity or
foldability claim - a Query may still READ through a Ref (impure), and even an
effect-free Query (``uuid4``, ``now``) is not foldable unless it is also
``deterministic``. Effect vs determinism are distinct: an effect is a READ or
WRITE through a Ref, purity is empty composition effects, foldability is pure
AND deterministic. This printer surfaces kind only; it makes no such claims.

Only the ANSI and plain string forms live here; there is no HTML explorer.
``render_nu`` renders the *tree*; rendering a Shape's backing storage is a
separate primitive, ``nu.inspect.render_shape``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from typing import Literal as TLiteral

from nu.core.literal import LiteralQuery
from nu.lang import Action, Command, Flow, Query, Ref, Span


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu


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
BRIGHT_RED = "\033[91m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"

VALUE_DOT = f"{GREEN}●{RESET}"


# -- Classification (isinstance against the kind classes) ---------------------


def _is_literal(node: Nu) -> bool:
    return isinstance(node, LiteralQuery)


def _is_ref(node: Nu) -> bool:
    return isinstance(node, Ref)


def _is_query(node: Nu) -> bool:
    return isinstance(node, Query)


def _is_command(node: Nu) -> bool:
    return isinstance(node, Command)


def _is_action(node: Nu) -> bool:
    return isinstance(node, Action)


def _is_flow(node: Nu) -> bool:
    return isinstance(node, Flow)


def _is_span(node: Nu) -> bool:
    return isinstance(node, Span)


def _category_color(node: Nu) -> str:
    if _is_span(node):
        return MAGENTA
    if _is_flow(node):
        return BLUE
    if _is_ref(node):
        return YELLOW
    if _is_command(node):
        return RED
    if _is_action(node):
        return BRIGHT_RED
    if _is_literal(node):
        # Trivial leaf literal vs computed (children present).
        return CYAN if not node._children else DIM_CYAN
    if _is_query(node):
        return GREEN
    return ""


# -- Labels -------------------------------------------------------------------


def _ref_label(node: Ref) -> str:
    cls = type(node).__name__

    # A structured (Shape) Ref carries its owning Shape, not a payload - surface
    # it as ``ItemRef[Order]`` so the tree shows which Shape a slot belongs to.
    owner = getattr(node, "_owner_shape", None)
    if owner is None:
        owner = getattr(node, "_root_shape", None)
    if owner is not None:
        return f"{cls}[{getattr(owner, '__name__', owner)}]"

    payload = getattr(node, "_payload", None) or {}
    if payload:
        hint = ", ".join(f"{k}={v!r}" for k, v in payload.items())
        return f"{cls}({hint})"
    return cls


def _literal_label(node: LiteralQuery) -> str:
    cls = type(node).__name__
    if not node._children:
        return f"{cls}({node._payload.get('value')!r})"
    return cls


def _default_label(node: Nu, *, color: bool = True) -> str:
    if isinstance(node, Ref):
        text = _ref_label(node)
    elif isinstance(node, LiteralQuery):
        text = _literal_label(node)
    else:
        text = type(node).__name__

    # A non-Literal Query is a value producer (yields a computed value, no
    # WRITE); mark it with a dot. Not a purity claim - it may READ a Ref.
    is_value_producer = _is_query(node) and not _is_literal(node)

    if not color:
        return f"● {text}" if is_value_producer else text

    cat_color = _category_color(node)
    colored = f"{cat_color}{BOLD}{text}{RESET}" if cat_color else f"{BOLD}{text}{RESET}"
    if is_value_producer:
        colored = f"{VALUE_DOT} {colored}"
    return colored


# -- Tree connectors ----------------------------------------------------------

CONNECTOR_BRANCH = "├──"
CONNECTOR_LAST = "└──"
CONNECTOR_PIPE = "│  "
CONNECTOR_SPACE = "   "


def _dim(text: str, *, color: bool = True) -> str:
    return f"{DIM}{text}{RESET}" if color else text


def _render(
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
            elif connector == CONNECTOR_LAST:
                child_prefix = prefix + CONNECTOR_SPACE
            else:
                child_prefix = prefix + _dim(CONNECTOR_PIPE, color=color)
            child_connector = CONNECTOR_LAST if is_last else CONNECTOR_BRANCH
            _walk(cast("Nu", child), child_prefix, child_connector)

    _walk(root, "", "", is_root=True)
    return "\n".join(lines)


# -- Public entry -------------------------------------------------------------


def render_nu(
    nu: Nu,
    *,
    as_: TLiteral["ansi", "plain"] = "ansi",
    label: Callable[[Nu], str] | None = None,
) -> str:
    """Render a Nu tree as a printable string.

    Args:
        nu: Root node of the tree.
        as_: Output format. ``"ansi"`` (default) emits ANSI color codes for a
            terminal, ``"plain"`` emits plain text for logs or files.
        label: Optional label callable to override the default per-node label.

    Returns:
        A multi-line string, one node per line.
    """
    return _render(nu, label=label, color=as_ == "ansi")
