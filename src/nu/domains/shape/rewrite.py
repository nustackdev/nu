"""Shape-domain rewrite helpers: substrate inline-ref building blocks.

Domain-specific (Layer 3): these know about shape Refs (``StructuredRef``) and
build on the generic, domain-free toolkit in ``nu.tree``. Other fabrics ship
their own equivalents the same way.

``extract_static_address``, ``walk_ref_chain``, ``reconstruct_with_flat_ref``
are shared building blocks for substrate inline-ref deformations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.kinds import Ref


__all__ = [
    "extract_static_address",
    "reconstruct_with_flat_ref",
    "walk_ref_chain",
]


# ---------------------------------------------------------------------------
# Substrate optimizer helpers (shared by substrate inline_refs implementations)
# ---------------------------------------------------------------------------


def extract_static_address(ref: Ref) -> object | None:
    """Try to extract a static (literal) address from a Ref.

    Returns the literal value if the address is a ``LiteralQuery`` leaf,
    or ``None`` if the address is dynamic (any other Nu node).

    All addresses are wrapped by ``Nu.__init__`` as ``LiteralQuery``
    nodes (for plain Python literals) or left as the provided Nu node (for
    dynamic addresses).  There is no ``_raw_address`` attribute; the address
    Nu node is ``ref.children[1]`` (``children[0]`` is the structural parent).
    """
    from nu.core import LiteralQuery

    addr = ref.children[1]  # address Nu node set by StructuredRef.__init__
    if isinstance(addr, LiteralQuery):
        return addr.payload["value"]

    return None  # truly dynamic


def walk_ref_chain(ref: Ref) -> tuple[list[object | None], list[Nu | None]]:
    """Walk the parent chain of a Ref at deformation time.

    Returns ``(addresses, address_terms)`` in root-to-leaf order.
    Each slot in ``addresses`` is the static address or ``None`` (dynamic).
    Each slot in ``address_terms`` is the address Nu for dynamic slots, or
    ``None``.

    This is pure shape Ref logic — no substrate knowledge.
    """
    addresses: list[object | None] = []
    address_terms: list[Nu | None] = []
    current: Ref | None = ref
    while current is not None:
        static_addr = extract_static_address(current)
        if static_addr is not None:
            addresses.append(static_addr)
            address_terms.append(None)
        else:
            addresses.append(None)
            address_terms.append(current.children[1])
        current = current._parent  # type: ignore[attr-defined]

    # Collected leaf-to-root; reverse to root-to-leaf.
    addresses.reverse()
    address_terms.reverse()
    return addresses, address_terms


def reconstruct_with_flat_ref(node: Nu, flat_ref: Nu) -> Nu:
    """Rebuild an op node with ``flat_ref`` replacing the original Ref child.

    Finds the original Ref via ``node.ref``, then rebuilds ``node`` via
    ``with_children``, the immutable-copy API, swapping only that
    child.  Other children (e.g. ``value_expr`` terms) are preserved.
    """
    old_ref = node.ref  # type: ignore[attr-defined]
    new_children = tuple(flat_ref if child is old_ref else child for child in node.children)
    return node.with_children(*new_children)
