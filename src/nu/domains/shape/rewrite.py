"""Shape-domain rewrite passes: ref annotation and substrate optimizer helpers.

Domain-specific (Layer 3): these know about shape interactions
(``LoadQuery``) and shape Refs (``_StructuredRef``). They build on the
generic, domain-free toolkit in ``nu.tree``. Other fabrics ship their
own equivalents the same way.

Two sources merged here:

- ``annotate_ref_loads`` — pre-compilation pass that wraps bare shape Refs
  with ``LoadQuery`` so substrate optimizers have something to match on.

- ``extract_static_address``, ``walk_ref_chain``,
  ``reconstruct_with_flat_ref`` — shared building blocks for substrate
  inline-ref deformations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.tree import map_nodes


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.kinds import Ref


__all__ = [
    "annotate_ref_loads",
    "extract_static_address",
    "reconstruct_with_flat_ref",
    "walk_ref_chain",
]


# ---------------------------------------------------------------------------
# annotate_ref_loads
# ---------------------------------------------------------------------------


def annotate_ref_loads(root: Nu) -> Nu:
    """Wrap bare shape Refs with ``LoadQuery`` for optimizer matching.

    Walks the tree bottom-up. For each non-leaf node, wraps any child
    that is a shape Ref (and not already a ``LoadQuery``) with
    ``LoadQuery``.  The Item/Collection split is gone; a single
    ``LoadQuery`` covers all structured Refs.

    This is idempotent — already-wrapped refs are not double-wrapped.

    Requires ``nu.domains.shape.refs._StructuredRef`` and
    ``nu.domains.shape.interactions.LoadQuery`` at call time.
    """
    from .interactions import LoadQuery
    from .refs import _StructuredRef as ShapeRef

    def _process(node: Nu) -> Nu:
        if not node.children:
            return node

        if isinstance(node, LoadQuery):
            return node

        target_ref = getattr(node, "ref", None)
        new_children: list[Nu] = []
        changed = False

        for child in node.children:
            if child is target_ref:
                new_children.append(child)
                continue

            if isinstance(child, ShapeRef) and not isinstance(child, LoadQuery):
                new_children.append(LoadQuery(child))
                changed = True
            else:
                new_children.append(child)

        if changed:
            return node.with_children(*new_children)
        return node

    return map_nodes(root, _process, order="bottom_up")


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
    Nu node is always ``ref.children[0]``.
    """
    from nu.core import LiteralQuery

    addr = ref.children[0]  # address Nu node set by _StructuredRef.__init__
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
            address_terms.append(current.children[0])
        current = current.parent_ref  # type: ignore[attr-defined]

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
