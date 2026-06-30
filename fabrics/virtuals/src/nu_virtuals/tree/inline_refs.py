"""inline_refs — virtuals substrate ref inlining deformation.

Walks the term tree bottom-up. For each op node that holds a virtuals substrate
Ref (ViewRef/PrimitiveRef), walks the Ref's parent chain at deformation time,
collects static/dynamic address segments and type markers, and creates a FlatRef
with a pre-resolved path tuple of ``(address, type_marker)`` segments.
"""

from __future__ import annotations

from nu.domains.shape.refs.base import _StructuredRef
from nu.domains.shape.rewrite import reconstruct_with_flat_ref, walk_ref_chain
from nu.tree import map_nodes
from nu_virtuals.refs.base import PrimitiveRef, ViewRef
from nu_virtuals.refs.flat import FlatRef


__all__ = [
    "inline_refs",
]


def inline_refs[N](tree: N) -> N:
    """Replace virtuals Ref parent-chains with flat FlatRefs."""
    return map_nodes(tree, _try_inline_ref, order="bottom_up")


def _try_inline_ref(node: object) -> object:
    """If node holds a virtuals Ref, replace it with a FlatRef."""
    ref = getattr(node, "ref", None)
    if ref is None or not isinstance(ref, _StructuredRef):
        return node
    if not isinstance(ref, (ViewRef, PrimitiveRef)):
        return node

    is_primitive = isinstance(ref, PrimitiveRef)

    addresses, address_terms = walk_ref_chain(ref)

    # Collect type markers from each ref in the chain (root-to-leaf).
    type_markers: list[type | None] = []
    current = ref
    while current is not None:
        type_markers.append(getattr(current, "_type_marker", None))
        current = current.parent_ref  # type: ignore[attr-defined]
    type_markers.reverse()

    dynamic: list[tuple[int, object]] = [
        (i, term) for i, term in enumerate(address_terms) if term is not None
    ]

    static_path = tuple(zip(addresses, type_markers, strict=True))
    inline = FlatRef(
        static_path=static_path,
        root_shape=ref.get_root_shape(),
        is_primitive=is_primitive,
        dynamic_segments=tuple(dynamic) if dynamic else None,
    )
    return reconstruct_with_flat_ref(node, inline)
