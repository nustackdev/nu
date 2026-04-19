"""Tree → JSON serialization for the HTML explorer.

Uses duck-typing classification (same approach as display.py POC 3)
to categorize nodes without importing from substrate packages.
"""

from __future__ import annotations

from typing import Any


__all__ = [
    "serialize",
]

# Duck-typed: accepts any Node subclass without importing concrete types.
_Node = Any


# =============================================================================
# NODE CATEGORIZATION (duck-typed, no imports)
# =============================================================================


def _is_span(node: _Node) -> bool:
    return (
        hasattr(node, "enter") and hasattr(node, "exit_success") and hasattr(node, "exit_failure")
    )


def _is_flow(node: _Node) -> bool:
    return hasattr(node, "execute") and not hasattr(node, "is_self_pure") and not _is_span(node)


def _is_ref(node: _Node) -> bool:
    return hasattr(node, "resolve") and hasattr(node, "fetch")


def _is_value(node: _Node) -> bool:
    return hasattr(node, "is_self_pure") and not hasattr(node, "apply") and not _is_ref(node)


def _is_morphism(node: _Node) -> bool:
    return hasattr(node, "apply") or hasattr(node, "_func") or hasattr(node, "_method_name")


def _is_pure(node: _Node) -> bool:
    if hasattr(node, "is_self_pure"):
        return node.is_self_pure
    return True


def _classify(node: _Node) -> str:
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


# =============================================================================
# LABEL FORMATTING
# =============================================================================


def _label(node: _Node) -> str:
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


# =============================================================================
# ATTRIBUTES
# =============================================================================


def _attrs(node: _Node) -> dict[str, Any]:
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


# =============================================================================
# SERIALIZATION
# =============================================================================


_counter = 0


def serialize(root: _Node) -> dict[str, Any]:
    """Recursively serialize a tree node into a JSON-compatible dict."""
    global _counter
    _counter = 0
    return _serialize_node(root)


def _serialize_node(node: _Node) -> dict[str, Any]:
    global _counter
    node_id = _counter
    _counter += 1

    category = _classify(node)
    children = [_serialize_node(child) for child in node.children]

    pure: bool | None = None
    if _is_morphism(node):
        pure = _is_pure(node)

    return {
        "id": node_id,
        "type": type(node).__name__,
        "category": category,
        "label": _label(node),
        "pure": pure,
        "leaf": node._is_leaf,
        "attrs": _attrs(node),
        "children": children,
    }
