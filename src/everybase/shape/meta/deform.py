"""Shared utilities for inline ref deformations.

Substrate-specific inline_refs() live in their owning packages
(everydict.meta, everypv.meta). This module provides the shared
building blocks they both use.

Public API:
    extract_static_address(ref) — get literal address from a Ref, or None
    walk_ref_chain(ref) — walk parent chain, return addresses + address terms
    reconstruct_with_flat_ref(node, flat_ref) — copy node, swap .ref + children
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import Term


if TYPE_CHECKING:
    from everybase.shape.refs.base import Ref


__all__ = [
    "extract_static_address",
    "reconstruct_with_flat_ref",
    "walk_ref_chain",
]


def extract_static_address(ref: Ref) -> object | None:
    """Try to extract a static (literal) address from a Ref.

    Returns the literal value if the address is static, or None if dynamic.
    Handles both _raw_address (set for non-Term addresses) and literal Values
    (where ensure_term wrapped a literal into AnyValue/StrValue/etc.).
    """
    # Fast path: _raw_address was set for non-Term addresses
    raw = ref._raw_address
    if raw is not None:
        return raw

    # Slow path: address is a Value wrapping a literal (e.g. AnyValue("cat_0"))
    # This happens when _create_child_ref calls ensure_term(key) on a literal.
    addr = ref.address  # children[0], a Term
    source = getattr(addr, "source", None)
    if source is not None and not isinstance(source, Term):
        return source  # literal value inside the Value wrapper

    return None  # truly dynamic


def walk_ref_chain(ref: Ref) -> tuple[list[object | None], list[Term | None]]:
    """Walk the parent chain of a Ref at deformation time.

    Returns (addresses, address_terms) in root-to-leaf order.
    Each slot in addresses is the static address or None (dynamic).
    Each slot in address_terms is the address Term for dynamic slots, or None.

    This is pure everyshape.Ref logic — no substrate knowledge.
    """
    addresses: list[object | None] = []
    address_terms: list[Term | None] = []
    current: Ref | None = ref
    while current is not None:
        static_addr = extract_static_address(current)
        if static_addr is not None:
            addresses.append(static_addr)
            address_terms.append(None)
        else:
            addresses.append(None)
            address_terms.append(current.address)
        current = current.parent

    # Collected leaf-to-root, reverse to root-to-leaf
    addresses.reverse()
    address_terms.reverse()
    return addresses, address_terms


def reconstruct_with_flat_ref(node: object, flat_ref: Term) -> object:
    """Rebuild morphism node with FlatRef replacing the original Ref.

    Uses copy + attribute replacement to preserve the node type and state,
    swapping the ref child for the FlatRef.
    """
    import copy

    clone = copy.copy(node)
    old_ref = node.ref  # type: ignore[attr-defined]
    clone.ref = flat_ref  # type: ignore[attr-defined]

    # Rebuild children: replace the old ref child with FlatRef,
    # keep other children (like value_expr terms) intact.
    new_children = []
    for child in node.children:  # type: ignore[attr-defined]
        if child is old_ref:
            new_children.append(flat_ref)
        else:
            new_children.append(child)

    clone._children = tuple(new_children)  # type: ignore[attr-defined]
    return clone
