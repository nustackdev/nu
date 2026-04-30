"""inline_refs — PV substrate ref inlining deformation.

Walks the term tree bottom-up. For each op node that holds a PV
substrate Ref (ViewRef/PrimitiveRef), walks the Ref's parent chain at
deformation time, collects static/dynamic address segments and type markers,
and creates a FlatRef with a pre-resolved path tuple.
"""

from __future__ import annotations

from nu.shapes.refs.base import Ref
from nu.shapes.tree.deform import reconstruct_with_flat_ref, walk_ref_chain
from nu.tree import map_nodes
from nu_virtuals.refs.base import PrimitiveRef, ViewRef
from nu_virtuals.refs.flat import FlatRef


__all__ = [
    "inline_refs",
]


def inline_refs[N](tree: N) -> N:
    """Replace PV Ref parent-chains with flat FlatRefs.

    Args:
        tree: Nu tree root.

    Returns:
        New tree with PV Ref chains replaced by FlatRefs.
    """
    return map_nodes(tree, _try_inline_ref, order="bottom_up")


def _try_inline_ref(node: object) -> object:
    """If node holds a PV Ref, replace it with FlatRef."""
    ref = getattr(node, "ref", None)
    if ref is None or not isinstance(ref, Ref):
        return node

    # Only handle PV substrate refs
    if not isinstance(ref, (ViewRef, PrimitiveRef)):
        return node

    is_primitive = isinstance(ref, PrimitiveRef)

    # Walk parent chain at deformation time
    addresses, address_terms = walk_ref_chain(ref)

    # Collect type markers from each ref in chain
    type_markers: list[type | None] = []
    current: Ref | None = ref
    while current is not None:
        marker = getattr(current, "_type_marker", None)
        type_markers.append(marker)
        current = current.parent
    type_markers.reverse()

    # Build dynamic segments list
    dynamic: list[tuple[int, object]] = []
    for i, term in enumerate(address_terms):
        if term is not None:
            dynamic.append((i, term))

    root_shape = ref.get_root_shape()

    # PV path: ((addr, type_marker), ...)
    static_path = tuple(zip(addresses, type_markers, strict=True))
    dyn = tuple(dynamic) if dynamic else None

    inline = FlatRef(
        static_path=static_path,
        root_shape=root_shape,
        is_primitive=is_primitive,
        dynamic_segments=dyn,
    )

    return reconstruct_with_flat_ref(node, inline)
